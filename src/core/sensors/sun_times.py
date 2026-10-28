from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta

from astral import Observer
from astral.sun import sunrise, sunset

from configurations.runtime_models import SchedulerConfig
from core.models.context import SunTimesData
from core.sensors.base import Sensor

logger = logging.getLogger("Tunalo.Sensor")


class SunTimesSensor(Sensor):
    key = "sun_times"

    def __init__(self, latitude: float, longitude: float) -> None:
        self._observer = Observer(latitude=latitude, longitude=longitude)
        self._cache_key: tuple[date, timedelta | None] | None = None
        self._cached: SunTimesData | None = None

    def collect(self) -> SunTimesData | None:
        """Calculate local sun times, or return None when either event is absent."""
        now = datetime.fromtimestamp(time.time()).astimezone()
        cache_key = (now.date(), now.utcoffset())
        if cache_key == self._cache_key:
            return self._cached

        try:
            calculated = SunTimesData(
                sunrise=int(sunrise(self._observer, date=now.date(), tzinfo=now.tzinfo).timestamp()),
                sunset=int(sunset(self._observer, date=now.date(), tzinfo=now.tzinfo).timestamp()),
            )
        except ValueError:
            calculated = None
            logger.debug("Sun times unavailable for local date %s", now.date())

        self._cached = calculated
        self._cache_key = cache_key
        return self._cached

    @classmethod
    def create(cls, config: SchedulerConfig) -> SunTimesSensor | None:
        location = config.policies.weather
        if location.lat is None or location.lon is None:
            return None
        return cls(location.lat, location.lon)
