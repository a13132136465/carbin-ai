from typing import TypedDict
from unittest import result
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()
model = ChatDeepSeek(model="deepseek-chat")


class CarbonAuditState(TypedDict):
    project_name: str
    project_type: str

    annual_generation_mwh: float
    grid_emission_factor: float

    validation_result: str
    carbon_estimate: float

    audit_report: str


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


builder = StateGraph(CarbonAuditState)

builder.add_node("validate", validate_project)

builder.add_node("calculate", calculate_carbon)
builder.add_node("generate_report", generate_report)

builder.add_edge(START, "validate")
builder.add_conditional_edges(
    "validate", route_after_validation, {"calculate": "calculate", "end": END}
)
builder.add_edge("calculate", "generate_report")
builder.add_edge("generate_report", END)
graph = builder.compile()

initial_state = {
    "project_name": "Tianjin Solar Farm",
    "project_type": "solar",
    "annual_generation_mwh": -5000,
    "grid_emission_factor": 0.58,
    "validation_result": "",
    "carbon_estimate": 0,
    "audit_report": "",
}

result = graph.invoke(initial_state)

print("\n========== Final Result ==========")

print(f"Project: {result['project_name']}")

print(f"Validation: {result['validation_result']}")

print(f"Carbon estimate: " f"{result['carbon_estimate']} tCO2/year")

print("\nAudit Report:")
print(result["audit_report"])
