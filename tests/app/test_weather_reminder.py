from __future__ import annotations

from app.weather_reminder import WeatherReminder
from core.models.context import Context, WeatherData
from core.models.scene import Scenes
from core.models.scheduling import (
    Action,
    ActionResult,
    Decision,
    DecisionMode,
    DisturbanceEvaluation,
    ScheduleResult,
    TimingEvaluation,
)
from core.models.selection import Selection
from core.models.trace import TickTrace


def schedule_at(last_success_at: float | None, source: str, *, paused: bool = False) -> ScheduleResult:
    return ScheduleResult(
        context=Context(weather=WeatherData(last_success_at=last_success_at, source_fingerprint=source)),
        selection=Selection(probabilities={}, salience={}, reason="no_safe_scenes"),
        mode=DecisionMode.PAUSE if paused else DecisionMode.NORMAL,
        decision=Decision(
            action=Action.NOOP,
            target=Scenes(),
            timing=TimingEvaluation(
                active_scenes=Scenes(),
                distance=None,
                reference_distance=0.0,
                interval=None,
                elapsed=0.0,
                startup_remaining=0.0,
            ),
            disturbance=DisturbanceEvaluation(),
        ),
        action=ActionResult(),
    )


def feed(reminder: WeatherReminder, scheduled: ScheduleResult, start: int, end: int, *, paused: bool = False) -> None:
    for ts in range(start, end + 1):
        reminder.on_tick(TickTrace(tick_id=1, ts=float(ts), paused=paused, pause_until=0.0, schedule=scheduled))


def test_weather_reminder_notifies_once_after_two_hours_without_success() -> None:
    notifications: list[int] = []
    reminder = WeatherReminder(notifications.append)
    scheduled = schedule_at(1000.0, "source-a")

    feed(reminder, scheduled, 1000, 8199)
    assert notifications == []

    feed(reminder, scheduled, 8200, 16000)
    assert notifications == [2]


def test_weather_success_silently_starts_a_new_reminder_period() -> None:
    notifications: list[int] = []
    reminder = WeatherReminder(notifications.append)
    feed(reminder, schedule_at(1000.0, "source-a"), 1000, 8200)
    assert notifications == [2]

    succeeded = schedule_at(9000.0, "source-a")
    feed(reminder, succeeded, 9000, 16199)
    assert notifications == [2]

    feed(reminder, succeeded, 16200, 16200)
    assert notifications == [2, 2]


def test_observed_source_changes_restart_the_reminder_even_when_returning_to_the_first_source() -> None:
    notifications: list[int] = []
    reminder = WeatherReminder(notifications.append)

    feed(reminder, schedule_at(None, "source-a"), 1000, 7999)
    feed(reminder, schedule_at(None, "source-b"), 8000, 8000)
    feed(reminder, schedule_at(None, "source-a"), 9000, 16200)
    assert notifications == [2]

    feed(reminder, schedule_at(None, "source-b"), 18000, 25200)
    assert notifications == [2, 2]


def test_weather_that_never_succeeds_is_timed_from_the_first_tick_even_while_paused() -> None:
    notifications: list[int] = []
    reminder = WeatherReminder(notifications.append)
    paused = schedule_at(None, "source-a", paused=True)

    feed(reminder, paused, 10000, 17199, paused=True)
    assert notifications == []

    feed(reminder, paused, 17200, 17200, paused=True)
    assert notifications == [2]


def test_system_sleep_gap_is_ignored_while_normal_ticks_still_count() -> None:
    notifications: list[int] = []
    reminder = WeatherReminder(notifications.append)
    scheduled = schedule_at(1000.0, "source-a")

    feed(reminder, scheduled, 1000, 2000)
    reminder.on_tick(TickTrace(tick_id=1, ts=50000.0, paused=False, pause_until=0.0, schedule=scheduled))
    assert notifications == []

    feed(reminder, scheduled, 50001, 56200)
    assert notifications == [2]
