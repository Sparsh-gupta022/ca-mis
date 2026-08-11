# HANDOFF_TASK_0.md

## Task

Task 0 — Foundation for the HSDG & Associates MIS MVP.

## Status

✅ Complete. Shared architecture, database schema, and a minimal running
FastAPI skeleton are in place. No feature endpoints, recurring task
generation, checklist logic, dashboard, filtering, or seed data are
implemented — those are separate future tasks (see `CLAUDE_RULES.md`).

## Files Created

Documentation (repo root):
- `PROJECT_SPEC.md`
- `DATABASE_SPEC.md`
- `API_SPEC.md`
- `ARCHITECTURE.md`
- `CLAUDE_RULES.md`
- `README.md`
- `HANDOFF_TASK_0.md` (this file)
- `.gitignore`

Backend:
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/alembic.ini`
- `backend/alembic/env.py` (wired to `app.core.config` + `app.models` metadata)
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/cf87a537f05c_foundation_schema_clients_compliance_.py`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/core/__init__.py`
- `backend/app/core/config.py`
- `backend/app/db/__init__.py`
- `backend/app/db/base_class.py`
- `backend/app/db/session.py`
- `backend/app/models/__init__.py`
- `backend/app/models/enums.py`
- `backend/app/models/client.py`
- `backend/app/models/compliance_schedule.py`
- `backend/app/models/task.py`
- `backend/app/models/checklist_item.py`
- `backend/app/schemas/__init__.py` (empty — placeholder for future tasks)
- `backend/app/services/__init__.py` (empty — placeholder for future tasks)
- `backend/app/api/__init__.py` (empty — placeholder for future tasks)
- `backend/app/api/routes/__init__.py` (empty — placeholder for future tasks)

`frontend/` directory created but empty — no frontend work in Task 0.

## Files Modified

None — this is the first task; everything above is new.

## Database Tables

- `clients`
- `compliance_schedules`
- `tasks`
- `checklist_items`

Full column-level spec in `DATABASE_SPEC.md`.

## Relationships

```
Client 1──< ComplianceSchedule
Client 1──< Task
ComplianceSchedule 1──< Task   (nullable FK — Task.compliance_schedule_id)
Task 1──< ChecklistItem
```

`Task` belongs directly to `Client` (not only reachable through
`ComplianceSchedule`), so one-off tasks not tied to a recurring rule are
representable. See `DATABASE_SPEC.md` for cascade behavior on each FK.

## API Conventions

Established in `API_SPEC.md`, not yet implemented beyond `GET /health`:

- Prefix: `/api/v1`
- Resource names: `clients`, `compliance-schedules`, `tasks`, `checklists`, `dashboard`
- List responses: `{"items": [...], "total": <int>}`
- `snake_case` JSON keys matching model field names

## Architecture Conventions

Established in `ARCHITECTURE.md`:

```
Route (app/api/routes/) → Schema (app/schemas/) → Service (app/services/) → Model (app/models/) → PostgreSQL
```

Folder structure matches the assessment's suggested layout exactly — see
`ARCHITECTURE.md` for the full tree and per-layer responsibilities.

## Commands Required to Run

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL if needed
alembic upgrade head
uvicorn app.main:app --reload
```

Then visit `http://127.0.0.1:8000/docs`. Full detail in `README.md`.

## Verification Performed

All of the following was actually executed in this session, not assumed:

1. **Backend starts** — `python3 -c "from app.main import app"` imported
   cleanly; `uvicorn app.main:app` was started and stayed up.
2. **PostgreSQL connection works** — installed PostgreSQL 16 locally,
   created a `hsdg_mis` database, and connected successfully via
   SQLAlchemy using the app's own `Settings`/`database_url`.
3. **Alembic migration works** — `alembic revision --autogenerate`
   correctly detected all 4 tables and every planned index directly from
   the SQLAlchemy models (nothing was hand-written into the migration
   except two explicit `DROP TYPE` statements added to the downgrade —
   see "Known Limitations"). `alembic upgrade head` applied successfully.
4. **All foundation tables created** — confirmed via `psql \dt`: all 4
   tables plus `alembic_version` present. Confirmed enum values in
   Postgres directly (`pg_enum` catalog) match the required strings
   exactly (`Not Started`, `In Progress`, `Awaiting Client`, `Filed`,
   `Monthly`, `Quarterly`, `Annual`) — not Python enum member names.
