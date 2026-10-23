from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from configurations.runtime_models import SchedulerConfig

logger = logging.getLogger("Tunalo.Sensor")


class Sensor(ABC):
    key: ClassVar[str]

    @abstractmethod
    def collect(self) -> Any:
        """Collects data from the sensor."""
        pass

    def export_state(self) -> dict[str, Any]:
        return {}

    def import_state(self, state: dict[str, Any]) -> None:
        pass

    @classmethod
    @abstractmethod
    def create(cls, config: SchedulerConfig) -> Sensor | None:
        """Factory method: return a ready instance, or None to skip registration."""
        pass
