# ARCHITECTURE.md — HSDG & Associates MIS

## Request Flow

```
HTTP Request
      ↓
FastAPI Route            (app/api/routes/*.py)
      ↓
Pydantic Schema          (app/schemas/*.py)
      ↓
Service / Business Logic (app/services/*.py)
      ↓
SQLAlchemy ORM            (app/models/*.py)
      ↓
PostgreSQL
      ↓
Response
```

Every layer has one job. A future task adding a feature should be able to
touch exactly the layers it needs and nothing else.

### Routes (`app/api/routes/`)

Thin. A route function:
1. Declares the path, method, and Pydantic request/response models.
2. Depends on `get_db` (from `app/db/session.py`) for a database session.
3. Calls into a service function and returns its result.

Routes must **not** contain SQLAlchemy queries or business rules directly
— see `CLAUDE_RULES.md` rule 10 ("keep route handlers thin").

### Schemas (`app/schemas/`)

Pydantic models used for request validation and response serialization.
These are the API's public shape and should mirror `API_SPEC.md`, not
leak internal model details the API contract doesn't promise (e.g. don't
expose a raw SQLAlchemy relationship object; return a shaped nested
object instead).

Convention: `<Resource>Create`, `<Resource>Update`, `<Resource>Read` (or
`<Resource>Out`) per resource, e.g. `ClientCreate`, `ClientUpdate`,
`ClientRead`.

### Services (`app/services/`)

Business logic lives here: recurring-task generation rules, dashboard
aggregation queries, checklist validation, etc. Services take a `Session`
and plain arguments in, and return plain Python objects (typically ORM
model instances) out. Services are what routes call — this is the layer
future feature tasks will spend most of their time in.

### Models (`app/models/`)

SQLAlchemy ORM models — the four tables described in `DATABASE_SPEC.md`
(`Client`, `ComplianceSchedule`, `Task`, `ChecklistItem`) plus the shared
`app/models/enums.py` (`TaskStatus`, `RecurrenceType`). This is the
**baseline schema** — see the "Database Baseline Rule" in
`CLAUDE_RULES.md` before changing anything here.

### Database Layer (`app/db/`)

- `base_class.py` — the shared `Base` all models inherit from.
- `session.py` — the SQLAlchemy `engine`, `SessionLocal`, and the
  `get_db()` FastAPI dependency that yields a request-scoped session.

### Configuration (`app/core/`)

- `config.py` — a single `Settings` (Pydantic Settings) object, populated
  from environment variables / `.env`. All configuration (DB URL, CORS
  origins, app metadata) is read from here — nowhere else in the app
  should read `os.environ` directly.

## Folder Structure

```
backend/
    app/
        main.py              # FastAPI app instance, health check, router registration
        core/
            config.py        # Settings (env-driven configuration)
        db/
            base_class.py    # Declarative Base
            session.py       # Engine, SessionLocal, get_db dependency
        models/
            enums.py         # TaskStatus, RecurrenceType
            client.py
            compliance_schedule.py
            task.py
            checklist_item.py
        schemas/              # Pydantic request/response models (empty in Task 0)
        services/             # Business logic (empty in Task 0)
        api/
            routes/           # FastAPI routers, one module per resource group (empty in Task 0)
    alembic/
        env.py                # Wired to app.core.config + app.models metadata
        versions/              # Migration scripts
    requirements.txt
    .env.example
    alembic.ini

frontend/                      # Not started — Task 0 is backend-only per instructions
```

This matches the suggested structure in the assignment exactly. No
structural deviation was made in Task 0.

## Terminology Consistency

The codebase, `DATABASE_SPEC.md`, and `API_SPEC.md` consistently use:

- **`clients`** (never `customers`)
- **`tasks`** (never `jobs`/`items`)
- **`compliance-schedules`** in URLs / `ComplianceSchedule` in code (never `rules`, `recurrences`)
- **`checklists`** in URLs / `ChecklistItem` in code

Future tasks must reuse these exact terms — see `CLAUDE_RULES.md`.
