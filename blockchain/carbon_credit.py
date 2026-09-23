from blockchain.contracts import (
    get_carbon_credit_contract,
)


def get_credit_id_by_audit_hash(
    audit_hash: bytes,
) -> int:
    """
    Find creditId by auditHash.

    Expected:
        0 -> not issued
        >0 -> issued

    Function name must match deployed ABI.
    """

    contract = get_carbon_credit_contract()

    return contract.functions.getCreditIdByAuditHash(audit_hash).call()


def get_credit_batch(
    credit_id: int,
):
    """
    Read CreditBatch.

    Expected fields:

        projectTokenId
        auditHash
        vintage
        totalIssued
    """

    contract = get_carbon_credit_contract()

    return contract.functions.getBatch(credit_id).call()


def get_credit_balance(
    account: str,
    credit_id: int,
) -> int:
    """
    ERC1155 balanceOf(account, id)
    """

    contract = get_carbon_credit_contract()

    return contract.functions.balanceOf(
        account,
        credit_id,
    ).call()


# ======================================================
# Mint
# ======================================================


def build_mint_credit_function(
    recipient: str,
    project_token_id: int,
    audit_hash: bytes,
    vintage: int,
    amount: int,
):
    """
    Build:

        mintCredit(
            address to,
            uint256 projectTokenId,
            bytes32 auditHash,
            uint64 vintage,
            uint256 amount
        )

    Does NOT broadcast.
    """

    contract = get_carbon_credit_contract()

    return contract.functions.mintCredit(
        recipient,
        project_token_id,
        audit_hash,
        vintage,
        amount,
    )


def parse_credit_minted_event(
    receipt,
) -> dict:

    contract = get_carbon_credit_contract()

    events = contract.events.CreditMinted().process_receipt(receipt)

    if not events:
        raise RuntimeError("CreditMinted event " "not found")

    event = events[0]

    return {
        "credit_id": (event["args"]["creditId"]),
        "project_token_id": (event["args"]["projectTokenId"]),
        "audit_hash": (event["args"]["auditHash"]),
        "recipient": (event["args"]["recipient"]),
        "amount": (event["args"]["amount"]),
    }


# ======================================================
# Retirement
# ======================================================


def build_retire_credit_function(
    credit_id: int,
    amount: int,
):
    """
    Build CarbonCredit retirement call.

    Assumed Solidity interface:

        retireCredit(
            uint256 creditId,
            uint256 amount
        )

    IMPORTANT:
    If your deployed function has a different
    name/signature, modify here according to ABI.
    """

    contract = get_carbon_credit_contract()

    return contract.functions.retireCredit(
        credit_id,
        amount,
    )


def parse_credit_retired_event(
    receipt,
) -> dict:
    """
    Assumed event:

        CreditRetired(
            uint256 indexed creditId,
            address indexed account,
            uint256 amount
        )

    Event field names must match deployed ABI.
    """

    contract = get_carbon_credit_contract()

    events = contract.events.CreditRetired().process_receipt(receipt)

    if not events:
        raise RuntimeError("CreditRetired event " "not found")

    event = events[0]

    return {
        "credit_id": (event["args"]["creditId"]),
        "account": (event["args"]["account"]),
        "amount": (event["args"]["amount"]),
    }
