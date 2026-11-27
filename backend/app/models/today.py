"""Today planner: pins and timed events."""

import uuid
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._mixins import CreatedAt, Timestamps, UUIDPk

if TYPE_CHECKING:
    from app.models.person import Person


class Pin(UUIDPk, CreatedAt, Base):
    """A task or a single step pinned to a day.

    There is no "done" column: a pin is done when its task or step is done
    (decision 11), so the two can never drift apart.
    """

    __tablename__ = "pins"
    __table_args__ = (
        CheckConstraint("num_nonnulls(task_id, step_id) = 1", name="one_target"),
        Index("ix_pins_date_position", "date", "position"),
    )

    date: Mapped[date]
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    step_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("steps.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(default=0, server_default="0")


# The same task (or step) can be pinned at most once per day.
Index(
    "uq_pins_date_task_id",
    Pin.date,
    Pin.task_id,
    unique=True,
    postgresql_where=Pin.task_id.is_not(None),
)
Index(
    "uq_pins_date_step_id",
    Pin.date,
    Pin.step_id,
    unique=True,
    postgresql_where=Pin.step_id.is_not(None),
)


event_people = Table(
    "event_people",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "person_id",
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Event(UUIDPk, Timestamps, Base):
    """One-off timed event (no recurring events in v1)."""

    __tablename__ = "events"
    __table_args__ = (Index("ix_events_date_start_time", "date", "start_time"),)

    title: Mapped[str]
    date: Mapped[date]
    start_time: Mapped[time]
    end_time: Mapped[time | None]  # decision 22
    location: Mapped[str | None]
    notes: Mapped[str | None]
    # Deleting a space keeps its events and only clears the link (spec).
    space_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("spaces.id", ondelete="SET NULL"), index=True
    )

    people: Mapped[list["Person"]] = relationship(
        secondary=event_people, passive_deletes=True
    )
