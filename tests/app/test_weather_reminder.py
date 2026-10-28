from __future__ import annotations

from app.weather_reminder import WeatherReminder
from core.models.context import Context, WeatherData
from core.models.scene import Scenes
from core.models.scheduling import Action, ActionResult, Decision, DecisionMode, DisturbanceEvaluation, ScheduleResult, TimingEvaluation
from core.models.selection import Selection
from core.models.trace import TickTrace


def trace_at(ts: float, *, last_success_at: float | None = 1000.0, source: str = "source-a", paused: bool = False) -> TickTrace:
    schedule = ScheduleResult(
        context=Context(weather=WeatherData(last_success_at=last_success_at, source_fingerprint=source)),
        selection=Selection(probabilities={}, salience={}, reason="no_safe_scenes"),
        mode=DecisionMode.PAUSE if paused else DecisionMode.NORMAL,
        decision=Decision(
            action=Action.NOOP,
            target=Scenes(),
            timing=TimingEvaluation(active_scenes=Scenes(), distance=None, reference_distance=0.0, interval=None, elapsed=0.0, startup_remaining=0.0),
            disturbance=DisturbanceEvaluation(),
        ),
        action=ActionResult(),
    )
    return TickTrace(tick_id=1, ts=ts, paused=paused, pause_until=0.0, schedule=schedule)


def test_weather_reminder_notifies_once_after_two_hours_without_success() -> None:
    notifications: list[float] = []
    reminder = WeatherReminder(notifications.append)

    reminder.on_tick(trace_at(1000.0))
    reminder.on_tick(trace_at(8199.0))
    assert notifications == []

    reminder.on_tick(trace_at(8200.0))
    reminder.on_tick(trace_at(16000.0))
    assert notifications == [7200.0]


def test_weather_success_silently_starts_a_new_reminder_period() -> None:
    notifications: list[float] = []
    reminder = WeatherReminder(notifications.append)
    reminder.on_tick(trace_at(1000.0))
    reminder.on_tick(trace_at(8200.0))

    reminder.on_tick(trace_at(9000.0, last_success_at=9000.0))
    reminder.on_tick(trace_at(16199.0, last_success_at=9000.0))
    assert notifications == [7200.0]

    reminder.on_tick(trace_at(16200.0, last_success_at=9000.0))
    assert notifications == [7200.0, 7200.0]


def test_observed_source_changes_restart_the_reminder_even_when_returning_to_the_first_source() -> None:
    notifications: list[float] = []
    reminder = WeatherReminder(notifications.append)

    reminder.on_tick(trace_at(1000.0, last_success_at=None))
    reminder.on_tick(trace_at(8000.0, last_success_at=None, source="source-b"))
    reminder.on_tick(trace_at(9000.0, last_success_at=None))
    reminder.on_tick(trace_at(16199.0, last_success_at=None))
    assert notifications == []

    reminder.on_tick(trace_at(16200.0, last_success_at=None))
    reminder.on_tick(trace_at(18000.0, last_success_at=None, source="source-b"))
    assert notifications == [7200.0]
    reminder.on_tick(trace_at(25200.0, last_success_at=None, source="source-b"))
    assert notifications == [7200.0, 7200.0]


def test_weather_that_never_succeeds_is_timed_from_the_first_tick_even_while_paused() -> None:
    notifications: list[float] = []
    reminder = WeatherReminder(notifications.append)

    reminder.on_tick(trace_at(10000.0, last_success_at=None, paused=True))
    reminder.on_tick(trace_at(17199.0, last_success_at=None, paused=True))
    assert notifications == []

    reminder.on_tick(trace_at(17200.0, last_success_at=None, paused=True))
    assert notifications == [7200.0]
