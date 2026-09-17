from typing import TypedDict, Optional, Annotated

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. Environment
# ============================================================

load_dotenv()


# ============================================================
# 2. LLM
# ============================================================

model = ChatDeepSeek(model="deepseek-chat")


# ============================================================
# 3. Build demo RAG knowledge base
# ============================================================

loader = TextLoader("docs/carbon-standards/demo_emission_factors.txt")

documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
)

chunks = splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vector_store = FAISS.from_documents(
    chunks,
    embeddings,
)


# Demo threshold only.
# Must be calibrated with a larger evaluation dataset
# before production use.
RETRIEVAL_DISTANCE_THRESHOLD = 0.85


# ============================================================
# 4. Structured Output Models
# ============================================================


class ProjectInput(BaseModel):

    project_name: Optional[str] = Field(
        default=None,
        description=("Name of the carbon project. " "None if not explicitly provided."),
    )

    project_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of carbon project, such as solar or wind. "
            "None if not explicitly provided."
        ),
    )

    project_region: Optional[str] = Field(
        default=None,
        description=(
            "Geographic region of the project, "
            "such as Tianjin, Beijing, Shanghai, Guangdong "
            "or Sichuan. "
            "Only extract the region explicitly provided "
            "by the user."
        ),
    )

    annual_generation_value: Optional[float] = Field(
        default=None,
        description=(
            "Numeric value of annual electricity generation. "
            "Only extract information explicitly provided "
            "by the user."
        ),
    )

    annual_generation_unit: Optional[str] = Field(
        default=None,
        description=(
            "Unit explicitly provided by the user for annual "
            "electricity generation, such as MWh, kWh, or 度. "
            "Do not infer or guess the unit."
        ),
    )

    grid_emission_factor_value: Optional[float] = Field(
        default=None,
        description=(
            "Numeric value of the grid emission factor. "
            "Only extract information explicitly provided "
            "by the user."
        ),
    )

    grid_emission_factor_unit: Optional[str] = Field(
        default=None,
        description=(
            "Unit explicitly provided by the user for the grid "
            "emission factor, such as tCO2/MWh. "
            "Do not infer or guess the unit."
        ),
    )


class EmissionFactorResult(BaseModel):

    found: bool = Field(
        description=(
            "Whether the requested grid emission factor "
            "is explicitly present in the provided context."
        )
    )

    region: Optional[str] = Field(
        default=None,
        description="Region requested by the user.",
    )

    value: Optional[float] = Field(
        default=None,
        description="Grid emission factor numeric value.",
    )

    unit: Optional[str] = Field(
        default=None,
        description="Grid emission factor unit.",
    )


structured_project_model = model.with_structured_output(ProjectInput)

structured_emission_model = model.with_structured_output(EmissionFactorResult)


# ============================================================
# 5. LangGraph State
# ============================================================


class CarbonAuditState(TypedDict):

    # Conversation
    user_input: str
    messages: Annotated[list, add_messages]

    # Project information
    project_name: Optional[str]
    project_type: Optional[str]
    project_region: Optional[str]

    # Raw values extracted from user / RAG
    annual_generation_value: Optional[float]
    annual_generation_unit: Optional[str]

    grid_emission_factor_value: Optional[float]
    grid_emission_factor_unit: Optional[str]

    # Normalized business values
    annual_generation_mwh: Optional[float]
    grid_emission_factor: Optional[float]

    # Validation
    validation_status: str
    validation_result: str
    missing_fields: list[str]

    # RAG
    retrieval_status: str
    retrieval_score: Optional[float]
    retrieved_context: str
    retrieval_sources: list[str]

    # Calculation / report
    carbon_estimate: float
    audit_report: str


# ============================================================
# 6. Parse user conversation
# ============================================================


def parse_project(state: CarbonAuditState):
    print("\n[parse_project]")

    messages = [SystemMessage(content="""
            Extract carbon project information
            from the conversation.

            Use the full conversation history
            to understand what the user's latest
            answer refers to.

            Only extract information explicitly
            provided by the user.

            Do not guess or invent missing values.

            Do not infer measurement units that
            the user did not explicitly provide.

            Preserve previously provided information
            if the latest user message only supplies
            one missing field.
            """)] + state["messages"]

    project = structured_project_model.invoke(messages)

    print(project)

    updates = {}

    if project.project_name is not None:
        updates["project_name"] = project.project_name

    if project.project_type is not None:
        updates["project_type"] = project.project_type

    if project.project_region is not None:
        updates["project_region"] = project.project_region

    if project.annual_generation_value is not None:
        updates["annual_generation_value"] = project.annual_generation_value

    if project.annual_generation_unit is not None:
        updates["annual_generation_unit"] = project.annual_generation_unit

    if project.grid_emission_factor_value is not None:
        updates["grid_emission_factor_value"] = project.grid_emission_factor_value

    if project.grid_emission_factor_unit is not None:
        updates["grid_emission_factor_unit"] = project.grid_emission_factor_unit

    return updates


