from fastapi import (
    FastAPI,
    HTTPException,
)

from api.schemas import (
    AuditDecisionRequest,
    AuditRequest,
    AuditResumeRequest,
    BlockchainOperationResponse,
    MintCarbonCreditRequest,
    MintProjectNFTRequest,
    RetireCarbonCreditRequest,
)

from services.audit_service import (
    approve_audit,
    get_audit,
    reject_audit,
    resume_audit,
    start_audit,
)

from services.blockchain_service import (
    mint_credit_for_audit,
    mint_project_for_audit,
    reconcile_transaction,
    retire_credit,
)

from services.blockchain_query_service import (
    get_blockchain_transaction,
    get_credit_on_chain_info,
    get_project_on_chain_info,
    get_retirement_info,
)

app = FastAPI(
    title="CarbonAI API",
    version="1.0.0",
)


# ======================================================
# Health
# ======================================================


@app.get("/health")
def health():

    return {
        "status": "ok",
    }


# ======================================================
# Audit
# ======================================================


@app.post("/api/audits")
def create_audit(
    request: AuditRequest,
):

    try:

        return start_audit(request.message)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.post("/api/audits/{thread_id}/resume")
def resume_audit_api(
    thread_id: str,
    request: AuditResumeRequest,
):

    try:

        return resume_audit(
            thread_id=thread_id,
            message=request.message,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.get("/api/audits/{audit_id}")
def get_audit_api(
    audit_id: str,
):

    try:

        audit = get_audit(audit_id)

        if audit is None:
            raise HTTPException(
                status_code=404,
                detail="Audit not found",
            )

        return audit

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.post("/api/audits/{audit_id}/approve")
def approve_audit_api(
    audit_id: str,
    request: AuditDecisionRequest,
):

    try:

        return approve_audit(
            audit_id=audit_id,
            reason=request.reason,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.post("/api/audits/{audit_id}/reject")
def reject_audit_api(
    audit_id: str,
    request: AuditDecisionRequest,
):

    try:

        return reject_audit(
            audit_id=audit_id,
            reason=request.reason,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ======================================================
# CarbonProjectNFT
# ======================================================


@app.post(
    "/api/audits/{audit_id}/project-nft/mint",
    response_model=BlockchainOperationResponse,
)
def mint_project_nft_api(
    audit_id: str,
    request: MintProjectNFTRequest,
):

    try:

        result = mint_project_for_audit(
            audit_id=(audit_id),
            metadata_uri=(request.metadata_uri),
        )

        return {"data": result}

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.get("/api/projects/{project_id}/blockchain")
def get_project_blockchain_api(
    project_id: str,
):

    try:

        return get_project_on_chain_info(project_id)

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ======================================================
# CarbonCredit Mint
# ======================================================


@app.post(
    "/api/audits/{audit_id}/credits/mint",
    response_model=BlockchainOperationResponse,
)
def mint_carbon_credit_api(
    audit_id: str,
    request: MintCarbonCreditRequest,
):

    try:

        result = mint_credit_for_audit(
            audit_id=(audit_id),
            vintage=(request.vintage),
        )

        return {"data": result}

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.get("/api/audits/{audit_id}/credits")
def get_carbon_credit_api(
    audit_id: str,
):

    try:

        return get_credit_on_chain_info(audit_id)

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ======================================================
# CarbonCredit Retirement
# ======================================================


@app.post(
    "/api/audits/{audit_id}/credits/retire",
    response_model=BlockchainOperationResponse,
)
def retire_carbon_credit_api(
    audit_id: str,
    request: RetireCarbonCreditRequest,
):

    try:

        result = retire_credit(
            audit_id=(audit_id),
            amount=(request.amount),
        )

        return {"data": result}

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.get("/api/retirements/{retirement_id}")
def get_retirement_api(
    retirement_id: str,
):

    try:

        return get_retirement_info(retirement_id)

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ======================================================
# Blockchain Transactions
# ======================================================


@app.get("/api/blockchain/transactions/" "{transaction_id}")
def get_blockchain_transaction_api(
    transaction_id: int,
):

    try:

        return get_blockchain_transaction(transaction_id)

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.post(
    "/api/blockchain/transactions/" "{transaction_id}/reconcile",
    response_model=BlockchainOperationResponse,
)
def reconcile_blockchain_transaction_api(
    transaction_id: int,
):

    try:

        result = reconcile_transaction(transaction_id)

        return {"data": result}

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
