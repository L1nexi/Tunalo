from __future__ import annotations

from collections.abc import Callable, Mapping

from configurations.runtime_models import TimingConfig
from core.models.association import Association
from core.models.scene import Scenes
from core.models.scheduling import TimingEvaluation, TimingState


class TimingControl:
    def __init__(
        self,
        config: TimingConfig,
        scene_associations: Mapping[str, Association],
        clock: Callable[[], float],
    ) -> None:
        self._clock = clock
        self._cycle_interval = config.cycle_interval
        self._reference_distance = sum(len(association) for association in scene_associations.values()) / (4 * len(scene_associations))
        now = clock()
        self._startup_end = now + config.startup_delay
        self._last_success_time = now
        self._cached_scenes_probabilities: dict[str, float] = {}

    def evaluate(self, current: Mapping[str, float]) -> TimingEvaluation:
        previous = self._cached_scenes_probabilities
        distance = None
        interval = None
        if current:
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
            active_scenes=Scenes([scene_id for scene_id, probability in previous.items() if probability > 0]),
            distance=distance,
            reference_distance=self._reference_distance,
            interval=interval,
            elapsed=now - self._last_success_time,
            startup_remaining=max(0.0, self._startup_end - now),
        )

    def notify_executed(self, probabilities: Mapping[str, float]) -> None:
        self._cached_scenes_probabilities = dict(probabilities)
        self._last_success_time = self._clock()

    def export_state(self) -> TimingState:
        return TimingState(
            cached_scenes_probabilities=dict(self._cached_scenes_probabilities),
            last_success_time=self._last_success_time,
            startup_end=self._startup_end,
        )

    def import_state(self, state: TimingState) -> None:
        self._cached_scenes_probabilities = dict(state.cached_scenes_probabilities)
        self._last_success_time = state.last_success_time
        self._startup_end = state.startup_end
