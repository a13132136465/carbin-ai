from datetime import datetime

from sqlalchemy import (
    String,
    Float,
    Text,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.connection import Base


class CarbonAudit(Base):

    __tablename__ = "carbon_audit"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
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
