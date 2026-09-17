from dotenv import load_dotenv

from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from langgraph.graph import (
    StateGraph,
    START,
    END,
)
from langgraph.types import (
    interrupt,
    Command,
)

from knowledge.retriever import search_best, normalize_region

from functools import lru_cache

from config.settings import settings
from agent.constants import (
    HUMAN_REQUIRED_FIELDS,
)
from persistence.checkpointer import (
    get_checkpointer,
)


# ============================================================
# 1. Environment
# ============================================================

load_dotenv()


# ============================================================
# 2. LLM
# ============================================================


@lru_cache(maxsize=1)
def get_llm():

    print(
        "[LLM] Creating DeepSeek client:",
        settings.DEEPSEEK_MODEL,
    )

    return ChatDeepSeek(model=settings.DEEPSEEK_MODEL)


model = get_llm()


# ============================================================
# 3. Structured Output Models
# ============================================================


from agent.schemas import (
    ProjectInput,
    EmissionFactorResult,
)

structured_project_model = model.with_structured_output(ProjectInput)

structured_emission_model = model.with_structured_output(EmissionFactorResult)


# ============================================================
# 4. LangGraph State
# ============================================================

from agent.state import CarbonAuditState

# ============================================================
# 5. Parse Project
# ============================================================


def parse_project(
    state: CarbonAuditState,
):
    print("\n[parse_project]")

    messages = [SystemMessage(content="""
            Extract carbon project information
            from the full conversation.

            Use conversation history to understand
            what the user's latest answer refers to.

            Only extract information explicitly
            provided by the user.

            Do not guess or invent missing values.

            Do not infer measurement units that
            the user did not explicitly provide.

            If older messages contain project
            information, preserve that information
            when interpreting the latest message.
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
# 6. Validate Project
# ============================================================


def validate_project(
    state: CarbonAuditState,
):
    print("\n[validate_project]")

    missing_fields = []

    if not state["project_name"]:
        missing_fields.append("project_name")

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

        print(
            "Missing fields:",
            missing_fields,
        )

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
            "validation_result": ("Grid emission factor must be " "greater than 0"),
            "missing_fields": [],
        }

    return {
        "validation_status": "VALID",
        "validation_result": ("Project data is valid"),
        "missing_fields": [],
    }


# ============================================================
# 7. Route After Validation
# ============================================================


from agent.constants import (
    HUMAN_REQUIRED_FIELDS,
    RAG_RESOLVABLE_FIELDS,
)


def route_after_validation(
    state: CarbonAuditState,
):

    status = state["validation_status"]

    if status == "VALID":
        return "normalize"

    if status == "INVALID":
        return "reject"

    missing_fields = set(state["missing_fields"])

    human_missing = missing_fields & HUMAN_REQUIRED_FIELDS

    rag_missing = missing_fields & RAG_RESOLVABLE_FIELDS

    print(
        "Human missing:",
        human_missing,
    )

    print(
        "RAG missing:",
        rag_missing,
    )

    # 用户自己的业务数据缺失，
    # 优先询问用户
    if human_missing:
        return "human"

    # 只有知识型数据缺失，
    # 尝试 RAG
    if rag_missing:
        return "retrieve"

    return "reject"


# ============================================================
# 8. Retrieve Emission Factor
# ============================================================


def retrieve_emission_factor(
    state: CarbonAuditState,
):
    print("\n[retrieve_emission_factor]")

    region = state["project_region"]

    normalized_region = normalize_region(region)

    query = "What is the grid emission factor " f"for {normalized_region}?"

    print("Original region:", region)
    print("Normalized region:", normalized_region)
    print("Retrieval query:", query)

    result = search_best(query)

    print("search_best result:", result)

    if not result.found:
        print("RAG NOT FOUND")

        return {
            "retrieval_status": "NOT_FOUND",
            "retrieval_score": result.score,
            "retrieved_context": "",
            "retrieval_sources": [],
        }

    print("RAG FOUND")

    return {
        "retrieval_status": "FOUND",
        "retrieval_score": result.score,
        "retrieved_context": result.content,
        "retrieval_sources": ([result.source] if result.source else []),
    }


# ============================================================
# 9. Route Retrieval
# ============================================================


def route_retrieval(
    state: CarbonAuditState,
):

    if state["retrieval_status"] == "FOUND":
        return "extract"

    return "human"


# ============================================================
# 10. Structured RAG Extraction
# ============================================================


def extract_emission_factor(
    state: CarbonAuditState,
):
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
            exist in the provided context.

            If the requested region or its
            emission factor cannot be found,
            set:

            found = false
            value = null
            unit = null
            """),
        HumanMessage(content=f"""
            Requested region:

            {region}

            Context:

            {context}
            """),
    ]

    result = structured_emission_model.invoke(messages)

    print(
        "Structured RAG result:",
        result,
    )

    if not result.found or result.value is None or result.unit is None:
        return {"retrieval_status": ("NOT_FOUND")}

    return {
        "grid_emission_factor_value": (result.value),
        "grid_emission_factor_unit": (result.unit),
        "retrieval_status": ("EXTRACTED"),
    }


# ============================================================
# 11. Route Extraction
# ============================================================


def route_extraction(
    state: CarbonAuditState,
):

    if state["retrieval_status"] == "EXTRACTED":
        # Business State changed.
        # Validate again.
        return "validate"

    return "human"


