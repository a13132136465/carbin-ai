import uuid

from datetime import datetime

from web3.exceptions import (
    TimeExhausted,
)

from blockchain.client import (
    get_web3,
)

from blockchain.contracts import (
    get_carbon_credit_contract,
    get_project_nft_contract,
)

from blockchain.project_nft import (
    build_mint_project_function,
    parse_project_minted_event,
)

from blockchain.carbon_credit import (
    build_mint_credit_function,
    build_retire_credit_function,
    get_credit_balance,
    get_credit_id_by_audit_hash,
    parse_credit_minted_event,
    parse_credit_retired_event,
)

from blockchain.hashing import (
    audit_id_to_hash,
)

from blockchain.transaction import (
    broadcast_contract_transaction,
    get_operator_address,
    get_transaction_receipt,
    wait_for_transaction_receipt,
)

from database.audit_repository import (
    find_by_audit_id,
    update_audit_credit_mint,
    update_audit_status,
)

from database.blockchain_transaction_repository import (
    create_transaction,
    find_transaction_by_id,
    mark_transaction_confirmed,
    mark_transaction_failed,
    update_transaction_hash,
)

from database.project_repository import (
    find_by_project_id,
    update_project_on_chain,
)

from database.retirement_repository import (
    create_retirement,
    find_retirement_by_id,
    mark_retirement_confirmed,
    mark_retirement_failed,
    update_retirement_tx_hash,
)

from domain.audit_status import (
    AuditStatus,
)

from domain.blockchain_status import (
    BlockchainTxStatus,
)

from domain.blockchain_tx_type import (
    BlockchainTxType,
)

# ======================================================
# Common
# ======================================================


def carbon_estimate_to_amount(
    carbon_estimate: float,
) -> int:

    if carbon_estimate is None:
        raise ValueError("Carbon estimate is missing")

    if carbon_estimate <= 0:
        raise ValueError("Carbon estimate must " "be positive")

    if not float(carbon_estimate).is_integer():
        raise ValueError(
            "Current CarbonCredit " "issuance only supports " "integer tCO2 amounts"
        )

    return int(carbon_estimate)


def generate_retirement_id() -> str:

    return "RET-" + uuid.uuid4().hex[:12].upper()


# ======================================================
# CarbonProjectNFT
# ======================================================


def mint_project_for_audit(
    audit_id: str,
    metadata_uri: str,
) -> dict:

    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError(f"Audit not found: {audit_id}")

    if audit.status != AuditStatus.APPROVED.value:
        raise ValueError(
            "Only APPROVED audits can "
            "mint a project NFT. "
            f"Current status: "
            f"{audit.status}"
        )

    if not audit.project_id:
        raise ValueError("Audit is not linked " "to a CarbonProject")

    project = find_by_project_id(audit.project_id)

    if project is None:
        raise ValueError(f"Project not found: " f"{audit.project_id}")

    # Project NFT already exists.
    # Reuse it.
    if project.on_chain_token_id is not None:
        return {
            "status": (BlockchainTxStatus.CONFIRMED.value),
            "already_minted": True,
            "audit_id": (audit.audit_id),
            "project_id": (project.project_id),
            "token_id": (project.on_chain_token_id),
            "contract_address": (project.contract_address),
            "tx_hash": (project.mint_tx_hash),
        }

    web3 = get_web3()

    contract = get_project_nft_contract()

    recipient = get_operator_address()

    tx_record = create_transaction(
        audit_id=(audit.audit_id),
        tx_type=(BlockchainTxType.MINT_PROJECT_NFT.value),
        business_ref_type=("PROJECT"),
        business_ref_id=(project.project_id),
        chain_id=(web3.eth.chain_id),
        contract_address=(contract.address),
    )

    function = build_mint_project_function(
        recipient=recipient,
        project_id=(project.project_id),
        metadata_uri=(metadata_uri),
    )

    try:

        tx_hash = broadcast_contract_transaction(function)

    except Exception as e:

        mark_transaction_failed(
            transaction_id=(tx_record.id),
            error_message=str(e),
        )

        raise

    update_transaction_hash(
        transaction_id=(tx_record.id),
        tx_hash=(tx_hash),
    )

    try:

        receipt = wait_for_transaction_receipt(tx_hash)

    except TimeExhausted:

        return {
            "status": (BlockchainTxStatus.PENDING.value),
            "transaction_id": (tx_record.id),
            "audit_id": (audit.audit_id),
            "project_id": (project.project_id),
            "tx_hash": (tx_hash),
        }

    if receipt.status != 1:

        mark_transaction_failed(
            transaction_id=(tx_record.id),
            error_message=("Transaction reverted"),
        )

        raise RuntimeError("Project NFT mint " "transaction reverted. " f"tx={tx_hash}")

    return _confirm_project_nft_mint(
        tx_record=tx_record,
        receipt=receipt,
        project=project,
        recipient=recipient,
    )


