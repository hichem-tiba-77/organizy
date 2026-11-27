"""FastAPI dependencies shared by routers (overridable in tests)."""

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.core.db import get_sessionmaker


def get_db() -> Iterator[Session]:
    with get_sessionmaker()() as session:
        yield session
