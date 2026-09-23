from database.connection import (
    SessionLocal,
)

from database.models import (
    CarbonAudit,
)


def create_audit(
    audit_id: str,
    thread_id: str,
    project_id: str | None = None,
) -> CarbonAudit:

    with SessionLocal() as session:

        audit = CarbonAudit(
            audit_id=audit_id,
            thread_id=thread_id,
            project_id=project_id,
            status="IN_PROGRESS",
        )

        session.add(audit)

        session.commit()

        session.refresh(audit)

        session.expunge(audit)

        return audit


def find_by_audit_id(
    audit_id: str,
) -> CarbonAudit | None:

    with SessionLocal() as session:

        audit = (
            session.query(CarbonAudit).filter(CarbonAudit.audit_id == audit_id).first()
        )

        if audit is not None:
            session.expunge(audit)

        return audit


def find_by_thread_id(
    thread_id: str,
) -> CarbonAudit | None:

    with SessionLocal() as session:

        audit = (
            session.query(CarbonAudit)
            .filter(CarbonAudit.thread_id == thread_id)
            .first()
        )

        if audit is not None:
            session.expunge(audit)

        return audit


def update_audit_project_id(
    thread_id: str,
    project_id: str,
):

    with SessionLocal() as session:

        audit = (
            session.query(CarbonAudit)
            .filter(CarbonAudit.thread_id == thread_id)
            .first()
        )

        if audit is None:
            raise ValueError("Audit not found")

        audit.project_id = project_id

        session.commit()


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


def update_audit_status(
    audit_id: str,
    status: str,
):

    with SessionLocal() as session:

        audit = (
            session.query(CarbonAudit).filter(CarbonAudit.audit_id == audit_id).first()
        )

        if audit is None:
            raise ValueError("Audit not found")

        audit.status = status

        session.commit()


def update_audit_credit_mint(
    audit_id: str,
    audit_hash: str,
    credit_id: int,
    contract_address: str,
    tx_hash: str,
    status: str,
):

    with SessionLocal() as session:

        audit = (
            session.query(CarbonAudit).filter(CarbonAudit.audit_id == audit_id).first()
        )

        if audit is None:
            raise ValueError("Audit not found")

        audit.audit_hash = audit_hash

        audit.credit_id = credit_id

        audit.credit_contract_address = contract_address

        audit.credit_mint_tx_hash = tx_hash

        audit.status = status

        session.commit()
