from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Float,
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
