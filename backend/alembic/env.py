"""Alembic environment: wires migrations to the app's settings and models.

- The DB URL comes from app settings (DATABASE_URL), never from alembic.ini.
- Tests can pass an open connection via ``config.attributes["connection"]``
  to migrate the test database (see tests/conftest.py).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import get_settings
from app.core.db import Base, make_engine

config = context.config

# Configure logging from alembic.ini only for the CLI; when tests pass a
# connection, leave pytest's logging setup alone.
if config.config_file_name is not None and "connection" not in config.attributes:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _configure(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        # Detect column type changes (e.g. text -> smallint) in autogenerate.
        compare_type=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (`alembic upgrade head --sql`)."""
    _configure(
        url=get_settings().database_url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_with(connection: Connection) -> None:
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        _run_with(connection)
        return

    engine = make_engine(get_settings().database_url)
    try:
        with engine.connect() as connection:
            _run_with(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