# ============================================================
# 7. Validate business data
# ============================================================


def validate_project(state: CarbonAuditState):
    print("\n[validate_project]")

    missing_fields = []

    # project_name intentionally NOT required
    # for the current calculation demo.

    if not state["project_type"]:
        missing_fields.append("project_type")

    if not state["project_region"]:
        missing_fields.append("project_region")

    if state["annual_generation_value"] is None:
        missing_fields.append("annual_generation_value")

    if not state["annual_generation_unit"]:
        missing_fields.append("annual_generation_unit")

    if state["grid_emission_factor_value"] is None:
        missing_fields.append("grid_emission_factor_value")

    if not state["grid_emission_factor_unit"]:
        missing_fields.append("grid_emission_factor_unit")

    if missing_fields:
        return {
            "validation_status": "MISSING",
            "validation_result": ("Required project information " "is missing"),
            "missing_fields": missing_fields,
        }

    if state["annual_generation_value"] <= 0:
        return {
            "validation_status": "INVALID",
            "validation_result": ("Annual generation must be " "greater than 0"),
            "missing_fields": [],
        }

    if state["grid_emission_factor_value"] <= 0:
        return {
            "validation_status": "INVALID",
            "validation_result": ("Grid emission factor must " "be greater than 0"),
            "missing_fields": [],
        }

    return {
        "validation_status": "VALID",
        "validation_result": ("Project data is valid"),
        "missing_fields": [],
    }


# ============================================================
# 8. Validation Routing
# ============================================================


def route_after_validation(state: CarbonAuditState):

    status = state["validation_status"]

    if status == "VALID":
        return "normalize"

    if status == "INVALID":
        return "reject"

    missing_fields = set(state["missing_fields"])

    rag_resolvable_fields = {
        "grid_emission_factor_value",
        "grid_emission_factor_unit",
    }

    # Only emission factor data is missing.
    if missing_fields and missing_fields.issubset(rag_resolvable_fields):
        return "retrieve"

    return "human"


# ============================================================
# 9. Retrieve emission factor
# ============================================================


def retrieve_emission_factor(state: CarbonAuditState):
    print("\n[retrieve_emission_factor]")

    region = state["project_region"]

    query = "What is the grid emission factor " f"for {region}?"

    print("Retrieval query:")
    print(query)

    results = vector_store.similarity_search_with_score(
        query,
        k=1,
    )

    if not results:
        return {
            "retrieval_status": "NOT_FOUND",
            "retrieval_score": None,
            "retrieved_context": "",
            "retrieval_sources": [],
        }

    document, score = results[0]

    print("Retrieval score:")
    print(score)

    print("Retrieved document:")
    print(document.page_content)

    return {
        "retrieval_status": "RETRIEVED",
        "retrieval_score": float(score),
        "retrieved_context": (document.page_content),
        "retrieval_sources": [
            document.metadata.get(
                "source",
                "Unknown source",
            )
        ],
    }


# ============================================================
# 10. Retrieval Guard
# ============================================================


def retrieval_guard(state: CarbonAuditState):
    print("\n[retrieval_guard]")

    score = state["retrieval_score"]

    if score is None:
        return {"retrieval_status": "NOT_FOUND"}

    print(
        "Distance:",
        score,
        "| Threshold:",
        RETRIEVAL_DISTANCE_THRESHOLD,
    )

    if score > RETRIEVAL_DISTANCE_THRESHOLD:
        return {"retrieval_status": "NOT_FOUND"}

    return {"retrieval_status": "FOUND"}


def route_retrieval(state: CarbonAuditState):

    if state["retrieval_status"] == "FOUND":
        return "extract"

    return "human"


# ============================================================
# 11. Structured RAG extraction
# ============================================================