def _confirm_project_nft_mint(
    tx_record,
    receipt,
    project,
    recipient: str | None = None,
) -> dict:

    event = parse_project_minted_event(receipt)

    if event["project_id"] != project.project_id:
        raise RuntimeError("ProjectMinted event " "projectId mismatch")

    if recipient is not None and event["owner"].lower() != recipient.lower():
        raise RuntimeError("ProjectMinted event " "owner mismatch")

    update_project_on_chain(
        project_id=(project.project_id),
        token_id=int(event["token_id"]),
        contract_address=(tx_record.contract_address),
        tx_hash=(tx_record.tx_hash),
    )

    mark_transaction_confirmed(
        transaction_id=(tx_record.id),
        block_number=(receipt.blockNumber),
    )

    project_hash = event["project_hash"]

    if hasattr(
        project_hash,
        "hex",
    ):
        project_hash = project_hash.hex()

    return {
        "status": (BlockchainTxStatus.CONFIRMED.value),
        "transaction_id": (tx_record.id),
        "project_id": (project.project_id),
        "token_id": int(event["token_id"]),
        "project_hash": (project_hash),
        "owner": (event["owner"]),
        "contract_address": (tx_record.contract_address),
        "tx_hash": (tx_record.tx_hash),
        "block_number": (receipt.blockNumber),
    }


# ======================================================
# CarbonCredit Mint
# ======================================================


def mint_credit_for_audit(
    audit_id: str,
    vintage: int | None = None,
) -> dict:

    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError(f"Audit not found: {audit_id}")

    if audit.status != AuditStatus.APPROVED.value:
        raise ValueError(
            "Only APPROVED audits can "
            "mint CarbonCredit. "
            f"Current status: "
            f"{audit.status}"
        )

    if not audit.project_id:
        raise ValueError("Audit has no project_id")

    project = find_by_project_id(audit.project_id)

    if project is None:
        raise ValueError("Project not found")

    if project.on_chain_token_id is None:
        raise ValueError("Project NFT has not " "been minted yet")

    audit_hash = audit_id_to_hash(audit.audit_id)

    audit_hash_hex = "0x" + audit_hash.hex()

    existing_credit_id = get_credit_id_by_audit_hash(audit_hash)

    if existing_credit_id != 0:
        raise ValueError(
            "CarbonCredit already "
            "issued for this audit. "
            f"creditId="
            f"{existing_credit_id}"
        )

    amount = carbon_estimate_to_amount(audit.carbon_estimate)

    if vintage is None:
        vintage = datetime.utcnow().year

    if vintage <= 0:
        raise ValueError("Invalid vintage")

    web3 = get_web3()

    contract = get_carbon_credit_contract()

    recipient = get_operator_address()

    tx_record = create_transaction(
        audit_id=(audit.audit_id),
        tx_type=(BlockchainTxType.MINT_CREDIT.value),
        business_ref_type=("AUDIT"),
        business_ref_id=(audit.audit_id),
        chain_id=(web3.eth.chain_id),
        contract_address=(contract.address),
    )

    update_audit_status(
        audit_id=(audit.audit_id),
        status=(AuditStatus.MINTING.value),
    )

    function = build_mint_credit_function(
        recipient=(recipient),
        project_token_id=int(project.on_chain_token_id),
        audit_hash=(audit_hash),
        vintage=(vintage),
        amount=(amount),
    )

    try:

        tx_hash = broadcast_contract_transaction(function)

    except Exception as e:

        mark_transaction_failed(
            transaction_id=(tx_record.id),
            error_message=str(e),
        )

        update_audit_status(
            audit_id=(audit.audit_id),
            status=(AuditStatus.APPROVED.value),
        )

        raise

    update_transaction_hash(
        transaction_id=(tx_record.id),
        tx_hash=(tx_hash),
    )

    try:

        receipt = wait_for_transaction_receipt(tx_hash)

    except TimeExhausted:

        return {
            "status": (BlockchainTxStatus.PENDING.value),
            "audit_status": (AuditStatus.MINTING.value),
            "transaction_id": (tx_record.id),
            "audit_id": (audit.audit_id),
            "audit_hash": (audit_hash_hex),
            "tx_hash": (tx_hash),
        }

    if receipt.status != 1:

        mark_transaction_failed(
            transaction_id=(tx_record.id),
            error_message=("Transaction reverted"),
        )

        update_audit_status(
            audit_id=(audit.audit_id),
            status=(AuditStatus.APPROVED.value),
        )

        raise RuntimeError("CarbonCredit mint " "transaction reverted")

    return _confirm_credit_mint(
        tx_record=tx_record,
        receipt=receipt,
        audit=audit,
        project=project,
        recipient=recipient,
    )


