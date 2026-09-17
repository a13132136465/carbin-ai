from database.connection import (
    SessionLocal,
)

from database.models import (
    CarbonAudit,
)


def create_audit(
    audit_id: str,
    thread_id: str,
) -> CarbonAudit:

    with SessionLocal() as session:

        audit = CarbonAudit(
            audit_id=audit_id,
            thread_id=thread_id,
            status="IN_PROGRESS",
        )

        session.add(audit)

        session.commit()

        session.refresh(audit)

        return audit


def find_by_audit_id(
    audit_id: str,
) -> CarbonAudit | None:

    with SessionLocal() as session:

        return (
            session.query(CarbonAudit).filter(CarbonAudit.audit_id == audit_id).first()
        )


def find_by_thread_id(
    thread_id: str,
) -> CarbonAudit | None:

    with SessionLocal() as session:

        return (
            session.query(CarbonAudit)
            .filter(CarbonAudit.thread_id == thread_id)
            .first()
        )


def update_audit_from_state(
    thread_id: str,
    result: dict,
    status: str,
):

    with SessionLocal() as session:

        audit = (
            session.query(CarbonAudit)
            .filter(CarbonAudit.thread_id == thread_id)
            .first()
        )

        if audit is None:
            raise ValueError("Audit not found")

        audit.status = status

        audit.project_name = result.get("project_name")

        audit.project_type = result.get("project_type")

        audit.project_region = result.get("project_region")

        audit.annual_generation_mwh = result.get("annual_generation_mwh")

        audit.grid_emission_factor = result.get("grid_emission_factor")

        audit.carbon_estimate = result.get("carbon_estimate")

        audit.audit_report = result.get("audit_report")

        session.commit()
