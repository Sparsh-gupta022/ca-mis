"""
Shared enum types used by ORM models and Pydantic schemas.

These map 1:1 to the values mandated by the official assessment. Do not
rename or add values without recording a SCHEMA CHANGE REQUEST (see
CLAUDE_RULES.md).
"""
import enum


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    AWAITING_CLIENT = "Awaiting Client"
    FILED = "Filed"


class RecurrenceType(str, enum.Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUAL = "Annual"
