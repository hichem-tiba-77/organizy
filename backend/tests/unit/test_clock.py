from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.core.clock import Clock
from app.core.config import Settings

ALGIERS = ZoneInfo("Africa/Algiers")  # UTC+1 all year, no DST


def clock_at(instant: datetime) -> Clock:
    return Clock(ALGIERS, utcnow=lambda: instant)


def test_today_is_already_tomorrow_in_algiers_at_2330_utc():
    clock = clock_at(datetime(2026, 11, 27, 23, 30, tzinfo=UTC))
    assert clock.today() == date(2026, 11, 28)


@pytest.mark.parametrize(
    ("utc_time", "expected"),
    [
        (datetime(2026, 11, 27, 22, 59, 59, tzinfo=UTC), date(2026, 11, 27)),
        (datetime(2026, 11, 27, 23, 0, 0, tzinfo=UTC), date(2026, 11, 28)),
    ],
)
def test_today_flips_at_local_midnight(utc_time, expected):
    assert clock_at(utc_time).today() == expected


def test_today_across_year_end():
    clock = clock_at(datetime(2026, 12, 31, 23, 15, tzinfo=UTC))
    assert clock.today() == date(2027, 1, 1)


def test_now_is_local_and_now_utc_is_utc():
    instant = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    clock = clock_at(instant)
    assert clock.now().utcoffset() == timedelta(hours=1)
    assert clock.now().hour == 11
    assert clock.now_utc() == instant
    assert clock.now_utc().tzinfo is UTC


def test_naive_clock_source_is_rejected():
    clock = clock_at(datetime(2026, 11, 27, 10, 0))  # noqa: DTZ001 (deliberately naive)
    with pytest.raises(ValueError, match="timezone-aware"):
        clock.today()


def test_default_timezone_is_africa_algiers(monkeypatch):
    monkeypatch.delenv("TZ", raising=False)
    assert Settings(_env_file=None).tz == "Africa/Algiers"


def test_unknown_timezone_is_rejected(monkeypatch):
    monkeypatch.setenv("TZ", "Mars/Olympus_Mons")
    with pytest.raises(ValidationError, match="Unknown time zone"):
        Settings(_env_file=None)
