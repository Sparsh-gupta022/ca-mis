"""
ChecklistItem — a single document required for a Task (e.g. "Bank
statement", "Purchase register"), markable as received or pending.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.task import Task


class ChecklistItem(Base):
    """A single document checklist entry belonging to a Task."""

    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    document_name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_received: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    task: Mapped["Task"] = relationship(back_populates="checklist_items")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChecklistItem id={self.id} document={self.document_name!r} received={self.is_received}>"
