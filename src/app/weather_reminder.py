from __future__ import annotations

from collections.abc import Callable

from core.models.trace import TickTrace

WEATHER_REMINDER_AFTER_HOURS = 2
WEATHER_REMINDER_AFTER_SECONDS = WEATHER_REMINDER_AFTER_HOURS * 60 * 60
WEATHER_REMINDER_SUSPENSION_GAP_SECONDS = 60.0


class WeatherReminder:
    def __init__(self, notify: Callable[[int], None]) -> None:
        self._notify = notify
        self._weather_key: tuple[str, float | None] | None = None
        self._last_tick_ts = 0.0
        self._monitored_elapsed = 0.0
        self._notified = False

    def on_tick(self, trace: TickTrace) -> None:
        """Check weather freshness after a committed tick.

        Tick gaps longer than ``WEATHER_REMINDER_SUSPENSION_GAP_SECONDS`` mean the
        scheduler was not running; they are not counted as update failure.

        Raises:
            Exception: If the injected notification function fails.
        """
        weather = trace.schedule.context.weather
        if weather is None:
            return

        key = (weather.source_fingerprint, weather.last_success_at)
        if key != self._weather_key:
            self._weather_key = key
            self._monitored_elapsed = 0.0
            self._notified = False
        else:
            gap = trace.ts - self._last_tick_ts
            if 0.0 < gap <= WEATHER_REMINDER_SUSPENSION_GAP_SECONDS:
                self._monitored_elapsed += gap

        self._last_tick_ts = trace.ts

        if not self._notified and self._monitored_elapsed >= WEATHER_REMINDER_AFTER_SECONDS:
            self._notified = True
            self._notify(WEATHER_REMINDER_AFTER_HOURS)
