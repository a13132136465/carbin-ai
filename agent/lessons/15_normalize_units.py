from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()
model = ChatDeepSeek(model="deepseek-chat")


class ProjectInput(BaseModel):

    project_name: Optional[str] = Field(
        default=None, description="Name of the carbon project. None if not provided."
    )

    project_type: Optional[str] = Field(
        default=None,
        description="Type of carbon project, such as solar or wind. None if not provided.",
    )

    annual_generation_value: Optional[float] = Field(
        default=None,
        description=(
            "Numeric value of annual electricity generation. "
            "Only extract information explicitly provided by the user."
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
            "Only extract information explicitly provided by the user."
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


class CarbonAuditState(TypedDict):

    user_input: str

    project_name: Optional[str]
    project_type: Optional[str]

    # Raw data extracted by LLM
    annual_generation_value: Optional[float]
    annual_generation_unit: Optional[str]

    grid_emission_factor_value: Optional[float]
    grid_emission_factor_unit: Optional[str]

    annual_generation_mwh: Optional[float]
    grid_emission_factor: Optional[float]

    validation_result: str
    carbon_estimate: float

    audit_report: str
    missing_fields: list[str]
    validation_status: str


structured_model = model.with_structured_output(ProjectInput)


def parse_project(state: CarbonAuditState):
    print("\nParsed project:")

    messages = [
        SystemMessage(content="""
            Extract carbon project information from the user's message.

            Only extract information explicitly provided by the user.

            Do not guess or invent missing values.

            If a value is not provided, return null.
            """),
        HumanMessage(content=state["user_input"]),
    ]

    project = structured_model.invoke(messages)
    print(project)

    updates = {}

    if project.project_name is not None:
        updates["project_name"] = project.project_name

    if project.project_type is not None:
        updates["project_type"] = project.project_type

    if project.annual_generation_value is not None:
        updates["annual_generation_value"] = project.annual_generation_value

    if project.annual_generation_unit is not None:
        updates["annual_generation_unit"] = project.annual_generation_unit

    if project.grid_emission_factor_value is not None:
        updates["grid_emission_factor_value"] = project.grid_emission_factor_value

    if project.grid_emission_factor_unit is not None:
        updates["grid_emission_factor_unit"] = project.grid_emission_factor_unit

    return updates


def validate_project(state: CarbonAuditState):
    print("\n[validate_project]")

    missing_fields = []

    if not state["project_name"]:
        missing_fields.append("project_name")

    if not state["project_type"]:
        missing_fields.append("project_type")

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
            "validation_result": "Required project information is missing",
            "missing_fields": missing_fields,
        }

    if state["annual_generation_value"] <= 0:
        return {
            "validation_status": "INVALID",
            "validation_result": "Annual generation must be greater than 0",
            "missing_fields": [],
        }

    if state["grid_emission_factor_value"] <= 0:
        return {
            "validation_status": "INVALID",
            "validation_result": "Grid emission factor must be greater than 0",
            "missing_fields": [],
        }

    return {
        "validation_status": "VALID",
        "validation_result": "Project data is valid",
        "missing_fields": [],
    }


def normalize_units(state: CarbonAuditState):
    print("\n[normalize_units]")

    generation_value = state["annual_generation_value"]
    generation_unit = state["annual_generation_unit"]

    factor_value = state["grid_emission_factor_value"]
    factor_unit = state["grid_emission_factor_unit"]

    # Normalize annual generation to MWh

    if generation_unit == "MWh":
        annual_generation_mwh = generation_value

    elif generation_unit == "kWh":
        annual_generation_mwh = generation_value / 1000

    elif generation_unit == "度":
        annual_generation_mwh = generation_value / 1000

    else:
        raise ValueError(f"Unsupported generation unit: {generation_unit}")

    # For now we only support tCO2/MWh

    if factor_unit == "tCO2/MWh":
        grid_emission_factor = factor_value

    else:
        raise ValueError(f"Unsupported emission factor unit: {factor_unit}")

    return {
        "annual_generation_mwh": annual_generation_mwh,
        "grid_emission_factor": grid_emission_factor,
    }


def calculate_carbon(state: CarbonAuditState):
    print("\n[calculate_carbon]")

    carbon_estimate = state["annual_generation_mwh"] * state["grid_emission_factor"]

    return {"carbon_estimate": carbon_estimate}


def route_after_validation(state: CarbonAuditState):

    status = state["validation_status"]

    if status == "VALID":
        return "normalize"

    if status == "MISSING":
        return "ask_for_info"

    return "reject"


def ask_for_info(state: CarbonAuditState):
    print("\n[ask_for_info]")

    fields = ", ".join(state["missing_fields"])

    question = "Please provide the missing project information: " f"{fields}"

    user_answer = interrupt(
        {"question": question, "missing_fields": state["missing_fields"]}
    )

    print("\n[Graph resumed]")
    print("User answer:")
    print(user_answer)

    return {"user_input": user_answer}


def generate_report(state: CarbonAuditState):
    print("\n[generate_report]")

    messages = [
        SystemMessage(content="""
            You are a carbon credit project auditor.

            Generate a concise preliminary audit report
            based only on the provided project data.

            Do not invent missing facts.
            """),
        HumanMessage(content=f"""
            Project name:
            {state["project_name"]}

            Project type:
            {state["project_type"]}

            Annual electricity generation:
            {state["annual_generation_mwh"]} MWh

            Grid emission factor:
            {state["grid_emission_factor"]} tCO2/MWh

            Validation result:
            {state["validation_result"]}

            Estimated annual carbon reduction:
            {state["carbon_estimate"]} tCO2/year

            Please provide a short preliminary audit report.
            """),
    ]

    response = model.invoke(messages)

    return {"audit_report": response.content}


def reject_project(state: CarbonAuditState):
    print("\n[reject_project]")

    return {
        "audit_report": (f"Project data is invalid: " f"{state['validation_result']}")
    }


builder = StateGraph(CarbonAuditState)
builder.add_node("parse", parse_project)
builder.add_node("validate", validate_project)

builder.add_node("calculate", calculate_carbon)
builder.add_node("generate_report", generate_report)

builder.add_node("ask_for_info", ask_for_info)
builder.add_node("reject", reject_project)
builder.add_node("normalize", normalize_units)

builder.add_edge(START, "parse")
builder.add_edge("parse", "validate")
builder.add_conditional_edges(
    "validate",
    route_after_validation,
    {"normalize": "normalize", "ask_for_info": "ask_for_info", "reject": "reject"},
)
builder.add_edge("normalize", "calculate")
builder.add_edge("ask_for_info", "parse")

builder.add_edge("reject", END)
builder.add_edge("calculate", "generate_report")
builder.add_edge("generate_report", END)
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "carbon-audit-001"}}
user_input = input("\nYou: ")
initial_state = {
    "user_input": user_input,
    "project_name": None,
    "project_type": None,
    "annual_generation_mwh": None,
    "grid_emission_factor": None,
    "validation_result": "",
    "carbon_estimate": 0,
    "audit_report": "",
    "validation_status": "",
    "missing_fields": [],
    "annual_generation_value": None,
    "annual_generation_unit": None,

    "grid_emission_factor_value": None,
    "grid_emission_factor_unit": None,
}

# 第一次启动 Graph
result = graph.invoke(initial_state, config=config)

print("\nFirst invocation result:")
print(result)

print("\nInterrupt information:")
print(result.get("__interrupt__"))


while result.get("__interrupt__"):

    interrupts = result["__interrupt__"]

    interrupt_data = interrupts[0].value

    question = interrupt_data["question"]

    print(f"\nCarbonAI: {question}")

    user_answer = input("\nYou: ")

    result = graph.invoke(Command(resume=user_answer), config=config)


print("\n========== Final Result ==========")

print(f"Project: " f"{result['project_name']}")

print(f"Project Type: " f"{result['project_type']}")

print(f"Annual Generation: " f"{result['annual_generation_mwh']} MWh")

print(f"Grid Emission Factor: " f"{result['grid_emission_factor']} tCO2/MWh")

print(f"Validation Status: " f"{result['validation_status']}")

print(f"Validation: " f"{result['validation_result']}")

print(f"Carbon Estimate: " f"{result['carbon_estimate']} tCO2/year")

print("\nAudit Report:")
print(result["audit_report"])
