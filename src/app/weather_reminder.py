from __future__ import annotations

from collections.abc import Callable

from core.models.trace import TickTrace

WEATHER_REMINDER_AFTER_SECONDS = 2 * 60 * 60


class WeatherReminder:
    def __init__(self, notify: Callable[[float], None]) -> None:
        self._notify = notify
        self._source_fingerprint: str | None = None
        self._baseline = 0.0
        self._notified = False

    def on_tick(self, trace: TickTrace) -> None:
        """Check weather freshness after a committed tick.

        Raises:
            Exception: If the injected notification function fails.
        """
        weather = trace.context.weather
        if weather is None:
            return
        if weather.source_fingerprint != self._source_fingerprint:
            self._source_fingerprint = weather.source_fingerprint
            self._baseline = trace.ts
            self._notified = False
        if weather.last_success_at is not None and weather.last_success_at != self._baseline:
            self._baseline = weather.last_success_at
            self._notified = False
        elapsed = trace.ts - self._baseline
        if not self._notified and elapsed >= WEATHER_REMINDER_AFTER_SECONDS:
            self._notified = True
            self._notify(elapsed)
