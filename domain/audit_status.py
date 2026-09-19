from enum import Enum


class AuditStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    NEEDS_INPUT = "NEEDS_INPUT"
    COMPLETED = "COMPLETED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    MINTING = "MINTING"
    MINTED = "MINTED"