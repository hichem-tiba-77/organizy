"""The single source of "now" and "today".

Every date rule (today, overdue, nudges, birthdays, recurring occurrences) must use
a Clock, never datetime.now() / date.today() directly (ruff's DTZ rules enforce it).
"today" is computed in the configured time zone (default Africa/Algiers), not UTC.
Tests inject a fixed instant through ``utcnow`` to make date boundaries deterministic.
"""

from collections.abc import Callable
from datetime import UTC, date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def _system_utcnow() -> datetime:
    return datetime.now(UTC)


class Clock:
    def __init__(
        self,
        tz: ZoneInfo,
        utcnow: Callable[[], datetime] = _system_utcnow,
    ) -> None:
        self.tz = tz
        self._utcnow = utcnow

    def now_utc(self) -> datetime:
        """Current instant, timezone-aware, in UTC (for stored timestamps)."""
        instant = self._utcnow()
        if instant.tzinfo is None:
            raise ValueError("Clock source must return a timezone-aware datetime")
        return instant.astimezone(UTC)

    def now(self) -> datetime:
        """Current instant in the local time zone."""
        return self.now_utc().astimezone(self.tz)

    def today(self) -> date:
        """Today's date in the local time zone."""
        return self.now().date()


@lru_cache
def get_clock() -> Clock:
    return Clock(ZoneInfo(get_settings().tz))
