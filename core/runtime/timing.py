from __future__ import annotations

from collections.abc import Callable, Mapping

from configurations.runtime_models import TimingConfig
from core.models.scene import SceneId
from core.models.scheduling import TimingEvaluation
from core.models.selection import SemanticItem


class TimingControl:
    def __init__(
        self,
        config: TimingConfig,
        scene_associations: Mapping[SceneId, frozenset[SemanticItem]],
        clock: Callable[[], float],
    ) -> None:
        self._clock = clock
        self._cycle_interval = config.cycle_interval
        self._reference_distance = sum(len(items) for items in scene_associations.values()) / (4 * len(scene_associations))
        now = clock()
        self._startup_end = now + config.startup_delay
        self._last_success_time = now

    def evaluate(self, current: Mapping[SceneId, float], previous: Mapping[SceneId, float]) -> TimingEvaluation:
        distance = (
            sum(abs(current.get(scene_id, 0.0) - previous.get(scene_id, 0.0)) for scene_id in current.keys() | previous.keys()) / 2
            if previous
            else 1.0
        )
        if distance == 0:
            interval = self._cycle_interval
        else:
            relative_change = distance / self._reference_distance
            interval = min(self._cycle_interval, max(0.0, (2 / relative_change) ** 5 - 1))
        now = self._clock()
        return TimingEvaluation(
            distance=distance,
            reference_distance=self._reference_distance,
            interval=interval,
            elapsed=now - self._last_success_time,
            startup_remaining=max(0.0, self._startup_end - now),
        )

    def notify_executed(self) -> None:
        self._last_success_time = self._clock()

    def export_state(self) -> dict[str, float]:
        return {"last_success_time": self._last_success_time, "startup_end": self._startup_end}

    def import_state(self, state: dict[str, float]) -> None:
        self._last_success_time = state["last_success_time"]
        self._startup_end = state["startup_end"]
