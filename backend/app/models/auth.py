"""Server-side login sessions."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import CreatedAt, UUIDPk


class AuthSession(UUIDPk, CreatedAt, Base):
    """The cookie holds a random token; only its SHA-256 hex digest is stored,
    so a database leak doesn't leak live sessions. Logout deletes the row.
    """

    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]
    user_agent: Mapped[str | None]
