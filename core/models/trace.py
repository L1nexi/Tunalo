from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from core.models.scene import SceneId, Scenes
from core.models.semantics import ContextVariable, SemanticItem

if TYPE_CHECKING:
    from core.models.context import Context


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


@dataclass
class ActivityDetails:
    match_source: Literal["title", "process", "none"] = "none"
    matched_rule: str | None = None
    matched_tag: str | None = None
    window_title: str = ""
    process: str = ""


@dataclass
class TimeDetails:
    hour: float = 0.0
    virtual_hour: float | None = None
    day_start_hour: float | None = None
    night_start_hour: float | None = None
    peaks: dict[str, float] = field(default_factory=dict)


@dataclass
class SeasonDetails:
    day_of_year: int = 0
    peaks: dict[str, int] = field(default_factory=dict)


@dataclass
class WeatherDetails:
    weather_id: int | None = None
    weather_main: str | None = None
    available: bool = False
    mapped: bool = False


@dataclass
class BaseEvaluation:
    policy_id: str
    salience: dict[SemanticItem, float]


@dataclass
class ActivityEvaluation(BaseEvaluation):
    details: ActivityDetails = field(default_factory=ActivityDetails)


@dataclass
class TimeEvaluation(BaseEvaluation):
    details: TimeDetails = field(default_factory=TimeDetails)


@dataclass
class SeasonEvaluation(BaseEvaluation):
    details: SeasonDetails = field(default_factory=SeasonDetails)


@dataclass
class WeatherEvaluation(BaseEvaluation):
    details: WeatherDetails = field(default_factory=WeatherDetails)


type PolicyEvaluation = ActivityEvaluation | TimeEvaluation | SeasonEvaluation | WeatherEvaluation


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
class Selection:
    probabilities: dict[SceneId, float]
    salience: dict[SemanticItem, float]
    reason: Literal["preference", "neutral", "best_effort", "no_safe_scenes"]
    selected_tier: int | None = None
    sources: list[ContextVariable] = field(default_factory=list)
    excluded_scenes: dict[SceneId, frozenset[SemanticItem]] = field(default_factory=dict)
    policy_evaluations: list[PolicyEvaluation] = field(default_factory=list)

    @property
    def scenes(self) -> Scenes:
        return Scenes([scene_id for scene_id, probability in self.probabilities.items() if probability > 0])


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
class ScheduleTrace:
    context: Context
    selection: Selection
    plan: ActPlan
    decision: Decision
    action: ActionResult


@dataclass
class TickTrace:
    tick_id: int
    ts: float
    paused: bool
    pause_until: float
    schedule: ScheduleTrace

    @property
    def context(self) -> Context:
        return self.schedule.context

    @property
    def selection(self) -> Selection:
        return self.schedule.selection

    @property
    def plan(self) -> ActPlan:
        return self.schedule.plan

    @property
    def decision(self) -> Decision:
        return self.schedule.decision

    @property
    def action(self) -> ActionResult:
        return self.schedule.action

    @property
    def active_scenes(self) -> Scenes:
        return self.schedule.plan.active_scenes

    @property
    def target(self) -> Scenes:
        if self.action.executed and self.decision.action == Action.SWITCH:
            return self.decision.target
        return self.active_scenes

    @property
    def cache_update(self) -> Scenes | None:
        if self.action.executed and self.decision.action == Action.SWITCH:
            return self.target
        return None