def _confirm_credit_mint(
    tx_record,
    receipt,
    audit,
    project,
    recipient: str | None = None,
) -> dict:

    event = parse_credit_minted_event(receipt)

    expected_audit_hash = audit_id_to_hash(audit.audit_id)

    if bytes(event["audit_hash"]) != bytes(expected_audit_hash):
        raise RuntimeError("CreditMinted " "auditHash mismatch")

    if int(event["project_token_id"]) != int(project.on_chain_token_id):
        raise RuntimeError("CreditMinted " "projectTokenId mismatch")

    if recipient is not None and event["recipient"].lower() != recipient.lower():
        raise RuntimeError("CreditMinted " "recipient mismatch")

    credit_id = int(event["credit_id"])

    audit_hash_hex = "0x" + expected_audit_hash.hex()

    update_audit_credit_mint(
        audit_id=(audit.audit_id),
        audit_hash=(audit_hash_hex),
        credit_id=(credit_id),
        contract_address=(tx_record.contract_address),
        tx_hash=(tx_record.tx_hash),
        status=(AuditStatus.MINTED.value),
    )

    mark_transaction_confirmed(
        transaction_id=(tx_record.id),
        block_number=(receipt.blockNumber),
    )

    return {
        "status": (BlockchainTxStatus.CONFIRMED.value),
        "audit_status": (AuditStatus.MINTED.value),
        "transaction_id": (tx_record.id),
        "audit_id": (audit.audit_id),
        "credit_id": (credit_id),
        "project_token_id": int(project.on_chain_token_id),
        "audit_hash": (audit_hash_hex),
        "tx_hash": (tx_record.tx_hash),
        "block_number": (receipt.blockNumber),
    }


# ======================================================
# CarbonCredit Retirement
# ======================================================