def extract_emission_factor(state: CarbonAuditState):
    print("\n[extract_emission_factor]")

    context = state["retrieved_context"]

    region = state["project_region"]

    messages = [
        SystemMessage(content="""
            Extract the grid emission factor
            from the provided context.

            Use only the provided context.

            Do not use outside knowledge.

            Do not guess or invent values.

            The requested region must explicitly
            exist in the context.

            If the requested region or its grid
            emission factor cannot be found,
            set found=false and value/unit to null.
            """),
        HumanMessage(content=f"""
            Context:

            {context}

            Requested region:

            {region}
            """),
    ]

    result = structured_emission_model.invoke(messages)

    print("Structured RAG result:")
    print(result)

    if not result.found or result.value is None or result.unit is None:
        return {"retrieval_status": ("NOT_FOUND")}

    return {
        "grid_emission_factor_value": (result.value),
        "grid_emission_factor_unit": (result.unit),
        "retrieval_status": "EXTRACTED",
    }


def route_extraction(state: CarbonAuditState):

    if state["retrieval_status"] == "EXTRACTED":
        # Revalidate because business state
        # has changed.
        return "validate"

    return "human"


# ============================================================
# 12. Human-in-the-loop
# ============================================================


def ask_for_info(state: CarbonAuditState):
    print("\n[ask_for_info]")

    fields = ", ".join(state["missing_fields"])

    question = "Please provide the missing " "project information: " f"{fields}"

    user_answer = interrupt(
        {
            "question": question,
            "missing_fields": (state["missing_fields"]),
        }
    )

    print("\n[Graph resumed]")

    print("User answer:")
    print(user_answer)

    return {
        "user_input": user_answer,
        "messages": [
            AIMessage(content=question),
            HumanMessage(content=user_answer),
        ],
    }


# ============================================================
# 13. Normalize units
# ============================================================


def normalize_units(state: CarbonAuditState):
    print("\n[normalize_units]")

    generation_value = state["annual_generation_value"]

    generation_unit = state["annual_generation_unit"]

    factor_value = state["grid_emission_factor_value"]

    factor_unit = state["grid_emission_factor_unit"]

    # Normalize generation to MWh

    if generation_unit == "MWh":
        annual_generation_mwh = generation_value

    elif generation_unit == "kWh":
        annual_generation_mwh = generation_value / 1000

    elif generation_unit == "度":
        annual_generation_mwh = generation_value / 1000

    else:
        raise ValueError("Unsupported generation unit: " f"{generation_unit}")

    # Currently only support tCO2/MWh

    if factor_unit == "tCO2/MWh":
        grid_emission_factor = factor_value

    else:
        raise ValueError("Unsupported emission factor unit: " f"{factor_unit}")

    return {
        "annual_generation_mwh": (annual_generation_mwh),
        "grid_emission_factor": (grid_emission_factor),
    }


# ============================================================
# 14. Carbon calculation
# ============================================================


def calculate_carbon(state: CarbonAuditState):
    print("\n[calculate_carbon]")

    carbon_estimate = state["annual_generation_mwh"] * state["grid_emission_factor"]

    print(
        "Estimated carbon reduction:",
        carbon_estimate,
        "tCO2/year",
    )

    return {"carbon_estimate": (carbon_estimate)}


# ============================================================
# 15. Generate audit report
# ============================================================


def generate_report(state: CarbonAuditState):
    print("\n[generate_report]")

    sources = state["retrieval_sources"]

    source_text = ", ".join(sources) if sources else "User provided"

    messages = [
        SystemMessage(content="""
            You are a carbon credit
            project auditor.

            Generate a concise preliminary
            audit report based only on the
            provided project data.

            Do not invent missing facts.

            Clearly state that this is only
            a preliminary software-generated
            assessment.
            """),
        HumanMessage(content=f"""
            Project name:
            {state["project_name"]}

            Project type:
            {state["project_type"]}

            Project region:
            {state["project_region"]}

            Annual electricity generation:
            {state["annual_generation_mwh"]} MWh

            Grid emission factor:
            {state["grid_emission_factor"]} tCO2/MWh

            Emission factor source:
            {source_text}

            Validation result:
            {state["validation_result"]}

            Estimated annual carbon reduction:
            {state["carbon_estimate"]} tCO2/year

            Please provide a short
            preliminary audit report.
            """),
    ]

    response = model.invoke(messages)

    return {"audit_report": (response.content)}


# ============================================================
# 16. Reject invalid project
# ============================================================


