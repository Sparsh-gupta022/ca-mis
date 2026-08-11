# PROJECT_SPEC.md — HSDG & Associates MIS

This document summarizes the official assessment (`HSDG_SWE_Intern_Assessment.pdf`)
as the source of truth for what this application must do. Anything in this
file that is not directly stated in the assessment is explicitly labelled
**Assumption**.

## Purpose

A CA (Chartered Accountant) firm runs on recurring statutory compliance
work: GST returns, TDS, income tax filings, audits, ROC filings. HSDG &
Associates currently tracks this in Excel. This project is an internal
MIS (Management Information System) MVP that replaces the spreadsheet
with a real, working application: client records, compliance tasks,
due dates, document checklists, and a dashboard.

Reference commercial products in this category: Jamku and ERPCA. This is
an internal, purpose-built alternative — not a clone.

## Required Features

1. **Client master** — add, edit, and list clients.
2. **Compliance tasks per client** — type, period, due date, assignee, status.
3. **Auto-generation of recurring tasks** — monthly, quarterly, annual —
   so nobody re-types the same task every period.
4. **Per-task document checklist** — each document markable received or pending.
5. **Dashboard** — due this week, overdue, awaiting client, workload per assignee.
6. **Task filters** — client, assignee, status, type, date range.
7. **Real, persistent database** — data must survive a restart.
8. **Seed data** — 15+ clients and 60+ tasks so the dashboard has something to show.

## Client Fields

| Field | Source |
|---|---|
| Name | Assessment |
| Entity type | Assessment |
| PAN/GSTIN | Assessment |
| Contact | Assessment |
| Partner in charge | Assessment |

## Task Fields

| Field | Source |
|---|---|
| Type (e.g. GSTR-3B) | Assessment |
| Period (e.g. Jul 2026) | Assessment |
| Due date | Assessment |
| Assignee | Assessment |
| Status | Assessment |
| Client (task belongs to a client) | Assessment (implied — "compliance tasks per client") |

## Status Values (exact, required)

- `Not Started`
- `In Progress`
- `Awaiting Client`
- `Filed`

These are fixed by the assessment. Do not rename, reorder, or add to this
list without a documented schema change request (see `CLAUDE_RULES.md`).

## Recurrence Requirements

Tasks must be auto-generated on a recurring basis rather than entered
manually every period. Supported recurrence types:

- `Monthly`
- `Quarterly`
- `Annual`

The foundation (Task 0) models the recurring **rule** as
`ComplianceSchedule`, from which a later task's generation logic will
produce period-specific `Task` rows. The generation algorithm itself
(how due dates are computed, how periods are labelled, idempotency on
re-runs) is explicitly **out of scope for Task 0** and is left to the
feature task that implements it.

## Checklist Requirements

Each task has a document checklist. Each checklist item can be marked
received or pending. No further checklist behavior (templates per
compliance type, mandatory vs optional documents, etc.) is specified by
the assessment; anything beyond received/pending is an assumption for a
later task to make explicitly, not something Task 0 should pre-decide.

## Dashboard Requirements

The dashboard must answer, at a glance:

- What's due this week
- What's overdue
- What's awaiting the client
- Workload per assignee (how many open tasks each person is carrying)

This is a **read/query** surface over `Task`, not a separate stored
entity. Task 0 does not implement the dashboard; it ensures the schema
(due dates, status, assignee, indexes) supports these queries
efficiently.

## Filtering Requirements

The task list must be filterable by: client, assignee, status, type, and
date range. The schema indexes these columns (see `DATABASE_SPEC.md`) so
filtering is fast even with dozens of clients and hundreds of tasks.

## Persistent Database Requirement

Data must survive an application/server restart. This project uses
PostgreSQL with SQLAlchemy models and Alembic migrations — not an
in-memory store.

## Seed Requirement

The final MVP must ship a seed script producing **15+ clients** and
**60+ tasks**, so the dashboard is meaningful on first run. Seed data
itself is a later task (see `CLAUDE_RULES.md` — Task 0 explicitly does
not implement it).

## Local-Run Requirement

The application must run locally by following the README, on the first
try, without additional undocumented steps.

## Submission Requirements (for context, not built in Task 0)

- GitHub repo with real, incremental commit history (not one squashed commit).
- `README.md`: setup steps, stack choice and why, assumptions, what's next.
- `AI_USAGE.md`: which AI tools were used, where they went wrong, what was
  fixed manually.
- A 5-minute screen recording: demo + a walk-through of the code the
  author is most and least happy with.

## Out of Scope (explicit, per assessment)

- Login / authentication
- Billing
- Government portal integrations
- Visual polish

## Sensible Assumptions (Task 0)

These are implementation decisions made where the assessment is silent.
Each is also called out at its point of use in `DATABASE_SPEC.md`.

1. **Assignee and partner-in-charge are plain strings, not a `User`
   entity.** Authentication/user management is explicitly out of scope,
   so there is no login-backed user table to reference. A later task may
   introduce a lightweight non-auth `TeamMember` lookup table if the firm
   wants consistent name spellings, but that would be a schema change
   requiring its own request.
2. **`entity_type` and `compliance_type` are free-text strings, not a
   fixed database enum.** Only the `status` and `recurrence` values are
   explicitly enumerated by the assessment; entity types (e.g. "Private
   Limited", "LLP", "Proprietorship") and compliance types (e.g.
   "GSTR-3B", "TDS Return", "ROC Filing") vary by firm practice and
   should not be hardcoded into the database schema for an MVP.
3. **`Task` belongs directly to `Client`** (not only reachable via
   `ComplianceSchedule`), so one-off, non-recurring tasks are also
   representable, and so task queries/filters don't require a join
   through the schedule table.
4. **`ComplianceSchedule.compliance_schedule_id` on `Task` is nullable.**
   A task can exist without a recurring rule behind it.
5. **PAN and GSTIN share a single `pan_gstin` string field**, since the
   assessment lists them together ("PAN/GSTIN") as one client attribute
   rather than two.
