"""
Tests for the Compliance Schedule + recurring task generation feature
(Task 2).

Uses the shared `client`/`db_session` fixtures from tests/conftest.py
(same isolated hsdg_mis_test database as the Task 1 Client tests).
"""
from datetime import date

from fastapi.testclient import TestClient

from app.models import Client, ComplianceSchedule, RecurrenceType, Task


def _create_client(client: TestClient, **overrides) -> dict:
    payload = {"name": "Acme Traders Pvt Ltd", "entity_type": "Private Limited"}
    payload.update(overrides)
    response = client.post("/api/v1/clients", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_schedule(client: TestClient, client_id: int, **overrides) -> dict:
    payload = {
        "client_id": client_id,
        "compliance_type": "GSTR-3B",
        "recurrence": "Monthly",
        "start_date": "2026-04-01",
        "due_day_offset": 20,
        "default_assignee": "Priya",
    }
    payload.update(overrides)
    response = client.post("/api/v1/compliance-schedules", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- Schedule CRUD -----------------------------------------------------


def test_create_schedule(client: TestClient):
    c = _create_client(client)
    body = _create_schedule(client, c["id"])
    assert body["client_id"] == c["id"]
    assert body["compliance_type"] == "GSTR-3B"
    assert body["recurrence"] == "Monthly"
    assert body["is_active"] is True
    assert body["id"] is not None


def test_create_schedule_nonexistent_client_404(client: TestClient):
    response = client.post(
        "/api/v1/compliance-schedules",
        json={
            "client_id": 999999,
            "compliance_type": "GSTR-3B",
            "recurrence": "Monthly",
            "start_date": "2026-04-01",
        },
    )
    assert response.status_code == 404


def test_create_schedule_missing_required_fields_422(client: TestClient):
    response = client.post("/api/v1/compliance-schedules", json={"compliance_type": "GSTR-3B"})
    assert response.status_code == 422


def test_create_schedule_invalid_recurrence_422(client: TestClient):
    c = _create_client(client)
    response = client.post(
        "/api/v1/compliance-schedules",
        json={
            "client_id": c["id"],
            "compliance_type": "GSTR-3B",
            "recurrence": "Fortnightly",  # not one of Monthly/Quarterly/Annual
            "start_date": "2026-04-01",
        },
    )
    assert response.status_code == 422


def test_list_schedules(client: TestClient):
    c = _create_client(client)
    _create_schedule(client, c["id"], compliance_type="GSTR-3B")
    _create_schedule(client, c["id"], compliance_type="TDS Return", recurrence="Quarterly")

    response = client.get("/api/v1/compliance-schedules")
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_filter_by_client_id(client: TestClient):
    c1 = _create_client(client, name="Client One")
    c2 = _create_client(client, name="Client Two")
    _create_schedule(client, c1["id"])
    _create_schedule(client, c2["id"])

    response = client.get("/api/v1/compliance-schedules", params={"client_id": c1["id"]})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["client_id"] == c1["id"]


def test_filter_by_is_active(client: TestClient):
    c = _create_client(client)
    active = _create_schedule(client, c["id"], compliance_type="GSTR-3B")
    _create_schedule(client, c["id"], compliance_type="TDS Return", recurrence="Quarterly")

    # deactivate one
    client.delete(f"/api/v1/compliance-schedules/{active['id']}")

    response = client.get("/api/v1/compliance-schedules", params={"is_active": True})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["compliance_type"] == "TDS Return"

    response = client.get("/api/v1/compliance-schedules", params={"is_active": False})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["compliance_type"] == "GSTR-3B"


def test_filter_by_recurrence(client: TestClient):
    c = _create_client(client)
    _create_schedule(client, c["id"], compliance_type="GSTR-3B", recurrence="Monthly")
    _create_schedule(client, c["id"], compliance_type="TDS Return", recurrence="Quarterly")
    _create_schedule(client, c["id"], compliance_type="Statutory Audit", recurrence="Annual")

    response = client.get("/api/v1/compliance-schedules", params={"recurrence": "Quarterly"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["compliance_type"] == "TDS Return"


def test_get_schedule_by_id(client: TestClient):
    c = _create_client(client)
    created = _create_schedule(client, c["id"])
    response = client.get(f"/api/v1/compliance-schedules/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_nonexistent_schedule_404(client: TestClient):
    response = client.get("/api/v1/compliance-schedules/999999")
    assert response.status_code == 404


def test_update_schedule(client: TestClient):
    c = _create_client(client)
    created = _create_schedule(client, c["id"])
    response = client.put(
        f"/api/v1/compliance-schedules/{created['id']}",
        json={"default_assignee": "Rahul", "due_day_offset": 25},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["default_assignee"] == "Rahul"
    assert body["due_day_offset"] == 25
    # untouched fields preserved
    assert body["compliance_type"] == created["compliance_type"]
    assert body["recurrence"] == created["recurrence"]


def test_update_nonexistent_schedule_404(client: TestClient):
    response = client.put("/api/v1/compliance-schedules/999999", json={"default_assignee": "X"})
    assert response.status_code == 404


def test_update_schedule_to_nonexistent_client_404(client: TestClient):
    c = _create_client(client)
    created = _create_schedule(client, c["id"])
    response = client.put(f"/api/v1/compliance-schedules/{created['id']}", json={"client_id": 999999})
    assert response.status_code == 404


def test_delete_deactivates_schedule(client: TestClient, db_session):
    c = _create_client(client)
    created = _create_schedule(client, c["id"])

    response = client.delete(f"/api/v1/compliance-schedules/{created['id']}")
    assert response.status_code == 204

    # Row still exists (soft delete / deactivate), just inactive.
    fetched = client.get(f"/api/v1/compliance-schedules/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["is_active"] is False

    row = db_session.get(ComplianceSchedule, created["id"])
    assert row is not None
    assert row.is_active is False


def test_delete_nonexistent_schedule_404(client: TestClient):
    response = client.delete("/api/v1/compliance-schedules/999999")
    assert response.status_code == 404


# --- Generation: monthly / quarterly / annual --------------------------


def test_generate_monthly(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(
        client, c["id"], compliance_type="GSTR-3B", recurrence="Monthly", start_date="2026-04-01", due_day_offset=20
    )

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-07-15"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["generated"] is True
    task = body["task"]
    assert task["period"] == "Jul 2026"
    assert task["due_date"] == "2026-08-20"  # period end (Jul 31) + 20 days


def test_generate_quarterly(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(
        client,
        c["id"],
        compliance_type="TDS Return",
        recurrence="Quarterly",
        start_date="2026-01-01",
        due_day_offset=30,
    )

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-05-10"}
    )
    assert response.status_code == 201
    task = response.json()["task"]
    assert task["period"] == "Q2 2026"
    assert task["due_date"] == "2026-07-30"  # Q2 ends Jun 30 + 30 days


def test_generate_annual(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(
        client,
        c["id"],
        compliance_type="Statutory Audit",
        recurrence="Annual",
        start_date="2025-01-01",
        due_day_offset=90,
    )

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-05-01"}
    )
    assert response.status_code == 201
    task = response.json()["task"]
    assert task["period"] == "2026"
    assert task["due_date"] == "2027-03-31"  # year end Dec 31 + 90 days


def test_generate_no_offset_due_date_is_period_end(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(
        client, c["id"], recurrence="Monthly", start_date="2026-04-01", due_day_offset=None
    )

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-06-10"}
    )
    task = response.json()["task"]
    assert task["due_date"] == "2026-06-30"  # last day of the period, no offset applied


def test_generated_task_fields(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(
        client,
        c["id"],
        compliance_type="GSTR-3B",
        default_assignee="Priya",
        start_date="2026-04-01",
    )

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-05-10"}
    )
    task = response.json()["task"]
    assert task["client_id"] == c["id"]
    assert task["compliance_schedule_id"] == schedule["id"]
    assert task["task_type"] == "GSTR-3B"  # denormalized from schedule.compliance_type
    assert task["assignee"] == "Priya"  # inherited from schedule.default_assignee
    assert task["status"] == "Not Started"


# --- Idempotency ---------------------------------------------------------


def test_idempotent_generation_same_period(client: TestClient, db_session):
    c = _create_client(client)
    schedule = _create_schedule(client, c["id"], start_date="2026-04-01")

    first = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-07-05"}
    )
    assert first.status_code == 201
    first_task_id = first.json()["task"]["id"]
    assert first.json()["generated"] is True

    # Same calendar period, different day within it.
    second = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-07-28"}
    )
    assert second.status_code == 200
    assert second.json()["generated"] is False
    assert second.json()["task"]["id"] == first_task_id

    # Only one Task row exists for this schedule + period.
    count = (
        db_session.query(Task)
        .filter(Task.compliance_schedule_id == schedule["id"], Task.period == "Jul 2026")
        .count()
    )
    assert count == 1


def test_idempotent_generation_different_periods_creates_separate_tasks(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(client, c["id"], start_date="2026-04-01")

    july = client.post(f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-07-05"})
    august = client.post(f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-08-05"})

    assert july.status_code == 201
    assert august.status_code == 201
    assert july.json()["task"]["id"] != august.json()["task"]["id"]
    assert july.json()["task"]["period"] == "Jul 2026"
    assert august.json()["task"]["period"] == "Aug 2026"


# --- Generation edge cases ------------------------------------------------


def test_generate_before_start_date_409(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(client, c["id"], start_date="2026-04-01")

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-01-15"}
    )
    assert response.status_code == 409


def test_generate_after_end_date_409(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(
        client, c["id"], recurrence="Quarterly", start_date="2026-01-01", end_date="2026-06-30"
    )

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-09-01"}
    )
    assert response.status_code == 409


def test_generate_within_end_date_still_works(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(
        client, c["id"], recurrence="Quarterly", start_date="2026-01-01", end_date="2026-06-30"
    )

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-05-15"}
    )
    assert response.status_code == 201
    assert response.json()["task"]["period"] == "Q2 2026"


def test_generate_on_inactive_schedule_409(client: TestClient):
    c = _create_client(client)
    schedule = _create_schedule(client, c["id"], start_date="2026-04-01")
    client.delete(f"/api/v1/compliance-schedules/{schedule['id']}")  # deactivates

    response = client.post(
        f"/api/v1/compliance-schedules/{schedule['id']}/generate", json={"as_of": "2026-07-01"}
    )
    assert response.status_code == 409


def test_generate_nonexistent_schedule_404(client: TestClient):
    response = client.post("/api/v1/compliance-schedules/999999/generate", json={"as_of": "2026-07-01"})
    assert response.status_code == 404


def test_generate_no_body_defaults_to_today(client: TestClient):
    c = _create_client(client)
    # Use a start_date safely in the past so "today" is a valid period.
    schedule = _create_schedule(client, c["id"], recurrence="Annual", start_date="2020-01-01")

    response = client.post(f"/api/v1/compliance-schedules/{schedule['id']}/generate")
    assert response.status_code == 201
    assert response.json()["task"]["period"] == str(date.today().year)


# --- Relationships ---------------------------------------------------------


def test_schedule_client_relationship(client: TestClient, db_session):
    c = _create_client(client)
    schedule_body = _create_schedule(client, c["id"])

    db_client = db_session.get(Client, c["id"])
    assert len(db_client.compliance_schedules) == 1
    assert db_client.compliance_schedules[0].id == schedule_body["id"]


def test_generated_task_appears_on_schedule_relationship(client: TestClient, db_session):
    c = _create_client(client)
    schedule_body = _create_schedule(client, c["id"], start_date="2026-04-01")
    client.post(f"/api/v1/compliance-schedules/{schedule_body['id']}/generate", json={"as_of": "2026-05-01"})

    db_schedule = db_session.get(ComplianceSchedule, schedule_body["id"])
    db_session.refresh(db_schedule)
    assert len(db_schedule.tasks) == 1
    assert db_schedule.tasks[0].client_id == c["id"]


def test_deactivating_schedule_preserves_generated_tasks(client: TestClient, db_session):
    c = _create_client(client)
    schedule_body = _create_schedule(client, c["id"], start_date="2026-04-01")
    gen = client.post(
        f"/api/v1/compliance-schedules/{schedule_body['id']}/generate", json={"as_of": "2026-05-01"}
    )
    task_id = gen.json()["task"]["id"]

    client.delete(f"/api/v1/compliance-schedules/{schedule_body['id']}")

    # The task generated earlier must still exist and still reference the
    # (now-inactive) schedule — deactivating must not touch existing tasks.
    task = db_session.get(Task, task_id)
    assert task is not None
    assert task.compliance_schedule_id == schedule_body["id"]