def reject_project(state: CarbonAuditState):
    print("\n[reject_project]")

    return {
        "audit_report": ("Project data is invalid: " f"{state['validation_result']}")
    }


# ============================================================
# 17. Build LangGraph
# ============================================================


builder = StateGraph(CarbonAuditState)


builder.add_node(
    "parse",
    parse_project,
)

builder.add_node(
    "validate",
    validate_project,
)

builder.add_node(
    "retrieve_emission_factor",
    retrieve_emission_factor,
)

builder.add_node(
    "retrieval_guard",
    retrieval_guard,
)

builder.add_node(
    "extract_emission_factor",
    extract_emission_factor,
)

builder.add_node(
    "ask_for_info",
    ask_for_info,
)

builder.add_node(
    "normalize",
    normalize_units,
)

builder.add_node(
    "calculate",
    calculate_carbon,
)

builder.add_node(
    "generate_report",
    generate_report,
)

builder.add_node(
    "reject",
    reject_project,
)


# ============================================================
# 18. Graph edges
# ============================================================


builder.add_edge(
    START,
    "parse",
)

builder.add_edge(
    "parse",
    "validate",
)


builder.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "normalize": "normalize",
        "retrieve": ("retrieve_emission_factor"),
        "human": "ask_for_info",
        "reject": "reject",
    },
)


builder.add_edge(
    "retrieve_emission_factor",
    "retrieval_guard",
)


builder.add_conditional_edges(
    "retrieval_guard",
    route_retrieval,
    {
        "extract": ("extract_emission_factor"),
        "human": "ask_for_info",
    },
)


builder.add_conditional_edges(
    "extract_emission_factor",
    route_extraction,
    {
        "validate": "validate",
        "human": "ask_for_info",
    },
)


builder.add_edge(
    "ask_for_info",
    "parse",
)

builder.add_edge(
    "normalize",
    "calculate",
)

builder.add_edge(
    "calculate",
    "generate_report",
)

builder.add_edge(
    "generate_report",
    END,
)

builder.add_edge(
    "reject",
    END,
)


# ============================================================
# 19. Compile graph
# ============================================================


checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)


config = {"configurable": {"thread_id": ("carbon-audit-001")}}


# ============================================================
# 20. Initial state
# ============================================================


user_input = input("\nYou: ")


initial_state = {
    "user_input": user_input,
    "messages": [HumanMessage(content=user_input)],
    "project_name": None,
    "project_type": None,
    "project_region": None,
    "annual_generation_value": None,
    "annual_generation_unit": None,
    "grid_emission_factor_value": None,
    "grid_emission_factor_unit": None,
    "annual_generation_mwh": None,
    "grid_emission_factor": None,
    "validation_status": "",
    "validation_result": "",
    "missing_fields": [],
    "retrieval_status": "",
    "retrieval_score": None,
    "retrieved_context": "",
    "retrieval_sources": [],
    "carbon_estimate": 0,
    "audit_report": "",
}


# ============================================================
# 21. Start graph
# ============================================================


result = graph.invoke(
    initial_state,
    config=config,
)


# ============================================================
# 22. Handle interrupts
# ============================================================


while result.get("__interrupt__"):

    interrupts = result["__interrupt__"]

    interrupt_data = interrupts[0].value

    question = interrupt_data["question"]

    print(f"\nCarbonAI: {question}")

    user_answer = input("\nYou: ")

    result = graph.invoke(
        Command(resume=user_answer),
        config=config,
    )


# ============================================================
# 23. Final output
# ============================================================


print("\n========== Final State ==========")

print(
    "Project name:",
    result["project_name"],
)

print(
    "Project type:",
    result["project_type"],
)

print(
    "Project region:",
    result["project_region"],
)

print(
    "Annual generation:",
    result["annual_generation_mwh"],
    "MWh",
)

print(
    "Grid emission factor:",
    result["grid_emission_factor"],
    "tCO2/MWh",
)

print(
    "Carbon estimate:",
    result["carbon_estimate"],
    "tCO2/year",
)

print(
    "Retrieval status:",
    result["retrieval_status"],
)

print(
    "Retrieval score:",
    result["retrieval_score"],
)

print(
    "Retrieval sources:",
    result["retrieval_sources"],
)


print("\n========== Audit Report ==========")

print(result["audit_report"])


print("\n========== Conversation History ==========")

for message in result["messages"]:

    print(f"{type(message).__name__}: " f"{message.content}")
