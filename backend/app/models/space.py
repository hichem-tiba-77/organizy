"""Spaces and their departments."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._mixins import Timestamps, UUIDPk


class Space(UUIDPk, Timestamps, Base):
    __tablename__ = "spaces"

    name: Mapped[str]
    color: Mapped[str]  # palette token, e.g. "indigo" (validated in schemas)
    icon: Mapped[str]  # emoji or lucide icon name
    position: Mapped[int] = mapped_column(default=0, server_default="0")
    archived_at: Mapped[datetime | None]

    departments: Mapped[list["Department"]] = relationship(
        back_populates="space",
        cascade="all, delete-orphan",
        passive_deletes=True,  # let the DB's ON DELETE CASCADE do the work
        order_by="Department.position",
    )


# Space names are unique ignoring case ("Horizon" vs "horizon").
Index("uq_spaces_lower_name", func.lower(Space.name), unique=True)


class Department(UUIDPk, Timestamps, Base):
    __tablename__ = "departments"
    __table_args__ = (
        # Target of the tasks composite FK (department_id, space_id), which
        # guarantees a task's department belongs to the task's own space.
        UniqueConstraint("id", "space_id"),
    )

    space_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE")
    )
    name: Mapped[str]
    position: Mapped[int] = mapped_column(default=0, server_default="0")

    space: Mapped[Space] = relationship(back_populates="departments")


# Unique per space, ignoring case. Also serves lookups by space_id.
Index(
    "uq_departments_space_id_lower_name",
    Department.space_id,
    func.lower(Department.name),
    unique=True,
)
