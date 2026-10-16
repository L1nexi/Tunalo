from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from core.models.scene import SceneId, Scenes

if TYPE_CHECKING:
    from core.models.context import Context
    from core.models.selection import Selection


class Action(StrEnum):
    NONE = "none"
    APPLY = "apply"
    HOLD = "hold"
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
class ActPlan:
    mode: DecisionMode
    cached_scenes_probabilities: dict[SceneId, float]

    @property
    def active_scenes(self) -> Scenes:
        return Scenes([scene_id for scene_id, probability in self.cached_scenes_probabilities.items() if probability > 0])


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
    distance: float
    reference_distance: float
    interval: float
    elapsed: float
    startup_remaining: float

    @property
    def remaining(self) -> float:
        return max(self.startup_remaining, self.interval - self.elapsed, 0.0)

    @property
    def ready(self) -> bool:
        return self.remaining == 0


@dataclass
class Decision:
    """Final controller decision for one tick."""

    action: Action
    target: Scenes
    timing: TimingEvaluation | None = None
    disturbance: DisturbanceEvaluation | None = None
    probabilities: dict[SceneId, float] = field(default_factory=dict)


@dataclass
class ActionResult:
    target_playlist: str | None = None
    selected_scene: SceneId | None = None
    executed: bool = False


@dataclass
class ScheduleResult:
    context: Context
    selection: Selection
    plan: ActPlan
    decision: Decision
    action: ActionResult

    @property
    def target(self) -> Scenes:
        """返回本次执行后的有效场景；切换未成功时沿用执行前场景。"""
        if self.action.executed and self.decision.action == Action.APPLY:
            return self.decision.target
        return self.plan.active_scenes
