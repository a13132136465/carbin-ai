from datetime import datetime

from database.connection import (
    SessionLocal,
)

from database.models import (
    BlockchainTransaction,
)

from domain.blockchain_status import (
    BlockchainTxStatus,
)


def create_transaction(
    audit_id: str,
    tx_type: str,
    chain_id: int,
    contract_address: str,
    business_ref_type: str | None = None,
    business_ref_id: str | None = None,
) -> BlockchainTransaction:

    with SessionLocal() as session:

        tx = BlockchainTransaction(
            audit_id=audit_id,
            tx_type=tx_type,
            business_ref_type=(business_ref_type),
            business_ref_id=(business_ref_id),
            chain_id=chain_id,
            contract_address=(contract_address),
            status=(BlockchainTxStatus.PENDING.value),
        )

        session.add(tx)

        session.commit()

        session.refresh(tx)

        session.expunge(tx)

        return tx


def find_transaction_by_id(
    transaction_id: int,
) -> BlockchainTransaction | None:

    with SessionLocal() as session:

        tx = session.get(
            BlockchainTransaction,
            transaction_id,
        )

        if tx is not None:
            session.expunge(tx)

        return tx


def find_transaction_by_hash(
    tx_hash: str,
) -> BlockchainTransaction | None:

    with SessionLocal() as session:

        tx = (
            session.query(BlockchainTransaction)
            .filter(BlockchainTransaction.tx_hash == tx_hash)
            .first()
        )

        if tx is not None:
            session.expunge(tx)

        return tx


def update_transaction_hash(
    transaction_id: int,
    tx_hash: str,
):

    with SessionLocal() as session:

        tx = session.get(
            BlockchainTransaction,
            transaction_id,
        )

        if tx is None:
            raise ValueError("Blockchain transaction " "not found")

        tx.tx_hash = tx_hash

        session.commit()


def mark_transaction_confirmed(
    transaction_id: int,
    block_number: int | None = None,
):

    with SessionLocal() as session:

        tx = session.get(
            BlockchainTransaction,
            transaction_id,
        )

        if tx is None:
            raise ValueError("Blockchain transaction " "not found")

        tx.status = BlockchainTxStatus.CONFIRMED.value

        tx.block_number = block_number

        tx.confirmed_at = datetime.utcnow()

        tx.error_message = None

        session.commit()


def mark_transaction_failed(
    transaction_id: int,
    error_message: str | None = None,
):

    with SessionLocal() as session:

        tx = session.get(
            BlockchainTransaction,
            transaction_id,
        )

        if tx is None:
            raise ValueError("Blockchain transaction " "not found")

        tx.status = BlockchainTxStatus.FAILED.value

        tx.error_message = error_message

        session.commit()
