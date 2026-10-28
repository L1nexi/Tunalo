from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, tzinfo

import pytest

from configurations.runtime_models import PoliciesConfig, SchedulerConfig, WeatherPolicyConfig
from core.sensors.sun_times import SunTimesSensor


@pytest.fixture
def local_clock(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], datetime]:
    class LocalDateTime(datetime):
        @classmethod
        def fromtimestamp(cls, timestamp: float, tz: tzinfo | None = None) -> LocalDateTime:
            return current[0]

        def astimezone(self, tz: tzinfo | None = None) -> datetime:
            return self if tz is None else super().astimezone(tz)

    current = [LocalDateTime.fromisoformat("2026-10-29T12:00:00+08:00")]

    def set_time(value: str) -> datetime:
        current[0] = LocalDateTime.fromisoformat(value)
        return current[0]

    monkeypatch.setattr("core.sensors.sun_times.datetime", LocalDateTime)
    return set_time


def test_first_sun_times_are_available_offline_without_a_weather_key(local_clock: Callable[[str], datetime], monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Sun times must be available without network access")

    monkeypatch.setattr("requests.sessions.Session.request", reject_network)
    now = local_clock("2026-10-29T12:00:00+08:00")
    config = SchedulerConfig(policies=PoliciesConfig(weather=WeatherPolicyConfig(lat=31.23, lon=121.47)))
    sensor = SunTimesSensor.create(config)
    assert sensor is not None
    result = sensor.collect()
    assert result is not None
    rise = datetime.fromtimestamp(result.sunrise, now.tzinfo)
    setting = datetime.fromtimestamp(result.sunset, now.tzinfo)
    assert rise.date() == setting.date() == now.date()
    assert 4 <= rise.hour < 8
    assert 16 <= setting.hour < 20
    assert result.sunrise < now.timestamp() < result.sunset


def test_sun_times_refresh_at_local_midnight_and_follow_clock_rollback(local_clock: Callable[[str], datetime]) -> None:
    sensor = SunTimesSensor(31.23, 121.47)
    first_day = local_clock("2026-10-29T00:01:00+08:00")
    first = sensor.collect()
    local_clock("2026-10-29T23:59:00+08:00")
    assert sensor.collect() == first
    next_day = local_clock("2026-10-30T00:01:00+08:00")
    following = sensor.collect()
    assert first is not None and following is not None
    assert datetime.fromtimestamp(following.sunrise, next_day.tzinfo).date() == next_day.date()
    assert following != first
    local_clock(first_day.isoformat())
    assert sensor.collect() == first


def test_same_local_date_with_a_new_timezone_selects_new_calendar_events(local_clock: Callable[[str], datetime]) -> None:
    sensor = SunTimesSensor(0, 179)
    east = local_clock("2026-01-01T12:00:00+14:00")
    eastern = sensor.collect()
    west = local_clock("2026-01-01T12:00:00-12:00")
    western = sensor.collect()
    assert eastern is not None and western is not None
    assert datetime.fromtimestamp(eastern.sunrise, east.tzinfo).date() == east.date()
    assert datetime.fromtimestamp(western.sunrise, west.tzinfo).date() == west.date()
    assert western.sunrise - eastern.sunrise > timedelta(hours=23).total_seconds()


@pytest.mark.parametrize("date", ["2026-06-21", "2026-12-21"])
def test_polar_dates_have_no_complete_sun_times_and_recover_on_a_normal_date(local_clock: Callable[[str], datetime], date: str) -> None:
    sensor = SunTimesSensor(78.2232, 15.6267)
    local_clock("2026-03-21T12:00:00+01:00")
    assert sensor.collect() is not None
    local_clock(f"{date}T12:00:00+01:00")
    assert sensor.collect() is None
    local_clock("2026-09-21T12:00:00+01:00")
    assert sensor.collect() is not None


def test_a_replacement_location_cannot_reuse_previous_sun_times(local_clock: Callable[[str], datetime]) -> None:
    local_clock("2026-10-29T12:00:00+08:00")
    old = SunTimesSensor(31.23, 121.47)
    previous = old.collect()
    replacement = SunTimesSensor(31.23, 91.47)
    replacement.import_state(old.export_state())
    current = replacement.collect()
    assert previous is not None and current is not None
    assert timedelta(hours=1).total_seconds() < current.sunrise - previous.sunrise < timedelta(hours=3).total_seconds()


@pytest.mark.parametrize("latitude,longitude", [(None, 121.47), (31.23, None), (None, None)])
def test_sun_times_require_both_coordinates(latitude: float | None, longitude: float | None) -> None:
    config = SchedulerConfig(policies=PoliciesConfig(weather=WeatherPolicyConfig(lat=latitude, lon=longitude)))
    assert SunTimesSensor.create(config) is None