5. **FastAPI `/docs` works** — live server returned `200` for `/health`,
   `/docs`, and `/openapi.json`.
6. **No credentials hardcoded** — grepped the codebase; the only
   embedded connection string is the documented local-dev placeholder
   (`postgres:postgres@localhost`) that matches `.env.example`, not a
   real secret.

Additional verification beyond the required checklist:
- Inserted a `Client` → `ComplianceSchedule` → `Task` → `ChecklistItem`
  chain through the ORM and re-queried it through the relationships to
  confirm FKs and `back_populates` are wired correctly.
- Ran a full migration round trip: `upgrade head` → `downgrade base` →
  `upgrade head`, then `alembic check` — reported **no schema drift**
  between the SQLAlchemy models and the migration.
- Reset the database to a clean, empty state (no leftover test rows)
  before finishing.

## Assumptions

Full list and rationale in `PROJECT_SPEC.md` → "Sensible Assumptions"
and `DATABASE_SPEC.md` → "Design Assumptions". Summary:

1. `assignee`, `default_assignee`, `partner_in_charge` are plain strings
   — no `User` table, since auth is out of scope.
2. `entity_type` and `compliance_type` are free-text strings, not DB
   enums — only `status` and `recurrence` are fixed enumerations per the
   assessment.
3. `Task.client_id` is a direct FK (not only reachable via
   `ComplianceSchedule`), so one-off tasks are representable.
4. `Task.compliance_schedule_id` is nullable.
5. PAN and GSTIN share a single `pan_gstin` field.
6. Integer primary keys, not UUIDs.
7. `due_day_offset` on `ComplianceSchedule` is a simple placeholder for
   future due-date computation logic — the actual generation algorithm
   is explicitly deferred to the task that implements it.

## Known Limitations

- Alembic's `autogenerate` does not emit `DROP TYPE` statements for
  Postgres native enums when the owning table is dropped. The generated
  migration's `downgrade()` was manually edited to add explicit
  `sa.Enum(name=...).drop(...)` calls so `downgrade` → `upgrade` is a
  true, repeatable round trip. Future migrations that add new enums
  should follow the same pattern if their `downgrade()` needs to be
  clean.
- No tests (pytest) were added in Task 0 — verification was done via
  direct ORM scripting and live server calls, described above. A future
  task may want to add a `tests/` directory with fixtures once feature
  endpoints exist to test.
- `frontend/` is an empty directory; no frontend tooling (Vite, package.json) was initialized in Task 0, per the "do not build the frontend features yet" instruction.
- Client deletion cascade behavior (hard delete cascading to schedules
  and tasks) is implemented at the schema level but was flagged in
  `DATABASE_SPEC.md` as worth reconsidering (soft delete/archive) before
  the `DELETE /clients/{id}` endpoint is actually built.

## Instructions for Future Claude Sessions

1. Read `CLAUDE_RULES.md` first — it is the operating manual for this
   project across sessions.
2. Read `PROJECT_SPEC.md`, `DATABASE_SPEC.md`, `API_SPEC.md`, and
   `ARCHITECTURE.md` before writing any code.
3. Implement one feature group at a time (see README → "Future Feature
   Tasks" for the suggested order).
4. Produce your own `HANDOFF_<TASK_NAME>.md` when done, following this
   file's structure.
5. If you think the schema needs to change, stop and use the
   `SCHEMA CHANGE REQUEST` format in `CLAUDE_RULES.md` — do not edit
   `app/models/` directly without that.

## Schema Decisions That Must Not Be Changed Casually

- The four core tables (`clients`, `compliance_schedules`, `tasks`,
  `checklist_items`) and their relationships as described in
  `DATABASE_SPEC.md`.
- The exact enum values for `task_status`
  (`Not Started`/`In Progress`/`Awaiting Client`/`Filed`) and
  `recurrence_type` (`Monthly`/`Quarterly`/`Annual`) — these come
  directly from the assessment.
- The API resource naming (`clients`, `compliance-schedules`, `tasks`,
  `checklists`, `dashboard`) and the `{"items": ..., "total": ...}` list
  response envelope in `API_SPEC.md`.
- The layered architecture (routes → schemas → services → models →
  database) and folder structure in `ARCHITECTURE.md`.

Any of the above may only change via a documented
`SCHEMA CHANGE REQUEST` (schema) or an explicit note in a future
`HANDOFF_*.md` explaining the deviation (API/architecture conventions).
