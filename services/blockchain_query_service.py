from blockchain.carbon_credit import (
    get_credit_balance,
    get_credit_batch,
)

from blockchain.contracts import (
    get_carbon_credit_contract,
    get_project_nft_contract,
)

from blockchain.transaction import (
    get_operator_address,
)

from database.audit_repository import (
    find_by_audit_id,
)

from database.blockchain_transaction_repository import (
    find_transaction_by_id,
)

from database.project_repository import (
    find_by_project_id,
)

from database.retirement_repository import (
    find_retirement_by_id,
)


def get_blockchain_transaction(
    transaction_id: int,
) -> dict:

    tx = find_transaction_by_id(transaction_id)

    if tx is None:
        raise ValueError("Blockchain transaction " "not found")

    return {
        "id": tx.id,
        "audit_id": tx.audit_id,
        "tx_type": (tx.tx_type),
        "business_ref_type": (tx.business_ref_type),
        "business_ref_id": (tx.business_ref_id),
        "chain_id": (tx.chain_id),
        "contract_address": (tx.contract_address),
        "tx_hash": (tx.tx_hash),
        "status": (tx.status),
        "block_number": (tx.block_number),
        "error_message": (tx.error_message),
        "created_at": (tx.created_at),
        "confirmed_at": (tx.confirmed_at),
    }


def get_project_on_chain_info(
    project_id: str,
) -> dict:

    project = find_by_project_id(project_id)

    if project is None:
        raise ValueError("Project not found")

    result = {
        "project_id": (project.project_id),
        "project_name": (project.project_name),
        "on_chain_token_id": (project.on_chain_token_id),
        "contract_address": (project.contract_address),
        "mint_tx_hash": (project.mint_tx_hash),
    }

    if project.on_chain_token_id is None:
        return result

    contract = get_project_nft_contract()

    token_id = int(project.on_chain_token_id)

    result["chain_owner"] = contract.functions.ownerOf(token_id).call()

    result["chain_project_id"] = contract.functions.projectIdOf(token_id).call()

    return result


def get_credit_on_chain_info(
    audit_id: str,
) -> dict:

    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError("Audit not found")

    if audit.credit_id is None:

        return {
            "audit_id": (audit.audit_id),
            "credit_id": None,
            "status": (audit.status),
        }

    credit_id = int(audit.credit_id)

    owner = get_operator_address()

    balance = get_credit_balance(
        account=owner,
        credit_id=credit_id,
    )

    batch = get_credit_batch(credit_id)

    return {
        "audit_id": (audit.audit_id),
        "audit_hash": (audit.audit_hash),
        "credit_id": (credit_id),
        "contract_address": (audit.credit_contract_address),
        "mint_tx_hash": (audit.credit_mint_tx_hash),
        "status": (audit.status),
        "owner": (owner),
        "balance": (balance),
        "batch": (batch),
    }


def get_retirement_info(
    retirement_id: str,
) -> dict:

    retirement = find_retirement_by_id(retirement_id)

    if retirement is None:
        raise ValueError("Retirement not found")

    return {
        "retirement_id": (retirement.retirement_id),
        "audit_id": (retirement.audit_id),
        "credit_id": (retirement.credit_id),
        "amount": (retirement.amount),
        "owner_address": (retirement.owner_address),
        "tx_hash": (retirement.tx_hash),
        "status": (retirement.status),
        "created_at": (retirement.created_at),
        "confirmed_at": (retirement.confirmed_at),
    }
