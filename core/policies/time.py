from __future__ import annotations

import logging
import time

from configurations.runtime_models import TimePolicyConfig
from core.models.context import Context
from core.models.semantics import VARIABLE_ITEMS, ContextVariable
from core.models.trace import TimeDetails, TimeEvaluation
from core.policies.base import Policy, _periodic_salience

logger = logging.getLogger("Tunalo.Policy")


class TimePolicy(Policy):
    config_key = "time"

    def __init__(self, config: TimePolicyConfig) -> None:
        super().__init__(config)
        self._peaks: dict[str, float] = {}
        self._curve_q = config.curve_q

    @staticmethod
    def _compute_peaks(ds: float, ns: float) -> dict[str, float]:
        day_span = (ns - ds) % 24
        night_span = 24 - day_span
        return {
            "dawn": ds,
            "day": (ds + day_span / 2) % 24,
            "sunset": ns % 24,
            "night": (ns + night_span / 2) % 24,
        }

    _TAG_ORDER = VARIABLE_ITEMS[ContextVariable.TIME]
    _VIRTUAL_PEAKS = [0.0, 6.0, 12.0, 18.0]

    @staticmethod
    def _warp_time(hour: float, peaks: dict[str, float]) -> float:
        real = [peaks[tag] for tag in TimePolicy._TAG_ORDER]
        n = len(real)
        for i in range(n):
            r_a = real[i]
            r_b = real[(i + 1) % n]
            seg = (r_b - r_a) % 24
            pos = (hour - r_a) % 24
            if pos < seg:
                v_a = TimePolicy._VIRTUAL_PEAKS[i]
                return (v_a + pos / seg * 6.0) % 24
        return 0.0

    def _recompute_peaks(self, ds: float, ns: float) -> None:
        self._day_start = ds
        self._night_start = ns
        self._peaks = self._compute_peaks(ds, ns)

    def _update_from_context(self, context: Context) -> None:
        weather = context.weather
        if weather is None or not weather.sunrise or not weather.sunset:
            return
        sunrise = time.localtime(weather.sunrise)
        sunset = time.localtime(weather.sunset)
        ds = sunrise.tm_hour + sunrise.tm_min / 60.0
        ns = sunset.tm_hour + sunset.tm_min / 60.0
        if self._peaks and abs(ds - self._day_start) <= 1 / 60 and abs(ns - self._night_start) <= 1 / 60:
            return
        self._recompute_peaks(ds, ns)
        logger.debug("TimePolicy peaks updated: day_start=%.2f night_start=%.2f", ds, ns)

    def evaluate(self, context: Context) -> TimeEvaluation:
        self._update_from_context(context)
        current_time = context.time
        hour = current_time.tm_hour + current_time.tm_min / 60.0

        if not self._peaks:
            return TimeEvaluation(policy_id=self.config_key, salience={item: 0.0 for item in self._TAG_ORDER}, details=TimeDetails(hour=hour))

        t_virtual = self._warp_time(hour, self._peaks)
        details = TimeDetails(
            hour=hour,
            virtual_hour=t_virtual,
            day_start_hour=self._day_start,
            night_start_hour=self._night_start,
            peaks=self._peaks.copy(),
        )

        values = (1.0, 0.0, -1.0, 0.0)
        salience = {
            item: _periodic_salience(
                t_virtual, [(peak, values[(index - own_index) % 4]) for index, peak in enumerate(self._VIRTUAL_PEAKS)], 24, 0, self._curve_q
            )
            for own_index, item in enumerate(self._TAG_ORDER)
        }
        return TimeEvaluation(policy_id=self.config_key, salience=salience, details=details)
