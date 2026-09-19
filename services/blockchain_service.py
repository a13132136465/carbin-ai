from domain.audit_status import AuditStatus

from database.audit_repository import (
    find_by_audit_id,
    update_status,
)


def mint_carbon_credit(
    audit_id: str,
):
    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError("Audit not found")

    if audit.status != AuditStatus.APPROVED.value:
        raise ValueError("Only approved audits " "can be minted")

    # 下一步：
    # blockchain transaction

    print(
        "Mint carbon credit:",
        audit.audit_id,
        audit.carbon_estimate,
    )
