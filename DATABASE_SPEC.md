# DATABASE_SPEC.md — HSDG & Associates MIS

This is the **shared baseline schema** for the whole project (see
"Database Baseline Rule" in `CLAUDE_RULES.md`). Future feature tasks must
not casually change it — schema changes go through the
`SCHEMA CHANGE REQUEST` process.

Database: **PostgreSQL**. ORM: **SQLAlchemy 2.0** (typed `Mapped[...]`
style). Migrations: **Alembic**. Verified against a real local PostgreSQL
16 instance as part of Task 0 (see `HANDOFF_TASK_0.md` → Verification).

## Entity-Relationship Overview

```
Client (1) ──────< (many) ComplianceSchedule
  │                              │
  │                              │ (optional origin)
  │                              v
  └──────────< (many) Task >───── (nullable FK)
                        │
                        │ (1) ──────< (many)
                        v
                  ChecklistItem
```

- A `Client` has many `ComplianceSchedule`s and many `Task`s directly.
- A `ComplianceSchedule` is the recurring **rule** (e.g. "this client
  files GSTR-3B every month"); a later task's generation logic reads
  active schedules and produces period-specific `Task` rows from them.
- A `Task` always belongs to a `Client` directly (not only reachable via
  a schedule), so one-off tasks not tied to any recurring rule are also
  supported. A `Task` optionally references the `ComplianceSchedule` that
  generated it.
- A `Task` has many `ChecklistItem`s (the documents needed for that task).

## Design Assumptions

(See `PROJECT_SPEC.md` → "Sensible Assumptions" for the full rationale.)

- `assignee`, `default_assignee`, and `partner_in_charge` are plain
  strings — there is no `User`/auth table, since login is out of scope.
- `entity_type` (Client) and `compliance_type` (ComplianceSchedule /
  Task) are free-text strings, not native DB enums — only `status` and
  `recurrence` are fixed enumerations per the assessment.
- `pan_gstin` is a single field covering either a PAN or a GSTIN.
- IDs are auto-incrementing integers (`SERIAL`/`BIGSERIAL` via Postgres),
  not UUIDs — simplest choice for an internal MVP with no external/public
  API exposure of these IDs.
- Every table has `created_at` / `updated_at` timestamps (server-set) for
  basic auditability, even though auditing wasn't explicitly requested —
  this is minimal, standard practice, not over-engineering.

---

## Table: `clients`

| Column | Type | Nullable | PK | FK | Notes |
|---|---|---|---|---|---|
| `id` | `INTEGER` (serial) | No | ✅ | | |
| `name` | `VARCHAR(255)` | No | | | Indexed for search/sort |
| `entity_type` | `VARCHAR(100)` | No | | | Free text. See assumptions. |
| `pan_gstin` | `VARCHAR(30)` | Yes | | | Indexed. Nullable — a new client may not have this on file yet |
| `contact` | `VARCHAR(255)` | Yes | | | Free text (phone/email/person) |
| `partner_in_charge` | `VARCHAR(255)` | Yes | | | Plain string. Indexed (used for workload/filter views) |
| `created_at` | `TIMESTAMPTZ` | No | | | `server_default now()` |
| `updated_at` | `TIMESTAMPTZ` | No | | | `server_default now()`, updated on write |

**Indexes:** `name`, `pan_gstin`, `partner_in_charge`

**Relationships:** `compliance_schedules` (1→many), `tasks` (1→many).
`ON DELETE CASCADE` from client to both — deleting a client removes its
schedules and tasks. (For a real firm this cascade is aggressive; a
future task may want a soft-delete/archive flow instead of a hard
`DELETE` — flagged here as a forward-looking note, not a Task 0 decision.)

---

## Table: `compliance_schedules`

| Column | Type | Nullable | PK | FK | Notes |
|---|---|---|---|---|---|
| `id` | `INTEGER` (serial) | No | ✅ | | |
| `client_id` | `INTEGER` | No | | → `clients.id` (`ON DELETE CASCADE`) | Indexed |
| `compliance_type` | `VARCHAR(100)` | No | | | Free text, e.g. `GSTR-3B`, `TDS Return`, `ROC Filing`. Indexed |
| `recurrence` | `recurrence_type` (native Postgres enum) | No | | | See enum values below |
| `start_date` | `DATE` | No | | | Recurrence becomes active from this date |
| `end_date` | `DATE` | Yes | | | Optional — stop generating after this date |
| `due_day_offset` | `INTEGER` | Yes | | | Days after period end the task is due. Placeholder for the (future) generation task's due-date logic — see note below |
| `default_assignee` | `VARCHAR(255)` | Yes | | | Plain string |
| `is_active` | `BOOLEAN` | No | | | `server_default true` |
| `created_at` | `TIMESTAMPTZ` | No | | | `server_default now()` |
| `updated_at` | `TIMESTAMPTZ` | No | | | `server_default now()`, updated on write |

**Indexes:** `client_id`, `compliance_type`

**Enum `recurrence_type` values:** `Monthly`, `Quarterly`, `Annual`
(exact strings, per the assessment).

> **Note on `due_day_offset`:** the assessment requires recurring task
> auto-generation but does not specify the due-date computation rule
> (e.g. GSTR-3B is statutorily due the 20th of the following month; ROC
> filings have their own calendar). `due_day_offset` is a simple,
> nullable placeholder field so the schema doesn't block that future
> task. The actual generation algorithm — and whether this field is
> sufficient or a statutory due-date lookup table is needed instead — is
> explicitly left to the task that implements recurring generation. If
> that task finds this field insufficient, it must file a
> `SCHEMA CHANGE REQUEST` rather than quietly repurpose it.

**Relationships:** belongs to `Client`; has many `Task` (tasks generated
from this rule — `ON DELETE SET NULL` from schedule to task, so deleting
a schedule does not delete its already-generated tasks).

---

## Table: `tasks`

| Column | Type | Nullable | PK | FK | Notes |
|---|---|---|---|---|---|
| `id` | `INTEGER` (serial) | No | ✅ | | |
| `client_id` | `INTEGER` | No | | → `clients.id` (`ON DELETE CASCADE`) | Indexed |
| `compliance_schedule_id` | `INTEGER` | Yes | | → `compliance_schedules.id` (`ON DELETE SET NULL`) | Indexed. Null = one-off task, not generated from a rule |
| `task_type` | `VARCHAR(100)` | No | | | Denormalized (present even for one-off tasks). Indexed |
| `period` | `VARCHAR(50)` | No | | | Human label, e.g. `Jul 2026`, `Q1 FY26-27`, `FY 2025-26` |
| `due_date` | `DATE` | No | | | Indexed — powers "due this week" / "overdue" / date-range filter |
| `assignee` | `VARCHAR(255)` | Yes | | | Plain string. Indexed — powers workload-per-assignee and filter |
| `status` | `task_status` (native Postgres enum) | No | | | `server_default 'Not Started'`. Indexed — powers dashboard buckets and filter |
| `created_at` | `TIMESTAMPTZ` | No | | | `server_default now()` |
| `updated_at` | `TIMESTAMPTZ` | No | | | `server_default now()`, updated on write |

**Indexes:** `client_id`, `compliance_schedule_id`, `task_type`,
`due_date`, `assignee`, `status`

**Enum `task_status` values (exact, required by assessment):**
`Not Started`, `In Progress`, `Awaiting Client`, `Filed`

**Relationships:** belongs to `Client`; optionally belongs to a
`ComplianceSchedule`; has many `ChecklistItem` (`ON DELETE CASCADE` —
deleting a task removes its checklist).

---

## Table: `checklist_items`

| Column | Type | Nullable | PK | FK | Notes |
|---|---|---|---|---|---|
| `id` | `INTEGER` (serial) | No | ✅ | | |
| `task_id` | `INTEGER` | No | | → `tasks.id` (`ON DELETE CASCADE`) | Indexed |
| `document_name` | `VARCHAR(255)` | No | | | e.g. "Bank statement", "Sales register" |
| `is_received` | `BOOLEAN` | No | | | `server_default false` |
| `created_at` | `TIMESTAMPTZ` | No | | | `server_default now()` |
| `updated_at` | `TIMESTAMPTZ` | No | | | `server_default now()`, updated on write |

**Indexes:** `task_id`

**Relationships:** belongs to `Task`.

---

## What Task 0 Deliberately Does Not Decide

These are real, future needs the assessment implies but does not
specify enough to model correctly today. Deciding them now would be
over-engineering ahead of requirements — they are called out so a later
task addresses them explicitly (and, if they require a schema change,
through the `SCHEMA CHANGE REQUEST` process):

- The exact algorithm and idempotency rules for recurring task
  generation (how `ComplianceSchedule` → `Task` rows are produced,
  and how re-runs avoid duplicating a period that was already generated).
- Whether document checklist templates should be attached to a
  `ComplianceSchedule`/`compliance_type` (e.g. "GSTR-3B always needs a
  sales register") rather than typed freshly per task.
- Soft-delete/archival for clients instead of a hard cascading delete.

## Verification Performed (Task 0)

- A local PostgreSQL 16 instance was installed and started in the
  sandbox.
- `alembic revision --autogenerate` correctly detected all 4 tables and
  every index listed above from the SQLAlchemy models.
- `alembic upgrade head` created all 4 tables successfully.
- `alembic downgrade base` → `alembic upgrade head` was run as a round
  trip, and `alembic check` reported no drift between models and
  migration afterwards.
- Test rows were inserted through the ORM (`Client` →
  `ComplianceSchedule` → `Task` → `ChecklistItem`) and re-queried through
  the relationships to confirm foreign keys and cascades are wired
  correctly. The enum columns were confirmed to store the exact
  human-readable values (e.g. `Not Started`), not Python enum member
  names.
- The test data was removed and the schema reset to a clean, empty state
  (`downgrade base` → `upgrade head`) before handoff.