def retire_credit(
    audit_id: str,
    amount: int,
) -> dict:

    audit = find_by_audit_id(audit_id)

    if audit is None:
        raise ValueError(f"Audit not found: {audit_id}")

    if audit.status != AuditStatus.MINTED.value:
        raise ValueError("CarbonCredit has not " "been minted for this audit")

    if audit.credit_id is None:
        raise ValueError("Audit has no credit_id")

    if amount <= 0:
        raise ValueError("Retirement amount " "must be positive")

    owner = get_operator_address()

    balance = get_credit_balance(
        account=owner,
        credit_id=int(audit.credit_id),
    )

    if balance < amount:
        raise ValueError(
            "Insufficient CarbonCredit "
            "balance. "
            f"balance={balance}, "
            f"requested={amount}"
        )

    retirement_id = generate_retirement_id()

    create_retirement(
        retirement_id=(retirement_id),
        audit_id=(audit.audit_id),
        credit_id=int(audit.credit_id),
        amount=(amount),
        owner_address=(owner),
    )

    web3 = get_web3()

    contract = get_carbon_credit_contract()

    tx_record = create_transaction(
        audit_id=(audit.audit_id),
        tx_type=(BlockchainTxType.RETIRE_CREDIT.value),
        # Critical:
        # identify the exact Retirement
        business_ref_type=("RETIREMENT"),
        business_ref_id=(retirement_id),
        chain_id=(web3.eth.chain_id),
        contract_address=(contract.address),
    )

    function = build_retire_credit_function(
        credit_id=int(audit.credit_id),
        amount=(amount),
    )

    try:

        tx_hash = broadcast_contract_transaction(function)

    except Exception as e:

        mark_transaction_failed(
            transaction_id=(tx_record.id),
            error_message=str(e),
        )

        mark_retirement_failed(retirement_id)

        raise

    update_transaction_hash(
        transaction_id=(tx_record.id),
        tx_hash=(tx_hash),
    )

    update_retirement_tx_hash(
        retirement_id=(retirement_id),
        tx_hash=(tx_hash),
    )

    try:

        receipt = wait_for_transaction_receipt(tx_hash)

    except TimeExhausted:

        return {
            "status": (BlockchainTxStatus.PENDING.value),
            "retirement_id": (retirement_id),
            "transaction_id": (tx_record.id),
            "tx_hash": (tx_hash),
        }

    if receipt.status != 1:

        mark_transaction_failed(
            transaction_id=(tx_record.id),
            error_message=("Retirement transaction " "reverted"),
        )

        mark_retirement_failed(retirement_id)

        raise RuntimeError("CarbonCredit retirement " "transaction reverted")

    return _confirm_credit_retirement(
        tx_record=tx_record,
        receipt=receipt,
        retirement_id=retirement_id,
    )


def _confirm_credit_retirement(
    tx_record,
    receipt,
    retirement_id: str,
) -> dict:

    retirement = find_retirement_by_id(retirement_id)

    if retirement is None:
        raise ValueError("Retirement not found")

    event = parse_credit_retired_event(receipt)

    if int(event["credit_id"]) != int(retirement.credit_id):
        raise RuntimeError("CreditRetired " "creditId mismatch")

    if int(event["amount"]) != int(retirement.amount):
        raise RuntimeError("CreditRetired " "amount mismatch")

    if event["account"].lower() != retirement.owner_address.lower():
        raise RuntimeError("CreditRetired " "account mismatch")

    mark_retirement_confirmed(
        retirement_id=(retirement.retirement_id),
        tx_hash=(tx_record.tx_hash),
    )

    mark_transaction_confirmed(
        transaction_id=(tx_record.id),
        block_number=(receipt.blockNumber),
    )

    new_balance = get_credit_balance(
        account=(retirement.owner_address),
        credit_id=int(retirement.credit_id),
    )

    return {
        "status": (BlockchainTxStatus.CONFIRMED.value),
        "retirement_id": (retirement.retirement_id),
        "transaction_id": (tx_record.id),
        "audit_id": (retirement.audit_id),
        "credit_id": int(retirement.credit_id),
        "amount": int(retirement.amount),
        "owner": (retirement.owner_address),
        "remaining_balance": (new_balance),
        "tx_hash": (tx_record.tx_hash),
        "block_number": (receipt.blockNumber),
    }


# ======================================================
# Unified Reconciliation
# ======================================================


