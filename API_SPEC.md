# API_SPEC.md — HSDG & Associates MIS

This is the **planned API contract** for the full application. Task 0
implements none of these feature endpoints — only `GET /health` exists
today (see `app/main.py`). Future tasks implement one group at a time and
must follow this contract rather than inventing new paths or names.

All feature routes are mounted under the prefix `/api/v1` (see
`app.core.config.settings.api_v1_prefix`). Examples below omit the prefix
for brevity — e.g. "`GET /clients`" means `GET /api/v1/clients`.

## Naming Conventions

- Resource is always **`clients`**, never `customer(s)`.
- Resource is always **`tasks`**, never `jobs`/`items`/`compliances`.
- Resource is always **`compliance-schedules`** (kebab-case in URLs,
  matches the `ComplianceSchedule` model).
- Resource is always **`checklists`** for checklist items in the URL
  (the model is `ChecklistItem`, nested under a task).
- JSON bodies use `snake_case` keys, matching the SQLAlchemy/Pydantic
  field names (e.g. `pan_gstin`, `due_date`, `partner_in_charge`).
- List endpoints return `{"items": [...], "total": <int>}` — never a bare
  array — so pagination metadata can be added later without a breaking
  change.
- Standard status codes: `200` (OK), `201` (Created), `204` (No Content,
  used for successful DELETE), `400` (validation error), `404` (not
  found), `422` (Pydantic validation error, FastAPI default).

---

## `/clients`

### `GET /clients`
List clients.

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `search` | string | Optional. Matches against `name` / `pan_gstin` |
| `partner_in_charge` | string | Optional filter |
| `page`, `page_size` | int | Optional pagination |

**Response `200`:**
```json
{ "items": [ { "id": 1, "name": "...", "entity_type": "...", "pan_gstin": "...", "contact": "...", "partner_in_charge": "...", "created_at": "...", "updated_at": "..." } ], "total": 15 }
```

### `POST /clients`
Create a client.

**Request body:** `name` (required), `entity_type` (required),
`pan_gstin` (optional), `contact` (optional), `partner_in_charge`
(optional).

**Response:** `201` with the created client. `422` on validation failure.

### `GET /clients/{client_id}`
Fetch a single client. `404` if not found.

### `PUT /clients/{client_id}`
Edit a client (full update of the editable fields above). `404` if not
found, `422` on validation failure.

### `DELETE /clients/{client_id}`
Delete a client. `204` on success, `404` if not found. (Cascades to the
client's schedules/tasks per `DATABASE_SPEC.md` — the implementing task
should confirm this is the desired product behavior before wiring it up,
since the assessment doesn't mention client deletion explicitly.)

---

## `/compliance-schedules`

### `GET /compliance-schedules`
List recurring compliance schedules.

**Query parameters:** `client_id`, `is_active`, `recurrence`.

### `POST /compliance-schedules`
Create a recurring schedule.

**Request body:** `client_id` (required), `compliance_type` (required),
`recurrence` (required, one of `Monthly`/`Quarterly`/`Annual`),
`start_date` (required), `end_date` (optional), `due_day_offset`
(optional), `default_assignee` (optional).

### `GET /compliance-schedules/{schedule_id}`
Fetch a single schedule. `404` if not found.

### `PUT /compliance-schedules/{schedule_id}`
Edit a schedule.

### `DELETE /compliance-schedules/{schedule_id}`
Delete (or deactivate — implementing task's call, document the choice)
a schedule. Existing generated tasks are preserved (`compliance_schedule_id`
set to null per the `ON DELETE SET NULL` FK).

### `POST /compliance-schedules/{schedule_id}/generate`
Trigger generation of the next period's `Task` from this schedule (or a
range of periods — implementing task defines the exact request body).
This is the "auto-generation of recurring tasks" feature. Must be
idempotent: re-running for a period that already has a generated task
should not create a duplicate.

---

## `/tasks`

### `GET /tasks`
List tasks, with filtering (this endpoint backs the "Task filters"
requirement).

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `client_id` | int | Filter by client |
| `assignee` | string | Filter by assignee |
| `status` | string | One of the 4 status values |
| `task_type` | string | e.g. `GSTR-3B` |
| `due_date_from`, `due_date_to` | date | Date range filter on `due_date` |
| `page`, `page_size` | int | Optional pagination |

**Response `200`:** `{ "items": [Task...], "total": <int> }`, each Task
including its `client` summary (id + name) so the UI doesn't need a
second call per row.

### `POST /tasks`
Create a one-off task (not tied to a schedule).

**Request body:** `client_id` (required), `task_type` (required),
`period` (required), `due_date` (required), `assignee` (optional),
`status` (optional, defaults to `Not Started`).

### `GET /tasks/{task_id}`
Fetch a single task, including its checklist items. `404` if not found.

### `PUT /tasks/{task_id}`
Edit a task, including status transitions (e.g. moving to `Filed`).

### `DELETE /tasks/{task_id}`
Delete a task. `204` on success.

---

## `/checklists`

Checklist items are nested under a task in the URL, since they only ever
make sense in the context of one task.

### `GET /tasks/{task_id}/checklists`
List the checklist items for a task.

### `POST /tasks/{task_id}/checklists`
Add a checklist item to a task.

**Request body:** `document_name` (required), `is_received` (optional,
defaults to `false`).

### `PUT /checklists/{checklist_item_id}`
Edit a checklist item — primarily used to toggle `is_received`.

**Request body:** `document_name` (optional), `is_received` (optional).

### `DELETE /checklists/{checklist_item_id}`
Remove a checklist item. `204` on success.

---

## `/dashboard`

Read-only aggregate endpoints. All four map directly to the "Dashboard"
requirement in the assessment.

### `GET /dashboard/due-this-week`
Tasks with `due_date` in the current week and `status != Filed`.

### `GET /dashboard/overdue`
Tasks with `due_date` in the past and `status != Filed`.

### `GET /dashboard/awaiting-client`
Tasks with `status == "Awaiting Client"`.

### `GET /dashboard/workload`
Open (`status != Filed`) task counts grouped by `assignee`.

**Response `200` (all four):**
```json
{ "items": [Task...], "total": <int> }
```
except `workload`, which returns:
```json
{ "items": [ { "assignee": "Priya", "open_task_count": 12 } ] }
```

---

## Not Yet Specified

Request/response field-level schemas (exact Pydantic models) are defined
by the task that implements each group, using the field lists in
`DATABASE_SPEC.md` as the source of truth for what each resource
contains. This file defines the contract shape (paths, methods,
purpose); implementing tasks should not deviate from the resource names,
prefixes, or response envelope (`{"items": ..., "total": ...}`) documented
here without a note in their `HANDOFF_*.md`.
