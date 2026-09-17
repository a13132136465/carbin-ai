from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from typing import TypedDict, Optional
from pydantic import BaseModel, Field


# ============================================================
# 1. Load environment variables
# ============================================================

load_dotenv()


# ============================================================
# 2. Create LLM
# ============================================================

model = ChatDeepSeek(
    model="deepseek-chat"
)


# ============================================================
# 3. Define structured output for project parsing
# ============================================================

class ProjectInput(BaseModel):

    project_name: Optional[str] = Field(
        default=None,
        description="Name of the carbon project. None if not provided."
    )

    project_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of carbon project, such as solar or wind. "
            "None if not provided."
        )
    )

    annual_generation_mwh: Optional[float] = Field(
        default=None,
        description=(
            "Annual renewable electricity generation in MWh. "
            "None if not provided."
        )
    )

    grid_emission_factor: Optional[float] = Field(
        default=None,
        description=(
            "Grid emission factor in tCO2/MWh. "
            "None if not provided."
        )
    )


structured_model = model.with_structured_output(
    ProjectInput
)


# ============================================================
# 4. Define LangGraph State
# ============================================================

class CarbonAuditState(TypedDict):

    # Original user input
    user_input: str

    # Parsed project information
    project_name: Optional[str]
    project_type: Optional[str]
    annual_generation_mwh: Optional[float]
    grid_emission_factor: Optional[float]

    # Workflow results
    validation_result: str
    carbon_estimate: float
    audit_report: str


# ============================================================
# 5. Node: Parse project
# ============================================================

def parse_project(state: CarbonAuditState):
    print("\n[parse_project]")

    messages = [
        SystemMessage(
            content="""
            Extract carbon project information from the user's message.

            Only extract information explicitly provided by the user.

            Do not guess or invent missing values.

            If a value is not provided, return null.
            """
        ),

        HumanMessage(
            content=state["user_input"]
        )
    ]

    project = structured_model.invoke(messages)

    print("\nParsed project:")
    print(project)

    return {
        "project_name": project.project_name,
        "project_type": project.project_type,
        "annual_generation_mwh": project.annual_generation_mwh,
        "grid_emission_factor": project.grid_emission_factor
    }


# ============================================================
# 6. Node: Validate project
# ============================================================

def validate_project(state: CarbonAuditState):
    print("\n[validate_project]")

    if not state["project_name"]:
        result = "FAIL: project name is missing"

    elif not state["project_type"]:
        result = "FAIL: project type is missing"

    elif state["annual_generation_mwh"] is None:
        result = "FAIL: annual generation is missing"

    elif state["grid_emission_factor"] is None:
        result = "FAIL: grid emission factor is missing"

    elif state["annual_generation_mwh"] <= 0:
        result = "FAIL: annual generation must be greater than 0"

    elif state["grid_emission_factor"] <= 0:
        result = "FAIL: grid emission factor must be greater than 0"

    else:
        result = "PASS"

    return {
        "validation_result": result
    }


# ============================================================
# 7. Node: Calculate carbon reduction
# ============================================================

def calculate_carbon(state: CarbonAuditState):
    print("\n[calculate_carbon]")

    carbon_estimate = (
        state["annual_generation_mwh"]
        * state["grid_emission_factor"]
    )

    return {
        "carbon_estimate": carbon_estimate
    }


# ============================================================
# 8. Conditional routing
# ============================================================

def route_after_validation(state: CarbonAuditState):

    if state["validation_result"] == "PASS":
        return "calculate"

    return "end"


# ============================================================
# 9. Node: Generate AI audit report
# ============================================================

def generate_report(state: CarbonAuditState):
    print("\n[generate_report]")

    messages = [
        SystemMessage(
            content="""
            You are a carbon credit project auditor.

            Generate a concise preliminary audit report
            based only on the provided project data.

            Do not invent missing facts.
            """
        ),

        HumanMessage(
            content=f"""
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
            """
        )
    ]

    response = model.invoke(messages)

    return {
        "audit_report": response.content
    }


# ============================================================
# 10. Build LangGraph
# ============================================================

builder = StateGraph(CarbonAuditState)


# Register nodes

builder.add_node(
    "parse",
    parse_project
)

builder.add_node(
    "validate",
    validate_project
)

builder.add_node(
    "calculate",
    calculate_carbon
)

builder.add_node(
    "generate_report",
    generate_report
)


# START -> parse

builder.add_edge(
    START,
    "parse"
)


# parse -> validate

builder.add_edge(
    "parse",
    "validate"
)


# validate -> calculate / END

builder.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "calculate": "calculate",
        "end": END
    }
)


# calculate -> generate_report

builder.add_edge(
    "calculate",
    "generate_report"
)


# generate_report -> END

builder.add_edge(
    "generate_report",
    END
)


# Compile graph

graph = builder.compile()


# ============================================================
# 11. Initial State
# ============================================================

initial_state = {

    "user_input": """
    我在天津有一个叫 Tianjin Solar Farm 的光伏项目。

    这个项目一年大约产生 5000 MWh 的清洁电力。

    电网排放因子按照 0.58 tCO2/MWh 计算。

    帮我进行初步审核。
    """,

    "project_name": None,
    "project_type": None,
    "annual_generation_mwh": None,
    "grid_emission_factor": None,

    "validation_result": "",
    "carbon_estimate": 0,
    "audit_report": ""
}


# ============================================================
# 12. Run Graph
# ============================================================

result = graph.invoke(
    initial_state
)


# ============================================================
# 13. Print Result
# ============================================================

print("\n========== Final Result ==========")

print(
    f"Project: "
    f"{result['project_name']}"
)

print(
    f"Project Type: "
    f"{result['project_type']}"
)

print(
    f"Annual Generation: "
    f"{result['annual_generation_mwh']} MWh"
)

print(
    f"Grid Emission Factor: "
    f"{result['grid_emission_factor']} tCO2/MWh"
)

print(
    f"Validation: "
    f"{result['validation_result']}"
)

print(
    f"Carbon Estimate: "
    f"{result['carbon_estimate']} tCO2/year"
)

print("\nAudit Report:")

print(
    result["audit_report"]
)