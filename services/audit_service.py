import uuid

from agent.carbon_graph import (
    graph,
    create_initial_state,
)

from database.audit_repository import (
    create_audit as create_audit_record,
    find_by_audit_id,
    find_by_thread_id,
    update_audit_from_state,
    update_status,
)
from langgraph.types import Command
from domain.audit_status import AuditStatus


def resolve_status(
    result: dict,
) -> AuditStatus:

    if result.get("__interrupt__"):
        return AuditStatus.NEEDS_INPUT

    return AuditStatus.COMPLETED


def start_audit(
    message: str,
) -> dict:

    thread_id = str(uuid.uuid4())

    audit_id = "AUD-" + uuid.uuid4().hex[:12].upper()

    create_audit_record(
        audit_id=audit_id,
        thread_id=thread_id,
    )

    config = {"configurable": {"thread_id": thread_id}}

    initial_state = create_initial_state(message)

    result = graph.invoke(
        initial_state,
        config=config,
    )

    status = resolve_status(result)

    update_audit_from_state(
        thread_id=thread_id,
        result=result,
        status=status,
    )

    return {
        "audit_id": audit_id,
        "thread_id": thread_id,
        "status": status,
        "result": result,
    }


def resume_audit(
    thread_id: str,
    message: str,
) -> dict:

    audit = find_by_thread_id(thread_id)

    if audit is None:
        raise ValueError("Audit not found")

    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        Command(resume=message),
        config=config,
    )

    status = resolve_status(result)

    update_audit_from_state(
        thread_id=thread_id,
        result=result,
        status=status,
    )

    return {
        "audit_id": audit.audit_id,
        "thread_id": thread_id,
        "status": status,
        "result": result,
    }


def get_audit(
    audit_id: str,
):

    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError("Audit not found")

    return audit


def approve_audit(
    audit_id: str,
):

    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError("Audit not found")

    if audit.status != AuditStatus.COMPLETED.value:
        raise ValueError("Only completed audits " "can be approved")

    update_status(
        audit_id,
        AuditStatus.APPROVED.value,
    )

    return find_by_audit_id(audit_id)


def reject_audit(
    audit_id: str,
):

    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError("Audit not found")

    if audit.status != AuditStatus.COMPLETED.value:
        raise ValueError("Only completed audits " "can be rejected")

    update_status(
        audit_id,
        AuditStatus.REJECTED.value,
    )

    return find_by_audit_id(audit_id)
