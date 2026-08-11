# HSDG & Associates — Internal MIS

An internal Management Information System for HSDG & Associates,
Chartered Accountants: client records, recurring compliance tasks
(GST, TDS, income tax, ROC, etc.), document checklists, and a dashboard
— replacing the firm's Excel-based tracking.

**⚠️ Status: foundation only, not a working application yet.** This
repository currently contains the shared database schema, project
architecture, and a FastAPI skeleton (Task 0). No feature (client CRUD,
task CRUD, recurring generation, checklists, dashboard, filtering, seed
data) is implemented yet. See "Current Status" and "Future Feature
Tasks" below.

## Stack

**Backend:** Python, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, Pydantic.
**Frontend:** React + Vite (not started yet).

### Why this stack

- **FastAPI** gives automatic OpenAPI/Swagger docs for free, which
  matters for a project multiple sessions/people will pick up — the API
  is always self-documenting at `/docs`.
- **PostgreSQL** is a real, restart-durable relational database with
  native enum support, which fits the fixed status/recurrence value
  lists in the assessment cleanly.
- **SQLAlchemy + Alembic** give typed ORM models plus versioned,
  reviewable schema migrations — appropriate for a schema that's meant
  to be a stable shared baseline across many incremental changes.
- **React + Vite** is a fast, conventional choice for the frontend when
  that work starts; no additional justification needed for an internal
  tool with no unusual UI requirements.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running locally, or reachable via `DATABASE_URL`)
- pip

## PostgreSQL Setup

Create a local database and a user (or reuse your default `postgres`
user). Example, using the default `postgres` superuser:

```bash
# Start your local PostgreSQL server if it isn't already running, then:
psql -U postgres -c "CREATE DATABASE hsdg_mis;"
```

Update `backend/.env` (see below) if your username, password, host, or
port differ from the defaults.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

```bash
cp .env.example .env
```

Then edit `.env` to match your local PostgreSQL setup:

| Variable | Purpose | Example |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/hsdg_mis` |
| `CORS_ORIGINS` | Allowed frontend origin(s) | `http://localhost:5173` |
| `APP_NAME`, `ENVIRONMENT`, `DEBUG` | App metadata | — |

`.env` is git-ignored. Never commit real credentials — `.env.example`
contains only placeholder values.

## Migrations

Run from the `backend/` directory (with your virtualenv active):

```bash
alembic upgrade head
```

This creates all foundation tables (`clients`, `compliance_schedules`,
`tasks`, `checklist_items`) in your PostgreSQL database.

To check the current migration state or roll back:

```bash
alembic current
alembic downgrade base   # drops everything this project created
```

## Running the API

```bash
cd backend
uvicorn app.main:app --reload
```

The API is now running at `http://127.0.0.1:8000`.

- Health check: `http://127.0.0.1:8000/health`
- **Swagger UI (interactive API docs): `http://127.0.0.1:8000/docs`**
- ReDoc: `http://127.0.0.1:8000/redoc`

## Current Task 0 Status

Task 0 (foundation) is complete:

- ✅ Database schema designed and documented (`DATABASE_SPEC.md`)
- ✅ SQLAlchemy models for `Client`, `ComplianceSchedule`, `Task`,
  `ChecklistItem` (`backend/app/models/`)
- ✅ Alembic configured and an initial migration created, tested against
  a real local PostgreSQL instance (created tables, round-tripped
  downgrade/upgrade, verified zero schema drift)
- ✅ FastAPI application skeleton — starts, serves `/health` and `/docs`
- ✅ Planned API contract documented (`API_SPEC.md`)
- ✅ Architecture and folder structure documented (`ARCHITECTURE.md`)
- ✅ Rules for future Claude sessions documented (`CLAUDE_RULES.md`)
- ❌ No feature endpoints implemented yet (see below)
- ❌ No frontend yet
- ❌ No seed data yet

See `HANDOFF_TASK_0.md` for the full detail of what was built and
verified.

## Future Feature Tasks

Not yet built, planned as separate follow-up tasks:

1. Client CRUD (`/clients` — add, edit, list)
2. Compliance schedule CRUD + recurring task auto-generation
3. Task CRUD + filtering (client, assignee, status, type, date range)
4. Checklist endpoints (mark documents received/pending)
5. Dashboard endpoints (due this week, overdue, awaiting client,
   workload per assignee)
6. Seed script (15+ clients, 60+ tasks)
7. Frontend (React + Vite) for all of the above

Each future task must read `CLAUDE_RULES.md` before starting.

## Assumptions Made

See `PROJECT_SPEC.md` → "Sensible Assumptions" and `DATABASE_SPEC.md` →
"Design Assumptions" for the full, detailed list. In short:

- No `User`/auth table — assignee and partner-in-charge are plain
  strings, since login/authentication is explicitly out of scope.
- `entity_type` and `compliance_type` are free-text strings, not fixed
  database enums (only `status` and `recurrence` are fixed enums, per
  the assessment).
- `Task` belongs directly to `Client` (not only reachable through a
  `ComplianceSchedule`), so one-off tasks are also representable.

## AI Usage

This foundation (Task 0) was built with Claude. See `AI_USAGE.md` (to be
completed alongside the full submission, per the assessment's
requirements) for the detailed account of where AI output needed
correction.
