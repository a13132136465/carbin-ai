from web3 import Web3


def audit_id_to_hash(
    audit_id: str,
) -> bytes:
    """
    Convert CarbonAI audit_id to Solidity bytes32.

    Equivalent Solidity logic:

        keccak256(bytes(auditId))
    """

    if not audit_id:
        raise ValueError("audit_id is required")

    return Web3.keccak(text=audit_id)


def project_id_to_hash(
    project_id: str,
) -> bytes:
    """
    Utility for project_id hashing.

    CarbonProjectNFT currently receives projectId
    as string directly, so this function is not
    required for mintProject().

    Keep it here for future verification or
    other on-chain mappings.
    """

    if not project_id:
        raise ValueError("project_id is required")

    return Web3.keccak(text=project_id)
