from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from configurations.runtime_models import DisturbanceConfig, TimingConfig
from core.models.context import Context
from core.models.scene import SceneId, Scenes
from core.models.scheduling import Action, ActPlan, Decision, DecisionMode
from core.models.selection import Selection, SemanticItem
from core.runtime.disturbance import DisturbanceControl
from core.runtime.timing import TimingControl


class Controller:
    def __init__(
        self,
        timing: TimingConfig,
        disturbance: DisturbanceConfig,
        scene_associations: Mapping[SceneId, frozenset[SemanticItem]],
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._timing = TimingControl(timing, scene_associations, clock if clock is not None else time.monotonic)
        self._disturbance = DisturbanceControl(disturbance)

    def decide_action(
        self,
        plan: ActPlan,
        context: Context,
        selection: Selection,
    ) -> Decision:
        selected = selection.scenes
        probabilities = dict(selection.probabilities)
        match plan.mode:
            case DecisionMode.NORMAL:
                if not selected:
                    return Decision(Action.HOLD if plan.active_scenes else Action.NONE, Scenes())
                timing = self._timing.evaluate(probabilities, plan.cached_scenes_probabilities)
                disturbance = self._disturbance.evaluate(context)
                action = Action.APPLY if timing.ready and disturbance.allowed else Action.HOLD
                return Decision(action, selected, timing=timing, disturbance=disturbance, probabilities=probabilities)
            case DecisionMode.MANUAL:
                if not selected:
                    return Decision(Action.HOLD if plan.active_scenes else Action.NONE, Scenes())
                return Decision(Action.APPLY, selected, probabilities=probabilities)
            case DecisionMode.RECOVERY:
                if not selected:
                    return Decision(Action.NONE, Scenes())
                return Decision(Action.APPLY, selected, probabilities=probabilities)
            case DecisionMode.PAUSE:
                return Decision(Action.PAUSE, selected, probabilities=probabilities)

    def notify_executed(self) -> None:
        self._timing.notify_executed()

    def export_state(self) -> dict[str, float]:
        return self._timing.export_state()

    def import_state(self, state: dict[str, float]) -> None:
        self._timing.import_state(state)
