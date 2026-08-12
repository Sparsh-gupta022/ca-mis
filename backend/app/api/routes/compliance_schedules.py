"""
Compliance Schedule routes — CRUD under /compliance-schedules, plus
POST /compliance-schedules/{schedule_id}/generate.

Thin per ARCHITECTURE.md: no SQLAlchemy queries or business logic here,
only request/response wiring around app/services/compliance_schedule.py.
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.compliance_schedule import ComplianceSchedule
from app.models.enums import RecurrenceType
from app.schemas.compliance_schedule import (
    ComplianceScheduleCreate,
    ComplianceScheduleGenerateRequest,
    ComplianceScheduleGenerateResponse,
    ComplianceScheduleListResponse,
    ComplianceScheduleRead,
    ComplianceScheduleUpdate,
)
from app.services import client as client_service
from app.services import compliance_schedule as schedule_service

router = APIRouter()


def _get_schedule_or_404(db: Session, schedule_id: int) -> ComplianceSchedule:
    schedule = schedule_service.get_schedule(db, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance schedule not found")
    return schedule


@router.get("", response_model=ComplianceScheduleListResponse)
def list_schedules(
    client_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    recurrence: RecurrenceType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ComplianceScheduleListResponse:
    items, total = schedule_service.list_schedules(
        db,
        client_id=client_id,
        is_active=is_active,
        recurrence=recurrence,
        page=page,
        page_size=page_size,
    )
    return ComplianceScheduleListResponse(items=items, total=total)


@router.post("", response_model=ComplianceScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ComplianceScheduleCreate, db: Session = Depends(get_db)) -> ComplianceSchedule:
    # Validate the referenced client exists before creating the schedule —
    # a schedule for a nonexistent client is a 404 on the referenced
    # resource, not a generic validation error.
    if client_service.get_client(db, payload.client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return schedule_service.create_schedule(db, payload)


@router.get("/{schedule_id}", response_model=ComplianceScheduleRead)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)) -> ComplianceSchedule:
    return _get_schedule_or_404(db, schedule_id)


@router.put("/{schedule_id}", response_model=ComplianceScheduleRead)
def update_schedule(
    schedule_id: int, payload: ComplianceScheduleUpdate, db: Session = Depends(get_db)
) -> ComplianceSchedule:
    schedule = _get_schedule_or_404(db, schedule_id)
    if payload.client_id is not None and client_service.get_client(db, payload.client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return schedule_service.update_schedule(db, schedule, payload)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)) -> None:
    """
    Deactivates the schedule (is_active = False) rather than deleting the
    row — see app/services/compliance_schedule.py::deactivate_schedule
    for the rationale.
    """
    schedule = _get_schedule_or_404(db, schedule_id)
    schedule_service.deactivate_schedule(db, schedule)


@router.post("/{schedule_id}/generate", response_model=ComplianceScheduleGenerateResponse)
def generate_task(
    schedule_id: int,
    response: Response,
    payload: ComplianceScheduleGenerateRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> ComplianceScheduleGenerateResponse:
    """
    Generate the Task for the period containing `as_of` (defaults to
    today). Idempotent: calling this again for the same period returns
    the existing Task (HTTP 200) instead of creating a duplicate (HTTP
    201 is returned only when a new Task was actually inserted).
    """
    schedule = _get_schedule_or_404(db, schedule_id)
    as_of = payload.as_of if payload else None

    try:
        task, created = schedule_service.generate_task(db, schedule, as_of=as_of)
    except schedule_service.ScheduleGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return ComplianceScheduleGenerateResponse(generated=created, task=task)
