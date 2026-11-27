"""Column mixins shared by most tables (PROPOSAL §2 conventions)."""

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPk:
    # Python-side default so the id exists before flush; server default so raw
    # SQL inserts (psql, future data fixes) work too. gen_random_uuid() is built in
    # since Postgres 13, no extension needed.
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        sort_order=-10,
    )


class CreatedAt:
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), sort_order=10
    )


class Timestamps(CreatedAt):
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), sort_order=11
    )


def check_in(column: str, values: tuple) -> str:
    """SQL for a CHECK such as: status IN ('todo', 'done')."""
    return f"{column} IN ({', '.join(repr(v) for v in values)})"
