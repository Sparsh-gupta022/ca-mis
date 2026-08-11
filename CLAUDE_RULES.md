# CLAUDE_RULES.md — Rules for Future Claude Sessions

This project is built incrementally across multiple, independent Claude
sessions. Task 0 built the shared foundation. Every session that works on
this project after Task 0 must follow these rules.

1. **Read `PROJECT_SPEC.md` before coding.** It is the source of truth
   for what the application must do, sourced from the official
   assessment.
2. **Read `DATABASE_SPEC.md` before coding.** It is the baseline schema.
3. **Read `API_SPEC.md` before coding.** It is the planned API contract.
4. **Read `ARCHITECTURE.md` before coding.** It defines the folder
   structure and the responsibility of each layer.
5. **Follow existing naming conventions.** `clients`, `tasks`,
   `compliance-schedules`, `checklists` — always these terms, never
   synonyms (`customers`, `jobs`, `rules`, etc.).
6. **Do not invent different API endpoints.** Implement what
   `API_SPEC.md` describes. If a genuinely new endpoint is needed that
   isn't in the spec, add it to `API_SPEC.md` in the same change and
   explain why in your `HANDOFF_*.md`.
7. **Do not casually modify database models.** The schema in
   `DATABASE_SPEC.md` / `app/models/` is the shared baseline. See
   "Database Baseline Rule" below.
8. **Do not modify unrelated feature files.** Touch only what your task
   requires.
9. **Follow the existing architecture.** Routes → Schemas → Services →
   Models → Database, as described in `ARCHITECTURE.md`. Don't add new
   layers or bypass existing ones.
10. **Keep route handlers thin.** No SQLAlchemy queries or business
    rules directly in `app/api/routes/*.py` — call a service function.
11. **Put business logic in services.** `app/services/*.py`.
12. **Use Pydantic for API validation.** Request/response shapes go in
    `app/schemas/*.py`.
13. **Use SQLAlchemy for database access.** No raw SQL unless a service
    has a specific, documented performance reason to use it.
14. **If a schema change is needed, report it instead of silently
    changing it.** Use the exact format below.
15. **Every completed feature must produce a `HANDOFF_<TASK_NAME>.md`**
    file at the repo root, following the shape of `HANDOFF_TASK_0.md`.
16. **Do not implement login, billing, government integrations, or
    visual polish** unless explicitly requested in a later task — these
    are out of scope per the official assessment.

## Database Baseline Rule

The schema defined in Task 0 (`DATABASE_SPEC.md`, `app/models/`) is the
**shared baseline** for every future task. If your task appears to
require a schema change (a new column, a new table, a changed
relationship, a new enum value, etc.), do **not** change the models
directly. Instead, stop and report using exactly this format:

```
SCHEMA CHANGE REQUEST

Reason:
Required field/change:
Why the existing schema is insufficient:
Affected tables:
Migration required:
Impact on existing code:
```

Only proceed with the schema change after this has been reviewed and
approved (by the person running the session, or per their explicit
instruction to proceed).

## Handoff File Requirements

Every completed feature task produces `HANDOFF_<TASK_NAME>.md` at the
repo root (e.g. `HANDOFF_TASK_1_CLIENT_CRUD.md`), following the same
section structure as `HANDOFF_TASK_0.md`:

```
## Task
## Status
## Files created
## Files modified
## Database tables
## Relationships
## API conventions
## Architecture conventions
## Commands required to run
## Verification performed
## Assumptions
## Known limitations
## Instructions for future Claude sessions
## Schema decisions that must not be changed casually
```

"Verification performed" must describe what was **actually run and
observed** (e.g. "ran `pytest`, 12 passed" or "started the server and
curled `GET /clients`, got a 200 with 15 seeded rows") — never claim
something was tested if it wasn't actually executed.
