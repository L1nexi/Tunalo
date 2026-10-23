from __future__ import annotations

from collections import deque
from typing import Any

import psutil

from configurations.runtime_models import SchedulerConfig
from core.sensors.base import Sensor


class CpuSensor(Sensor):
    key = "cpu"

    def __init__(self, window: int = 10) -> None:
        self._samples: deque[float] = deque(maxlen=window)
        # Prime psutil's internal baseline so the first collect() measurement
        # covers a real ~1 s interval rather than returning 0.0.
        psutil.cpu_percent()

    @classmethod
    def create(cls, config: SchedulerConfig) -> CpuSensor | None:
        return cls(window=config.disturbance.cpu_sample_window)

    def collect(self) -> float:
        sample = psutil.cpu_percent()
        self._samples.append(sample)
        return sum(self._samples) / len(self._samples)

    def export_state(self) -> dict[str, Any]:
        return {"samples": list(self._samples)}

    def import_state(self, state: dict[str, Any]) -> None:
        self._samples = deque(state["samples"], maxlen=self._samples.maxlen)
