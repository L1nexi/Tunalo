from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from core.models.scene import SceneId
from core.models.semantics import ContextVariable, SemanticItem

FinitePositive = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class SceneConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    playlist: str = Field(min_length=1)
    associations: frozenset[SemanticItem] = Field(min_length=1)
    item_count: int = 0


class ActivityMatcherConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["process", "title"]
    match: Literal["exact", "regex", "contains"]
    pattern: str = Field(min_length=1)
    tag: Literal["focus", "chill"]
    case_sensitive: bool = False


class BasePolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActivityPolicyConfig(BasePolicyConfig):
    age_scale: FinitePositive = 300.0
    curve_q: FinitePositive = 0.5
    matchers: list[ActivityMatcherConfig] = Field(default_factory=list)


class TimePolicyConfig(BasePolicyConfig):
    curve_q: FinitePositive = 0.5


class SeasonPolicyConfig(BasePolicyConfig):
    spring_peak: int = 80
    summer_peak: int = 172
    autumn_peak: int = 265
    winter_peak: int = 355
    plateau_half_width: float = Field(10.0, ge=0, allow_inf_nan=False)
    curve_q: FinitePositive = 0.5


class WeatherPolicyConfig(BasePolicyConfig):
    api_key: str = ""
    lat: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    lon: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    fetch_interval: float = Field(600.0, ge=60)
    request_timeout: float = Field(10.0, ge=1)

    @field_validator("lat", "lon", mode="before")
    @classmethod
    def validate_coordinate_input(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, bool) or isinstance(value, str):
            raise PydanticCustomError("float_type", "Input should be a valid number")
        return value


class PoliciesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity: ActivityPolicyConfig = Field(default_factory=ActivityPolicyConfig)
    time: TimePolicyConfig = Field(default_factory=TimePolicyConfig)
    season: SeasonPolicyConfig = Field(default_factory=SeasonPolicyConfig)
    weather: WeatherPolicyConfig = Field(default_factory=WeatherPolicyConfig)


class SchedulingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    startup_delay: float = Field(30.0, ge=0)
    idle_threshold: float = Field(60.0, ge=0)
    force_after: float = Field(14400.0, ge=0)
    cycle_cooldown: float = Field(600.0, ge=0)
    cpu_threshold: float = Field(85.0, ge=0, le=100)
    cpu_sample_window: int = Field(10, ge=1)
    pause_on_fullscreen: bool = True


class MatchingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preference_tiers: list[list[ContextVariable]] = Field(default_factory=list)
    positive_boundary: FinitePositive = 0.5
    negative_boundary: FinitePositive = 0.5
    variable_temperature: FinitePositive = 1.4
    scene_temperature: FinitePositive = 1.5


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wallpaper_engine_path: str = ""
    language: Literal["zh", "en"] | None = None
    scenes: dict[SceneId, SceneConfig] = Field(default_factory=dict)
    matching: MatchingConfig = Field(default_factory=MatchingConfig)
    policies: PoliciesConfig = Field(default_factory=PoliciesConfig)
    scheduling: SchedulingConfig = Field(default_factory=SchedulingConfig)
