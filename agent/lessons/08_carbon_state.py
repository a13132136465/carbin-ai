from typing import TypedDict
from unittest import result

from langgraph.graph import StateGraph, START, END


class CarbonAuditState(TypedDict):
    project_name: str
    project_type: str

    annual_generation_mwh: float
    grid_emission_factor: float

    validation_result: str
    carbon_estimate: float


def validate_project(state: CarbonAuditState):
    print("\n[validate_project]")

    if not state["project_name"].strip():
        result = "FAIL: project name is missing"

    elif not state["project_type"].strip():
        result = "FAIL: project type is missing"

    elif state["annual_generation_mwh"] <= 0:
        result = "FAIL: annual generation must be greater than 0"

    elif state["grid_emission_factor"] <= 0:
        result = "FAIL: grid emission factor must be greater than 0"

    else:
        result = "PASS"

    return {"validation_result": result}


def calculate_carbon(state: CarbonAuditState):
    print("\n[calculate_carbon]")

    carbon_estimate = state["annual_generation_mwh"] * state["grid_emission_factor"]

    return {"carbon_estimate": carbon_estimate}


def route_after_validation(state: CarbonAuditState):
    if state["validation_result"] == "PASS":
        return "calculate"

    return "end"


builder = StateGraph(CarbonAuditState)

builder.add_node("validate", validate_project)

builder.add_node("calculate", calculate_carbon)

builder.add_edge(START, "validate")
builder.add_conditional_edges(
    "validate", route_after_validation, {"calculate": "calculate", "end": END}
)
graph = builder.compile()

initial_state = {
    "project_name": "Tianjin Solar Farm",
    "project_type": "solar",
    "annual_generation_mwh": 5000,
    "grid_emission_factor": 0.58,
    "validation_result": "",
    "carbon_estimate": 0,
}

result = graph.invoke(initial_state)

print("\nFinal State:")
print(result)
