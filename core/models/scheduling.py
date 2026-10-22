from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from core.models.scene import Scenes

if TYPE_CHECKING:
    from core.models.context import Context
    from core.models.selection import Selection


class Action(StrEnum):
    NOOP = "noop"
    APPLY = "apply"
    PAUSE = "pause"


class Blocker(StrEnum):
    FULLSCREEN = "fullscreen"
    CPU = "cpu"
    IDLE = "idle"


class DecisionMode(StrEnum):
    NORMAL = "normal"
    MANUAL = "manual"
    RECOVERY = "recovery"
    PAUSE = "pause"


@dataclass(frozen=True)
class TimingState:
    cached_scenes_probabilities: dict[str, float]
    last_success_time: float
    startup_end: float


@dataclass
class DisturbanceEvaluation:
    blocked_by: list[Blocker] = field(default_factory=list)
    idle_seconds: float = 0.0
    idle_threshold: float = 0.0
    cpu_percent: float = 0.0
    cpu_threshold: float | None = None
    fullscreen: bool = False

    @property
    def allowed(self) -> bool:
        return len(self.blocked_by) == 0


@dataclass(frozen=True)
class TimingEvaluation:
    active_scenes: Scenes
    distance: float | None
    reference_distance: float
    interval: float | None
    elapsed: float
    startup_remaining: float

    @property
    def remaining(self) -> float | None:
        if self.interval is None:
            return None
        return max(self.startup_remaining, self.interval - self.elapsed, 0.0)

    @property
    def ready(self) -> bool:
        return self.remaining == 0


@dataclass
class Decision:
    """Final controller decision for one tick."""

    action: Action
    target: Scenes
    timing: TimingEvaluation
    disturbance: DisturbanceEvaluation
    probabilities: dict[str, float] = field(default_factory=dict)


@dataclass
class ActionResult:
    target_playlist: str | None = None
    selected_scene: str | None = None
    executed: bool = False


@dataclass
class ScheduleResult:
    context: Context
    selection: Selection
    mode: DecisionMode
    decision: Decision
    action: ActionResult

    @property
    def target(self) -> Scenes:
        if self.action.executed and self.decision.action == Action.APPLY:
            return self.decision.target
        return self.decision.timing.active_scenes
