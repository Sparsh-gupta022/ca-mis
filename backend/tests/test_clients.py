"""
Tests for the Client CRUD feature (Task 1).

Covers the 13 scenarios required by the task brief.
"""
from fastapi.testclient import TestClient


def _create(client: TestClient, **overrides) -> dict:
    payload = {
        "name": "Acme Traders Pvt Ltd",
        "entity_type": "Private Limited",
        "pan_gstin": "07AACCA1234H1Z1",
        "contact": "acme@example.com",
        "partner_in_charge": "CA Deepak Sharma",
    }
    payload.update(overrides)
    response = client.post("/api/v1/clients", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# 1. Create client
def test_create_client(client: TestClient):
    body = _create(client)
    assert body["name"] == "Acme Traders Pvt Ltd"
    assert body["entity_type"] == "Private Limited"
    assert body["id"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# 2. List clients
def test_list_clients(client: TestClient):
    _create(client, name="Acme Traders")
    _create(client, name="Beta Logistics LLP", pan_gstin="09AABCB5678L1Z2")

    response = client.get("/api/v1/clients")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


# 3. Search by name
def test_search_by_name(client: TestClient):
    _create(client, name="Acme Traders")
    _create(client, name="Beta Logistics LLP", pan_gstin="09AABCB5678L1Z2")

    response = client.get("/api/v1/clients", params={"search": "acme"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Acme Traders"


# 4. Search by PAN/GSTIN
def test_search_by_pan_gstin(client: TestClient):
    _create(client, name="Acme Traders", pan_gstin="07AACCA1234H1Z1")
    _create(client, name="Beta Logistics LLP", pan_gstin="09AABCB5678L1Z2")

    response = client.get("/api/v1/clients", params={"search": "AABCB"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Beta Logistics LLP"


# 5. Filter by partner_in_charge
def test_filter_by_partner_in_charge(client: TestClient):
    _create(client, name="Acme Traders", partner_in_charge="CA Deepak Sharma")
    _create(
        client,
        name="Beta Logistics LLP",
        pan_gstin="09AABCB5678L1Z2",
        partner_in_charge="CA Priya Singh",
    )

    response = client.get("/api/v1/clients", params={"partner_in_charge": "CA Priya Singh"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Beta Logistics LLP"


# 6. Pagination
def test_pagination(client: TestClient):
    for i in range(5):
        _create(client, name=f"Client {i}", pan_gstin=None)

    response = client.get("/api/v1/clients", params={"page": 2, "page_size": 2})
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2


# 7. Get client by ID
def test_get_client_by_id(client: TestClient):
    created = _create(client)
    response = client.get(f"/api/v1/clients/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


# 8. Update client
def test_update_client(client: TestClient):
    created = _create(client)
    response = client.put(f"/api/v1/clients/{created['id']}", json={"contact": "new@acme.com"})
    assert response.status_code == 200
    body = response.json()
    assert body["contact"] == "new@acme.com"
    # untouched fields remain unchanged
    assert body["name"] == created["name"]
    assert body["entity_type"] == created["entity_type"]


# 9. Delete client
def test_delete_client(client: TestClient):
    created = _create(client)
    response = client.delete(f"/api/v1/clients/{created['id']}")
    assert response.status_code == 204

    follow_up = client.get(f"/api/v1/clients/{created['id']}")
    assert follow_up.status_code == 404


# 10. Get nonexistent client -> 404
def test_get_nonexistent_client_404(client: TestClient):
    response = client.get("/api/v1/clients/999999")
    assert response.status_code == 404


# 11. Update nonexistent client -> 404
def test_update_nonexistent_client_404(client: TestClient):
    response = client.put("/api/v1/clients/999999", json={"contact": "x@example.com"})
    assert response.status_code == 404


# 12. Delete nonexistent client -> 404
def test_delete_nonexistent_client_404(client: TestClient):
    response = client.delete("/api/v1/clients/999999")
    assert response.status_code == 404


# 13. Missing required fields -> validation error
def test_create_missing_required_fields_422(client: TestClient):
    response = client.post("/api/v1/clients", json={"entity_type": "LLP"})
    assert response.status_code == 422

    response = client.post("/api/v1/clients", json={"name": "No Entity Type Co"})
    assert response.status_code == 422


# Extra: cascade delete removes dependent schedules/tasks (DATABASE_SPEC.md ON DELETE CASCADE)
def test_delete_client_cascades_to_schedules_and_tasks(client: TestClient, db_session):
    from datetime import date

    from app.models import ComplianceSchedule, RecurrenceType, Task

    created = _create(client)

    schedule = ComplianceSchedule(
        client_id=created["id"],
        compliance_type="GSTR-3B",
        recurrence=RecurrenceType.MONTHLY,
        start_date=date(2026, 4, 1),
    )
    db_session.add(schedule)
    db_session.flush()

    task = Task(
        client_id=created["id"],
        compliance_schedule_id=schedule.id,
        task_type="GSTR-3B",
        period="Aug 2026",
        due_date=date(2026, 8, 20),
    )
    db_session.add(task)
    db_session.commit()

    response = client.delete(f"/api/v1/clients/{created['id']}")
    assert response.status_code == 204

    assert db_session.query(ComplianceSchedule).count() == 0
    assert db_session.query(Task).count() == 0
