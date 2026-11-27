"""Ideas inbox (global, or attached to a space)."""

import uuid

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import Timestamps, UUIDPk, check_in

IDEA_STATUSES = ("open", "archived", "converted")


class Idea(UUIDPk, Timestamps, Base):
    __tablename__ = "ideas"
    __table_args__ = (
        CheckConstraint(check_in("status", IDEA_STATUSES), name="status_valid"),
    )

    text: Mapped[str]
    # The spec deletes a space's ideas with the space.
    space_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(default="open", server_default="open")
    # ideas <-> tasks reference each other (decision 26). use_alter breaks the
    # cycle: this FK is added after both tables exist.
    converted_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL", use_alter=True), index=True
    )
