from fastapi import (
    FastAPI,
    HTTPException,
)

from api.schemas import (
    AuditRequest,
    AuditResumeRequest,
    AuditResponse,
    AuditDetailResponse,
)

from services.audit_service import (
    start_audit,
    resume_audit as resume_audit_service,
    get_audit as get_audit_service,
    approve_audit as approve_audit_service,
    reject_audit as reject_audit_service,
)

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

    result = start_audit(request.message)

    return build_audit_response(result)


def build_audit_response(
    service_result: dict,
) -> AuditResponse:

    result = service_result["result"]

    interrupts = result.get("__interrupt__")

    question = None
    missing_fields = []

    if interrupts:

        interrupt_data = interrupts[0].value

        question = interrupt_data.get("question")

        missing_fields = interrupt_data.get(
            "missing_fields",
            [],
        )

    return AuditResponse(
        audit_id=service_result["audit_id"],
        thread_id=service_result["thread_id"],
        status=service_result["status"],
        question=question,
        project_name=result.get("project_name"),
        project_type=result.get("project_type"),
        project_region=result.get("project_region"),
        annual_generation_mwh=result.get("annual_generation_mwh"),
        grid_emission_factor=result.get("grid_emission_factor"),
        carbon_estimate=result.get("carbon_estimate"),
        audit_report=result.get("audit_report"),
        missing_fields=(missing_fields),
    )


@app.post(
    "/api/audits/{thread_id}/resume",
    response_model=AuditResponse,
)
def resume_audit(
    thread_id: str,
    request: AuditResumeRequest,
):

    try:

        result = resume_audit_service(
            thread_id=thread_id,
            message=request.message,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=("Error resuming audit: " f"{str(e)}"),
        )

    return build_audit_response(result)


@app.get(
    "/api/audits/{audit_id}",
    response_model=AuditDetailResponse,
)
def get_audit(
    audit_id: str,
):

    try:
        audit = get_audit_service(audit_id)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    return AuditDetailResponse(
        audit_id=audit.audit_id,
        status=audit.status,
        project_name=audit.project_name,
        project_type=audit.project_type,
        project_region=audit.project_region,
        annual_generation_mwh=(audit.annual_generation_mwh),
        grid_emission_factor=(audit.grid_emission_factor),
        carbon_estimate=(audit.carbon_estimate),
        audit_report=audit.audit_report,
    )


@app.post("/api/audits/{audit_id}/approve")
def approve_audit(
    audit_id: str,
):

    try:
        audit = approve_audit_service(audit_id)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return {
        "audit_id": audit.audit_id,
        "status": audit.status,
    }


@app.post("/api/audits/{audit_id}/reject")
def reject_audit(
    audit_id: str,
):

    try:
        audit = reject_audit_service(audit_id)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return {
        "audit_id": audit.audit_id,
        "status": audit.status,
    }
