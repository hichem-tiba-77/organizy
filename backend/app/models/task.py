"""Tasks, steps, task people links and recurring rules/occurrences."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    Table,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._mixins import Timestamps, UUIDPk, check_in

if TYPE_CHECKING:
    from app.models.person import Person

TASK_PRIORITIES = ("low", "medium", "high")
TASK_STATUSES = ("todo", "in_progress", "waiting", "done")
STEP_WEIGHTS = (1, 2, 3)  # Small, Medium, Large
RECURRENCE_FREQUENCIES = ("daily", "weekly", "monthly")


task_people = Table(
    "task_people",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "person_id",
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # the PK only serves lookups by task_id
    ),
)


class Task(UUIDPk, Timestamps, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        # Composite FK: the department must belong to the same space. On delete,
        # Postgres 15+ nulls only department_id, so the task moves to
        # "No department" in its space and keeps its space_id.
        ForeignKeyConstraint(
            ["department_id", "space_id"],
            ["departments.id", "departments.space_id"],
            ondelete="SET NULL (department_id)",
        ),
        CheckConstraint(check_in("priority", TASK_PRIORITIES), name="priority_valid"),
        CheckConstraint(check_in("status", TASK_STATUSES), name="status_valid"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="progress_range"),
        CheckConstraint(
            "(status = 'done') = (completed_at IS NOT NULL)",
            name="completed_at_iff_done",
        ),
        CheckConstraint(
            "status = 'waiting' OR (waiting_on_person_id IS NULL"
            " AND waiting_on_text IS NULL AND nudge_on IS NULL)",
            name="waiting_fields_only_when_waiting",
        ),
        CheckConstraint(
            "waiting_on_person_id IS NULL OR waiting_on_text IS NULL",
            name="waiting_on_person_or_text",
        ),
        CheckConstraint(
            "NOT is_recurring OR due_date IS NULL", name="recurring_has_no_due_date"
        ),
        Index("ix_tasks_space_id_status", "space_id", "status"),
    )

    space_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE")
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    title: Mapped[str]
    description: Mapped[str | None]
    due_date: Mapped[date | None] = mapped_column(index=True)
    priority: Mapped[str] = mapped_column(default="medium", server_default="medium")
    status: Mapped[str] = mapped_column(default="todo", server_default="todo")
    # Cached step-based progress, written only by services/progress (never by
    # clients). The UI shows 100 when status is done.
    progress: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    completed_at: Mapped[datetime | None]
    waiting_on_person_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), index=True
    )
    waiting_on_text: Mapped[str | None]
    nudge_on: Mapped[date | None] = mapped_column(index=True)
    is_recurring: Mapped[bool] = mapped_column(default=False, server_default=false())
    source_idea_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ideas.id", ondelete="SET NULL"), index=True
    )
    position: Mapped[int] = mapped_column(default=0, server_default="0")

    steps: Mapped[list["Step"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Step.position",
    )
    recurrence_rule: Mapped["RecurrenceRule | None"] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )
    people: Mapped[list["Person"]] = relationship(
        secondary=task_people, passive_deletes=True
    )


class Step(UUIDPk, Timestamps, Base):
    __tablename__ = "steps"
    __table_args__ = (
        CheckConstraint(check_in("weight", STEP_WEIGHTS), name="weight_valid"),
        CheckConstraint("done = (done_at IS NOT NULL)", name="done_at_iff_done"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str]
    weight: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
    done: Mapped[bool] = mapped_column(default=False, server_default=false())
    done_at: Mapped[datetime | None]
    due_date: Mapped[date | None] = mapped_column(index=True)
    position: Mapped[int] = mapped_column(default=0, server_default="0")

    task: Mapped[Task] = relationship(back_populates="steps")


class RecurrenceRule(Base):
    """One per recurring template task (tasks.is_recurring = true)."""

    __tablename__ = "recurrence_rules"
    __table_args__ = (
        CheckConstraint(
            check_in("frequency", RECURRENCE_FREQUENCIES), name="frequency_valid"
        ),
        # ISO weekdays: 1 = Monday ... 7 = Sunday.
        CheckConstraint(
            "weekdays <@ ARRAY[1, 2, 3, 4, 5, 6, 7]::smallint[]",
            name="weekdays_valid",
        ),
        CheckConstraint(
            "(frequency = 'weekly') = (cardinality(weekdays) > 0)",
            name="weekdays_iff_weekly",
        ),
        CheckConstraint(
            "(frequency = 'monthly') = (month_day IS NOT NULL)",
            name="month_day_iff_monthly",
        ),
        CheckConstraint("month_day BETWEEN 1 AND 31", name="month_day_range"),
        CheckConstraint("end_date >= start_date", name="end_after_start"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    frequency: Mapped[str]
    weekdays: Mapped[list[int]] = mapped_column(
        ARRAY(SmallInteger), default=list, server_default="{}"
    )
    # Day 31 in a 30-day month falls on the last day (services/recurrence).
    month_day: Mapped[int | None] = mapped_column(SmallInteger)
    start_date: Mapped[date | None]  # inclusive
    end_date: Mapped[date | None]  # inclusive


class RecurringOccurrence(UUIDPk, Base):
    """Written only when an occurrence is checked or unchecked (decision 12)."""

    __tablename__ = "recurring_occurrences"
    __table_args__ = (
        UniqueConstraint("task_id", "date"),  # also serves lookups by task_id
        CheckConstraint(
            "done = (completed_at IS NOT NULL)", name="completed_at_iff_done"
        ),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE")
    )
    date: Mapped[date]
    done: Mapped[bool] = mapped_column(default=False, server_default=false())
    completed_at: Mapped[datetime | None]
