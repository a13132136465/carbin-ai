import uuid

from fastapi import FastAPI, HTTPException

from api.schemas import (
    AuditRequest,
    AuditResponse,
)

from agent.carbon_graph import (
    graph,
    create_initial_state,
)

from langgraph.types import Command

from api.schemas import (
    AuditRequest,
    AuditResumeRequest,
    AuditResponse,
)
from database.audit_repository import create_audit, update_audit_from_state

app = FastAPI(
    title="CarbonAI API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/api/audits",
    response_model=AuditResponse,
)
def create_audit(
    request: AuditRequest,
):

    thread_id = str(uuid.uuid4())
    audit_id = "AUD-" + uuid.uuid4().hex[:12].upper()
    create_audit(
        audit_id=audit_id,
        thread_id=thread_id,
    )

    config = {"configurable": {"thread_id": thread_id}}

    initial_state = create_initial_state(request.message)

    result = graph.invoke(
        initial_state,
        config=config,
    )
    return build_audit_response(
        result,
        thread_id,
    )


def build_audit_response(
    result: dict,
    thread_id: str,
) -> AuditResponse:

    interrupts = result.get("__interrupt__")
    status = "NEEDS_INPUT" if interrupts else "COMPLETED"
    update_audit_from_state(
        thread_id=thread_id,
        result=result,
        status=status,
    )
    if interrupts:
        interrupt_data = interrupts[0].value

        return AuditResponse(
            status="NEEDS_INPUT",
            thread_id=thread_id,
            audit_id=result.get("audit_id"),
            question=(interrupt_data.get("question")),
            project_name=result.get("project_name"),
            project_type=result.get("project_type"),
            project_region=result.get("project_region"),
            annual_generation_mwh=(result.get("annual_generation_mwh")),
            grid_emission_factor=(result.get("grid_emission_factor")),
            carbon_estimate=result.get("carbon_estimate"),
            audit_report=result.get("audit_report"),
            missing_fields=(
                interrupt_data.get(
                    "missing_fields",
                    [],
                )
            ),
        )

    return AuditResponse(
        status="COMPLETED",
        thread_id=thread_id,
        question=None,
        project_name=result.get("project_name"),
        project_type=result.get("project_type"),
        project_region=result.get("project_region"),
        annual_generation_mwh=result.get("annual_generation_mwh"),
        grid_emission_factor=result.get("grid_emission_factor"),
        carbon_estimate=result.get("carbon_estimate"),
        audit_report=result.get("audit_report"),
        missing_fields=[],
    )


@app.post(
    "/api/audits/{thread_id}/resume",
    response_model=AuditResponse,
)
def resume_audit(
    thread_id: str,
    request: AuditResumeRequest,
):

    config = {"configurable": {"thread_id": thread_id}}
    try:

        result = graph.invoke(
            Command(resume=request.message),
            config=config,
        )
        status = "NEEDS_INPUT" if result.get("__interrupt__") else "COMPLETED"

        update_audit_from_state(
            thread_id=thread_id,
            result=result,
            status=status,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error resuming audit: {str(e)}",
        )

    return build_audit_response(
        result,
        thread_id,
    )
