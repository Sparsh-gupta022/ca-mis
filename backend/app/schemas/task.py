"""
Pydantic schemas for the Task resource.

Only a read/response schema exists here for now — Task 2 needs one to
serve the `POST /compliance-schedules/{id}/generate` response, but full
Task CRUD (create/update schemas, request validation) is a separate
future task per API_SPEC.md. `TaskRead` mirrors the Task fields exactly
as defined in DATABASE_SPEC.md / app/models/task.py; the future Task CRUD
task should reuse this class rather than redefining it.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import TaskStatus


class TaskRead(BaseModel):
    """Response shape for a single task."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    compliance_schedule_id: int | None
    task_type: str
    period: str
    due_date: date
    assignee: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
