"""All SQLAlchemy models. Importing this package registers every table on
Base.metadata, which is what Alembic autogenerate compares against the DB.
"""

from app.models.auth import AuthSession
from app.models.idea import Idea
from app.models.person import (
    ContactLog,
    Person,
    PersonContact,
    PersonCustomField,
    PersonFamily,
    PersonTag,
    person_spaces,
)
from app.models.space import Department, Space
from app.models.task import (
    RecurrenceRule,
    RecurringOccurrence,
    Step,
    Task,
    task_people,
)
from app.models.today import Event, Pin, event_people

__all__ = [
    "AuthSession",
    "ContactLog",
    "Department",
    "Event",
    "Idea",
    "Person",
    "PersonContact",
    "PersonCustomField",
    "PersonFamily",
    "PersonTag",
    "Pin",
    "RecurrenceRule",
    "RecurringOccurrence",
    "Space",
    "Step",
    "Task",
    "event_people",
    "person_spaces",
    "task_people",
]
