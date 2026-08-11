"""
ComplianceSchedule — the recurring "rule" for a client (e.g. "this client
files GSTR-3B every month"). A background/service-layer job (built in a
later task) reads active schedules and generates period-specific Task rows
from them.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import RecurrenceType

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.task import Task


class ComplianceSchedule(Base):
    """A recurring compliance rule owned by a client."""

    __tablename__ = "compliance_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # e.g. "GSTR-3B", "TDS Return", "Income Tax Return", "ROC Filing",
    # "Statutory Audit". Kept as free text rather than a DB enum because the
    # firm's compliance catalogue is larger than this MVP should hardcode.
    # See DATABASE_SPEC.md "Design assumptions".
    compliance_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    recurrence: Mapped[RecurrenceType] = mapped_column(
        SAEnum(
            RecurrenceType,
            name="recurrence_type",
            native_enum=True,
            # See Task.status for why values_callable is required here.
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    # Date the recurrence becomes active — used by the (future) generation
    # job to know where to start producing Task rows.
    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Optional date after which no further Tasks should be generated.
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Number of days after a period's end that the task is due. Nullable —
    # the generation task may instead use a fixed statutory due date table.
    # This is a placeholder field for the future recurring-task-generation
    # feature; documented as an assumption in DATABASE_SPEC.md.
    due_day_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Default assignee for tasks generated from this schedule. Stored as a
    # plain string — see Client.partner_in_charge for the same rationale.
    default_assignee: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped["Client"] = relationship(back_populates="compliance_schedules")
    tasks: Mapped[list["Task"]] = relationship(back_populates="compliance_schedule")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ComplianceSchedule id={self.id} type={self.compliance_type!r} recurrence={self.recurrence}>"
