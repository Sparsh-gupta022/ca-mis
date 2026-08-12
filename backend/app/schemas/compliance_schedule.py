"""
Pydantic schemas for the ComplianceSchedule resource, and for the
POST /compliance-schedules/{id}/generate endpoint.

These mirror the ComplianceSchedule fields exactly as defined in
DATABASE_SPEC.md / app/models/compliance_schedule.py. No fields are
added or renamed here.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RecurrenceType
from app.schemas.task import TaskRead


class ComplianceScheduleBase(BaseModel):
    """Fields shared by create/update payloads."""

    client_id: int
    compliance_type: str = Field(..., min_length=1, max_length=100)
    recurrence: RecurrenceType
    start_date: date
    end_date: date | None = None
    due_day_offset: int | None = Field(default=None, ge=0)
    default_assignee: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class ComplianceScheduleCreate(ComplianceScheduleBase):
    """
    Payload for POST /compliance-schedules.

    client_id, compliance_type, recurrence, and start_date are required
    (per API_SPEC.md); end_date, due_day_offset, default_assignee are
    optional, and is_active defaults to True.
    """


class ComplianceScheduleUpdate(BaseModel):
    """
    Payload for PUT /compliance-schedules/{schedule_id}.

    All fields optional — same partial-update convention as
    app/schemas/client.py's ClientUpdate.
    """

    client_id: int | None = None
    compliance_type: str | None = Field(default=None, min_length=1, max_length=100)
    recurrence: RecurrenceType | None = None
    start_date: date | None = None
    end_date: date | None = None
    due_day_offset: int | None = Field(default=None, ge=0)
    default_assignee: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class ComplianceScheduleRead(ComplianceScheduleBase):
    """Response shape for a single compliance schedule."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ComplianceScheduleListResponse(BaseModel):
    """Response shape for GET /compliance-schedules."""

    items: list[ComplianceScheduleRead]
    total: int


class ComplianceScheduleGenerateRequest(BaseModel):
    """
    Optional payload for POST /compliance-schedules/{schedule_id}/generate.

    `as_of` lets the caller (or a test, or a future scheduler/cron job)
    specify which reference date to generate the applicable period for.
    Defaults to today if omitted — see HANDOFF_TASK_2 for the full
    period/due-date calculation this drives.
    """

    as_of: date | None = None


class ComplianceScheduleGenerateResponse(BaseModel):
    """Response shape for POST /compliance-schedules/{schedule_id}/generate."""

    generated: bool = Field(
        description="True if a new Task was created by this call; "
        "False if a Task for this period already existed (idempotent no-op)."
    )
    task: TaskRead
