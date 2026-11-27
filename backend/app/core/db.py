"""Database engine, session factory and the declarative Base for models."""

import uuid
from datetime import datetime
from functools import lru_cache

from sqlalchemy import DateTime, Engine, MetaData, Text, Uuid, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

# Deterministic constraint names, so Alembic migrations are stable and reviewable.
# column_0_N_name joins every column (e.g. uq_departments_id_space_id).
# Expression and partial indexes are named explicitly in the models.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Python type -> column type defaults. Every datetime is timestamptz (UTC),
    # so a naive timestamp column can't slip in; plain str is Postgres text.
    type_annotation_map = {
        datetime: DateTime(timezone=True),
        str: Text(),
        uuid.UUID: Uuid(),
    }


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
