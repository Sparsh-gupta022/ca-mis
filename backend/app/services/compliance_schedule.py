"""
Service layer for the ComplianceSchedule resource and for generating
period-specific Task rows from a schedule.

Routes call these functions; all SQLAlchemy queries and business logic
live here, per ARCHITECTURE.md.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.compliance_schedule import ComplianceSchedule
from app.models.enums import RecurrenceType
from app.models.task import Task
from app.schemas.compliance_schedule import ComplianceScheduleCreate, ComplianceScheduleUpdate


class ScheduleGenerationError(Exception):
    """
    Raised when a Task cannot be generated for a schedule at the given
    reference date (schedule inactive, or the period falls outside the
    schedule's [start_date, end_date] window). The route layer maps this
    to an HTTP 409.
    """


# --- CRUD -------------------------------------------------------------


def list_schedules(
    db: Session,
    *,
    client_id: int | None = None,
    is_active: bool | None = None,
    recurrence: RecurrenceType | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[ComplianceSchedule], int]:
    """List compliance schedules with optional filters and pagination."""
    from sqlalchemy import func

    stmt = select(ComplianceSchedule)
    count_stmt = select(func.count()).select_from(ComplianceSchedule)

    if client_id is not None:
        stmt = stmt.where(ComplianceSchedule.client_id == client_id)
        count_stmt = count_stmt.where(ComplianceSchedule.client_id == client_id)

    if is_active is not None:
        stmt = stmt.where(ComplianceSchedule.is_active == is_active)
        count_stmt = count_stmt.where(ComplianceSchedule.is_active == is_active)

    if recurrence is not None:
        stmt = stmt.where(ComplianceSchedule.recurrence == recurrence)
        count_stmt = count_stmt.where(ComplianceSchedule.recurrence == recurrence)

    total = db.execute(count_stmt).scalar_one()

    stmt = stmt.order_by(ComplianceSchedule.id).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())

    return items, total


def get_schedule(db: Session, schedule_id: int) -> ComplianceSchedule | None:
    """Fetch a single schedule by ID, or None if it doesn't exist."""
    return db.get(ComplianceSchedule, schedule_id)


def create_schedule(db: Session, payload: ComplianceScheduleCreate) -> ComplianceSchedule:
    """Create and persist a new compliance schedule."""
    schedule = ComplianceSchedule(**payload.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(
    db: Session, schedule: ComplianceSchedule, payload: ComplianceScheduleUpdate
) -> ComplianceSchedule:
    """Apply a partial update to an existing schedule."""
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(schedule, field, value)

    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def deactivate_schedule(db: Session, schedule: ComplianceSchedule) -> ComplianceSchedule:
    """
    "Delete" a schedule by deactivating it (is_active = False) rather than
    removing the row.

    See HANDOFF_TASK_2_COMPLIANCE_SCHEDULES.md for the rationale: this
    preserves the schedule's history and its link from already-generated
    tasks, and is one of the two behaviors API_SPEC.md explicitly leaves
    to the implementer ("Delete (or deactivate...)"). The underlying
    ON DELETE SET NULL foreign key from Task.compliance_schedule_id is
    unused by this endpoint but remains available if a future task
    decides a true hard-delete is needed instead.
    """
    schedule.is_active = False
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


# --- Recurring task generation -----------------------------------------


def _first_of_next_month(d: date) -> date:
    """First day of the calendar month after the month containing `d`."""
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)


def _period_bounds(recurrence: RecurrenceType, as_of: date) -> tuple[date, date, str]:
    """
    Compute (period_start, period_end, period_label) for the period that
    contains `as_of`, for the given recurrence type.

    Deliberately uses plain calendar months/quarters/years — not a
    statutory or fiscal-year calendar — per the instruction not to invent
    filing calendars the project hasn't specified. See
    HANDOFF_TASK_2_COMPLIANCE_SCHEDULES.md → "Due-date behavior" for the
    full rationale.
    """
    if recurrence == RecurrenceType.MONTHLY:
        period_start = as_of.replace(day=1)
        period_end = _first_of_next_month(period_start) - timedelta(days=1)
        label = period_start.strftime("%b %Y")
        return period_start, period_end, label

    if recurrence == RecurrenceType.QUARTERLY:
        quarter_index = (as_of.month - 1) // 3  # 0-3
        start_month = quarter_index * 3 + 1
        period_start = date(as_of.year, start_month, 1)
        # Last month of the quarter, then roll to the month after it.
        last_month_of_quarter = period_start.replace(month=start_month + 2)
        period_end = _first_of_next_month(last_month_of_quarter) - timedelta(days=1)
        label = f"Q{quarter_index + 1} {as_of.year}"
        return period_start, period_end, label

    if recurrence == RecurrenceType.ANNUAL:
        period_start = date(as_of.year, 1, 1)
        period_end = date(as_of.year, 12, 31)
        label = str(as_of.year)
        return period_start, period_end, label

    raise ValueError(f"Unhandled recurrence type: {recurrence!r}")  # pragma: no cover


def _compute_due_date(period_end: date, due_day_offset: int | None) -> date:
    """
    due_date = period_end + due_day_offset days, or period_end itself if
    no offset is configured on the schedule. See
    HANDOFF_TASK_2_COMPLIANCE_SCHEDULES.md for why this field (already
    defined in Task 0's DATABASE_SPEC.md) is sufficient for this task
    without inventing a statutory due-date table.
    """
    if due_day_offset is None:
        return period_end
    return period_end + timedelta(days=due_day_offset)


def generate_task(
    db: Session, schedule: ComplianceSchedule, as_of: date | None = None
) -> tuple[Task, bool]:
    """
    Generate (or idempotently fetch) the Task for the period that
    contains `as_of` (defaults to today).

    Returns (task, created) where `created` is False if a Task already
    existed for this schedule + period (idempotent no-op — no duplicate
    is created) and True if a new Task row was just inserted.

    Raises ScheduleGenerationError if the schedule is inactive, or if the
    computed period falls outside [schedule.start_date, schedule.end_date].
    """
    as_of = as_of or date.today()

    if not schedule.is_active:
        raise ScheduleGenerationError("Cannot generate a task for an inactive schedule.")

    period_start, period_end, label = _period_bounds(schedule.recurrence, as_of)

    if period_end < schedule.start_date:
        raise ScheduleGenerationError(
            f"Period {label!r} ends before the schedule's start_date "
            f"({schedule.start_date.isoformat()}); nothing to generate yet."
        )

    if schedule.end_date is not None and period_start > schedule.end_date:
        raise ScheduleGenerationError(
            f"Period {label!r} begins after the schedule's end_date "
            f"({schedule.end_date.isoformat()}); this schedule has ended."
        )

    existing = db.execute(
        select(Task).where(
            Task.compliance_schedule_id == schedule.id,
            Task.period == label,
        )
    ).scalar_one_or_none()

    if existing is not None:
        return existing, False

    due_date = _compute_due_date(period_end, schedule.due_day_offset)

    task = Task(
        client_id=schedule.client_id,
        compliance_schedule_id=schedule.id,
        task_type=schedule.compliance_type,
        period=label,
        due_date=due_date,
        assignee=schedule.default_assignee,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task, True
