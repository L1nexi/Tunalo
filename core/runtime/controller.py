from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from configurations.runtime_models import DisturbanceConfig, TimingConfig
from core.models.association import Association
from core.models.context import Context
from core.models.scheduling import Action, Decision, DecisionMode, TimingState
from core.models.selection import Selection
from core.runtime.disturbance import DisturbanceControl
from core.runtime.timing import TimingControl


class Controller:
    def __init__(
        self,
        timing: TimingConfig,
        disturbance: DisturbanceConfig,
        scene_associations: Mapping[str, Association],
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._timing = TimingControl(timing, scene_associations, clock if clock is not None else time.monotonic)
        self._disturbance = DisturbanceControl(disturbance)

    def decide_action(
        self,
        mode: DecisionMode,
        context: Context,
        selection: Selection,
    ) -> Decision:
        selected = selection.scenes
        probabilities = dict(selection.probabilities)
        timing = self._timing.evaluate(probabilities)
        disturbance = self._disturbance.evaluate(context)
        match mode:
            case DecisionMode.NORMAL:
                action = Action.APPLY if selected and timing.ready and disturbance.allowed else Action.NOOP
            case DecisionMode.MANUAL:
                action = Action.APPLY if selected else Action.NOOP
            case DecisionMode.RECOVERY:
                action = Action.APPLY if selected else Action.NOOP
            case DecisionMode.PAUSE:
                action = Action.PAUSE
        return Decision(action, selected, timing=timing, disturbance=disturbance, probabilities=probabilities)

    def notify_executed(self, decision: Decision) -> None:
        self._timing.notify_executed(decision.probabilities)

    def export_state(self) -> TimingState:
        return self._timing.export_state()

    def import_state(self, state: TimingState) -> None:
        self._timing.import_state(state)