def reconcile_transaction(
    transaction_id: int,
) -> dict:

    tx = find_transaction_by_id(transaction_id)

    if tx is None:
        raise ValueError("Blockchain transaction " "not found")

    # ----------------------------------------------
    # Already finished
    # ----------------------------------------------

    if tx.status == BlockchainTxStatus.CONFIRMED.value:
        return {
            "status": (BlockchainTxStatus.CONFIRMED.value),
            "transaction_id": (tx.id),
            "tx_hash": (tx.tx_hash),
        }

    if tx.status == BlockchainTxStatus.FAILED.value:
        return {
            "status": (BlockchainTxStatus.FAILED.value),
            "transaction_id": (tx.id),
            "tx_hash": (tx.tx_hash),
        }

    # ----------------------------------------------
    # Broadcast may not have happened yet
    # ----------------------------------------------

    if not tx.tx_hash:
        return {
            "status": (BlockchainTxStatus.PENDING.value),
            "transaction_id": (tx.id),
            "reason": ("Transaction has " "no tx_hash yet"),
        }

    # ----------------------------------------------
    # Query actual chain state
    # ----------------------------------------------

    receipt = get_transaction_receipt(tx.tx_hash)

    if receipt is None:
        return {
            "status": (BlockchainTxStatus.PENDING.value),
            "transaction_id": (tx.id),
            "tx_hash": (tx.tx_hash),
        }

    # ----------------------------------------------
    # Actual EVM failure
    # ----------------------------------------------

    if receipt.status != 1:

        mark_transaction_failed(
            transaction_id=(tx.id),
            error_message=("Transaction reverted"),
        )

        _handle_reverted_business_state(tx)

        return {
            "status": (BlockchainTxStatus.FAILED.value),
            "transaction_id": (tx.id),
            "tx_hash": (tx.tx_hash),
        }

    # ----------------------------------------------
    # Confirm based on tx_type
    # ----------------------------------------------

    if tx.tx_type == BlockchainTxType.MINT_PROJECT_NFT.value:
        return reconcile_project_nft_mint(
            tx=tx,
            receipt=receipt,
        )

    if tx.tx_type == BlockchainTxType.MINT_CREDIT.value:
        return reconcile_credit_mint(
            tx=tx,
            receipt=receipt,
        )

    if tx.tx_type == BlockchainTxType.RETIRE_CREDIT.value:
        return reconcile_credit_retirement(
            tx=tx,
            receipt=receipt,
        )

    raise ValueError("Unsupported transaction type: " f"{tx.tx_type}")


def _handle_reverted_business_state(
    tx,
):

    if tx.tx_type == BlockchainTxType.MINT_CREDIT.value:
        update_audit_status(
            audit_id=(tx.audit_id),
            status=(AuditStatus.APPROVED.value),
        )

    elif tx.tx_type == BlockchainTxType.RETIRE_CREDIT.value:

        if tx.business_ref_id:

            retirement = find_retirement_by_id(tx.business_ref_id)

            if retirement is not None:

                mark_retirement_failed(retirement.retirement_id)


def reconcile_project_nft_mint(
    tx,
    receipt,
) -> dict:

    audit = find_by_audit_id(tx.audit_id)

    if audit is None:
        raise ValueError("Audit not found")

    if not audit.project_id:
        raise ValueError("Audit has no project_id")

    project = find_by_project_id(audit.project_id)

    if project is None:
        raise ValueError("Project not found")

    return _confirm_project_nft_mint(
        tx_record=tx,
        receipt=receipt,
        project=project,
    )


def reconcile_credit_mint(
    tx,
    receipt,
) -> dict:

    audit = find_by_audit_id(tx.audit_id)

    if audit is None:
        raise ValueError("Audit not found")

    if not audit.project_id:
        raise ValueError("Audit has no project_id")

    project = find_by_project_id(audit.project_id)

    if project is None:
        raise ValueError("Project not found")

    if project.on_chain_token_id is None:
        raise ValueError("Project has no " "on-chain tokenId")

    return _confirm_credit_mint(
        tx_record=tx,
        receipt=receipt,
        audit=audit,
        project=project,
    )


def reconcile_credit_retirement(
    tx,
    receipt,
) -> dict:

    if tx.business_ref_type != "RETIREMENT":
        raise RuntimeError(
            "RETIRE_CREDIT transaction " "has invalid " "business_ref_type"
        )

    if not tx.business_ref_id:
        raise RuntimeError("RETIRE_CREDIT transaction " "has no business_ref_id")

    retirement = find_retirement_by_id(tx.business_ref_id)

    if retirement is None:
        raise ValueError("Retirement not found: " f"{tx.business_ref_id}")

    return _confirm_credit_retirement(
        tx_record=tx,
        receipt=receipt,
        retirement_id=(retirement.retirement_id),
    )
