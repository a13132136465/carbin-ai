from typing import Any

from pydantic import (
    BaseModel,
    Field,
)

# ======================================================
# Audit
# ======================================================


class AuditRequest(BaseModel):

    message: str = Field(
        min_length=1,
    )


class AuditResumeRequest(BaseModel):

    message: str = Field(
        min_length=1,
    )


class AuditDecisionRequest(BaseModel):

    reason: str | None = None


# ======================================================
# Blockchain - Project NFT
# ======================================================


class MintProjectNFTRequest(BaseModel):

    metadata_uri: str = Field(
        min_length=1,
    )


# ======================================================
# Blockchain - CarbonCredit
# ======================================================


class MintCarbonCreditRequest(BaseModel):

    vintage: int | None = Field(
        default=None,
        ge=1900,
        le=3000,
    )


# ======================================================
# Blockchain - Retirement
# ======================================================


class RetireCarbonCreditRequest(BaseModel):

    amount: int = Field(
        gt=0,
    )


# ======================================================
# Generic API responses
# ======================================================


class MessageResponse(BaseModel):

    message: str


class BlockchainOperationResponse(BaseModel):

    data: dict[str, Any]
