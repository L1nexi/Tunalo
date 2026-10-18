from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, Self

from pydantic import FiniteFloat, RootModel, model_validator

from core.models.scene import SceneId, Scenes


class ContextVariable(StrEnum):
    SEASON = "season"
    TIME = "time"
    WEATHER = "weather"
    ACTIVITY = "activity"


class SemanticItem(StrEnum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    DAWN = "dawn"
    DAY = "day"
    SUNSET = "sunset"
    NIGHT = "night"
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    WORK = "work"
    LEISURE = "leisure"


VARIABLE_SEMANTIC_ITEMS: dict[ContextVariable, tuple[SemanticItem, ...]] = {
    ContextVariable.SEASON: (SemanticItem.SPRING, SemanticItem.SUMMER, SemanticItem.AUTUMN, SemanticItem.WINTER),
    ContextVariable.TIME: (SemanticItem.DAWN, SemanticItem.DAY, SemanticItem.SUNSET, SemanticItem.NIGHT),
    ContextVariable.WEATHER: (SemanticItem.CLEAR, SemanticItem.CLOUDY, SemanticItem.RAIN, SemanticItem.SNOW),
    ContextVariable.ACTIVITY: (SemanticItem.WORK, SemanticItem.LEISURE),
}
SEMANTIC_ITEMS: tuple[SemanticItem, ...] = tuple(item for items in VARIABLE_SEMANTIC_ITEMS.values() for item in items)


class Salience(RootModel[dict[SemanticItem, FiniteFloat]]):
    """Validated model input; omitted semantic items have neutral evidence."""

    @model_validator(mode="after")
    def complete_vocabulary(self) -> Self:
        self.root = {item: self.root.get(item, 0.0) for item in SEMANTIC_ITEMS}
        return self


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


@dataclass
class Selection[SceneKey: str = SceneId]:
    probabilities: dict[SceneKey, float]
    salience: dict[SemanticItem, float]
    reason: Literal["preference", "best_effort", "no_safe_scenes"]
    selected_tier: int | None = None
    sources: list[ContextVariable] = field(default_factory=list)
    excluded_scenes: dict[SceneKey, frozenset[SemanticItem]] = field(default_factory=dict)
    policy_evaluations: list[PolicyEvaluation] = field(default_factory=list)

    @property
    def scenes(self: Selection[SceneId]) -> Scenes:
        return Scenes([scene_id for scene_id, probability in self.probabilities.items() if probability > 0])
