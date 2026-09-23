from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.connection import Base


class CarbonProject(Base):

    __tablename__ = "carbon_project"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    project_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    project_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    project_region: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    on_chain_token_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    contract_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    mint_tx_hash: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class CarbonAudit(Base):

    __tablename__ = "carbon_audit"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("carbon_project.project_id"),
        nullable=True,
        index=True,
    )

    audit_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    thread_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    project_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    project_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    project_region: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    annual_generation_mwh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    grid_emission_factor: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    carbon_estimate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    audit_report: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # =============================================
    # CarbonCredit on-chain fields
    # =============================================

    audit_hash: Mapped[str | None] = mapped_column(
        String(66),
        nullable=True,
        index=True,
    )

    credit_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    credit_contract_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    credit_mint_tx_hash: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class BlockchainTransaction(Base):

    __tablename__ = "blockchain_transaction"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    audit_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("carbon_audit.audit_id"),
        nullable=False,
        index=True,
    )

    tx_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    # =============================================
    # Business reference
    # =============================================

    business_ref_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    business_ref_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    # =============================================
    # Blockchain
    # =============================================

    chain_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    contract_address: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    tx_hash: Mapped[str | None] = mapped_column(
        String(80),
        unique=True,
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
    )

    block_number: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class CarbonCreditRetirement(Base):

    __tablename__ = "carbon_credit_retirement"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    retirement_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    audit_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("carbon_audit.audit_id"),
        nullable=False,
        index=True,
    )

    credit_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    owner_address: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    tx_hash: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
