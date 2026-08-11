"""
Client — the customer master for the firm (a CA firm's client, e.g. a
company, LLP, or individual whose compliance work is tracked).
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.compliance_schedule import ComplianceSchedule
    from app.models.task import Task


class Client(Base):
    """A client of the CA firm."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Free-text entity classification (e.g. "Private Limited", "LLP",
    # "Proprietorship", "Individual"). Kept as a plain string rather than a
    # DB enum — see DATABASE_SPEC.md "Design assumptions".
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Single field covering PAN or GSTIN (whichever applies to the client).
    # Nullable because a brand-new client may not have this on file yet.
    pan_gstin: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)

    # Free-text contact info (phone / email / person). Kept simple for MVP.
    contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Stored as a plain string because authentication / user management is
    # explicitly out of scope for this MVP. See DATABASE_SPEC.md.
    partner_in_charge: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    compliance_schedules: Mapped[list["ComplianceSchedule"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="client", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Client id={self.id} name={self.name!r}>"
