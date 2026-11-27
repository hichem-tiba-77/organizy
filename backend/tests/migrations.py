"""Helpers to run Alembic from tests against a given connection."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import Connection

BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic_config(connection: Connection) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["connection"] = connection  # read by alembic/env.py
    return config
