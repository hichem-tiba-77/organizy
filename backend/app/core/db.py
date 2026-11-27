"""Database engine, session factory and the declarative Base for models."""

from functools import lru_cache

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

# Deterministic constraint names, so Alembic migrations are stable and reviewable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def make_engine(url: str, connect_timeout: int = 5) -> Engine:
    # pool_pre_ping: transparently replaces connections dropped by a DB restart.
    # connect_timeout (seconds, libpq minimum 2): without it, a stopped database
    # makes requests (and /health) hang instead of failing fast.
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": connect_timeout},
    )


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return make_engine(settings.database_url, settings.db_connect_timeout)


@lru_cache
def get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
