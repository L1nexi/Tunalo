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
    SWITCH = "switch"
    CYCLE = "cycle"
    HOLD = "hold"
    PAUSE = "pause"


class Blocker(StrEnum):
    COOLDOWN = "cooldown"
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
    active_scenes: Scenes


@dataclass
class BlockerEvaluation:
    blocked_by: list[Blocker] = field(default_factory=list)
    cooldown_remaining: float = 0.0
    idle_seconds: float = 0.0
    idle_threshold: float = 0.0
    cpu_percent: float = 0.0
    cpu_threshold: float | None = None
    fullscreen: bool = False
    force_after_remaining: float | None = None

    @property
    def allowed(self) -> bool:
        return len(self.blocked_by) == 0


@dataclass
class Decision:
    """Final controller decision for one tick."""

    action: Action
    target: Scenes
    evaluation: BlockerEvaluation | None = None
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
        if self.action.executed and self.decision.action == Action.SWITCH:
            return self.decision.target
        return self.plan.active_scenes
