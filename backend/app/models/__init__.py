"""
Import every model here so that:
1. `Base.metadata` is aware of all tables (needed for Alembic autogenerate).
2. Application code can do `from app.models import Client, Task, ...`.
"""
from app.models.checklist_item import ChecklistItem
from app.models.client import Client
from app.models.compliance_schedule import ComplianceSchedule
from app.models.enums import RecurrenceType, TaskStatus
from app.models.task import Task

__all__ = [
    "Client",
    "ComplianceSchedule",
    "Task",
    "ChecklistItem",
    "TaskStatus",
    "RecurrenceType",
]