# ============================================================
# 12. Human In The Loop
# ============================================================

def ask_for_info(
    state: CarbonAuditState,
):
    print("\n[ask_for_info]")
    human_missing_fields = [
        field for field in state["missing_fields"] if field in HUMAN_REQUIRED_FIELDS
    ]

    # 如果没有必须由人填写的数据，
    # 说明这里只应该是 RAG 失败后才会来到这里。
    if not human_missing_fields:
        human_missing_fields = state["missing_fields"]
    fields = ", ".join(human_missing_fields)

    question = "Please provide the missing " "project information: " f"{fields}"

    user_answer = interrupt(
        {
            "question": question,
            "missing_fields": (state["missing_fields"]),
        }
    )

    print("\n[Graph resumed]")

    print(
        "User answer:",
        user_answer,
    )

    return {
        "user_input": (user_answer),
        "messages": [
            AIMessage(content=question),
            HumanMessage(content=user_answer),
        ],
    }


# ============================================================
# 13. Normalize Units
# ============================================================


def normalize_units(
    state: CarbonAuditState,
):
    print("\n[normalize_units]")

    generation_value = state["annual_generation_value"]

    generation_unit = state["annual_generation_unit"]

    factor_value = state["grid_emission_factor_value"]

    factor_unit = state["grid_emission_factor_unit"]

    # Generation → MWh

    if generation_unit == "MWh":

        annual_generation_mwh = generation_value

    elif generation_unit == "kWh":

        annual_generation_mwh = generation_value / 1000

    elif generation_unit == "度":

        annual_generation_mwh = generation_value / 1000

    else:

        raise ValueError("Unsupported generation unit: " f"{generation_unit}")

    # Emission factor normalization

    if factor_unit == "tCO2/MWh":

        grid_emission_factor = factor_value

    else:

        raise ValueError("Unsupported emission factor " f"unit: {factor_unit}")

    return {
        "annual_generation_mwh": (annual_generation_mwh),
        "grid_emission_factor": (grid_emission_factor),
    }


# ============================================================
# 14. Calculate Carbon Reduction
# ============================================================


def calculate_carbon(
    state: CarbonAuditState,
):
    print("\n[calculate_carbon]")

    carbon_estimate = state["annual_generation_mwh"] * state["grid_emission_factor"]

    print(
        "Carbon estimate:",
        carbon_estimate,
        "tCO2/year",
    )

    return {"carbon_estimate": (carbon_estimate)}


# ============================================================
# 15. Generate Report
# ============================================================


def generate_report(
    state: CarbonAuditState,
):
    print("\n[generate_report]")

    sources = state["retrieval_sources"]

    if sources:
        source_text = ", ".join(sources)
    else:
        source_text = "Provided directly by user"

    messages = [
        SystemMessage(content="""
            You are a carbon credit
            project auditor.

            Generate a concise preliminary
            audit report based only on the
            provided project data.

            Do not invent missing facts.

            Clearly state that the result is
            a preliminary software-generated
            assessment and not an official
            carbon-credit verification.
            """),
        HumanMessage(content=f"""
            Project name:
            {state["project_name"]}

            Project type:
            {state["project_type"]}

            Project region:
            {state["project_region"]}

            Annual generation:
            {state["annual_generation_mwh"]} MWh

            Grid emission factor:
            {state["grid_emission_factor"]}
            tCO2/MWh

            Grid emission factor source:
            {source_text}

            Validation result:
            {state["validation_result"]}

            Estimated annual carbon reduction:
            {state["carbon_estimate"]}
            tCO2/year
            """),
    ]

    response = model.invoke(messages)

    return {"audit_report": (response.content)}


# ============================================================
# 16. Reject Project
# ============================================================


def reject_project(
    state: CarbonAuditState,
):
    print("\n[reject_project]")

    return {
        "audit_report": ("Project data is invalid: " f"{state['validation_result']}")
    }


# ============================================================
# 17. Build Graph
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
# 18. Graph Edges
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


builder.add_conditional_edges(
    "retrieve_emission_factor",
    route_retrieval,
    {
        "extract": ("extract_emission_factor"),
        "human": ("ask_for_info"),
    },
)


builder.add_conditional_edges(
    "extract_emission_factor",
    route_extraction,
    {
        "validate": ("validate"),
        "human": ("ask_for_info"),
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
# 19. Compile Graph
# ============================================================


checkpointer = get_checkpointer()


graph = builder.compile(checkpointer=checkpointer)


# ============================================================
# 20. CLI Test
# ============================================================


def create_initial_state(
    user_input: str,
):
    return {
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


if __name__ == "__main__":

    config = {"configurable": {"thread_id": ("carbon-audit-001")}}

    user_input = input("\nYou: ")

    initial_state = create_initial_state(user_input)

    result = graph.invoke(
        initial_state,
        config=config,
    )

    while result.get("__interrupt__"):

        interrupt_data = result["__interrupt__"][0].value

        question = interrupt_data["question"]

        print(f"\nCarbonAI: {question}")

        user_answer = input("\nYou: ")

        result = graph.invoke(
            Command(resume=user_answer),
            config=config,
        )

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

    print("\n========== Conversation ==========")

    for message in result["messages"]:

        print(f"{type(message).__name__}: " f"{message.content}")
