"""Models and migrations must never drift apart."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine

from app.core.db import Base
from tests.migrations import alembic_config


def test_models_match_migrations(engine: Engine) -> None:
    # Same check as `alembic check`: autogenerate against the migrated DB must
    # find nothing. Fails if a model changes without a new migration.
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_downgrade_then_upgrade_round_trip(engine: Engine) -> None:
    with engine.begin() as connection:
        config = alembic_config(connection)
        command.downgrade(config, "base")
        command.upgrade(config, "head")
