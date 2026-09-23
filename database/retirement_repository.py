from datetime import datetime

from database.connection import (
    SessionLocal,
)

from database.models import (
    CarbonCreditRetirement,
)

from domain.retirement_status import (
    RetirementStatus,
)


def create_retirement(
    retirement_id: str,
    audit_id: str,
    credit_id: int,
    amount: int,
    owner_address: str,
) -> CarbonCreditRetirement:

    with SessionLocal() as session:

        retirement = CarbonCreditRetirement(
            retirement_id=(retirement_id),
            audit_id=(audit_id),
            credit_id=(credit_id),
            amount=(amount),
            owner_address=(owner_address),
            status=(RetirementStatus.PENDING.value),
        )

        session.add(retirement)

        session.commit()

        session.refresh(retirement)

        session.expunge(retirement)

        return retirement


def find_retirement_by_id(
    retirement_id: str,
) -> CarbonCreditRetirement | None:

    with SessionLocal() as session:

        retirement = (
            session.query(CarbonCreditRetirement)
            .filter(CarbonCreditRetirement.retirement_id == retirement_id)
            .first()
        )

        if retirement is not None:
            session.expunge(retirement)

        return retirement


def find_retirement_by_tx_hash(
    tx_hash: str,
) -> CarbonCreditRetirement | None:

    with SessionLocal() as session:

        retirement = (
            session.query(CarbonCreditRetirement)
            .filter(CarbonCreditRetirement.tx_hash == tx_hash)
            .first()
        )

        if retirement is not None:
            session.expunge(retirement)

        return retirement


def update_retirement_tx_hash(
    retirement_id: str,
    tx_hash: str,
):

    with SessionLocal() as session:

        retirement = (
            session.query(CarbonCreditRetirement)
            .filter(CarbonCreditRetirement.retirement_id == retirement_id)
            .first()
        )

        if retirement is None:
            raise ValueError("Retirement not found")

        retirement.tx_hash = tx_hash

        session.commit()


def mark_retirement_confirmed(
    retirement_id: str,
    tx_hash: str,
):

    with SessionLocal() as session:

        retirement = (
            session.query(CarbonCreditRetirement)
            .filter(CarbonCreditRetirement.retirement_id == retirement_id)
            .first()
        )

        if retirement is None:
            raise ValueError("Retirement not found")

        retirement.status = RetirementStatus.CONFIRMED.value

        retirement.tx_hash = tx_hash

        retirement.confirmed_at = datetime.utcnow()

        session.commit()


def mark_retirement_failed(
    retirement_id: str,
):

    with SessionLocal() as session:

        retirement = (
            session.query(CarbonCreditRetirement)
            .filter(CarbonCreditRetirement.retirement_id == retirement_id)
            .first()
        )

        if retirement is None:
            raise ValueError("Retirement not found")

        retirement.status = RetirementStatus.FAILED.value

        session.commit()
