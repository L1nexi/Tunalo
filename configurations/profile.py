from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.models.scene import SceneId
from core.models.semantics import ContextVariable


class ProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


NonEmptyText = Annotated[str, Field(min_length=1)]


class WeatherLocationProfile(ProfileModel):
    name: str = ""
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class WeatherProfile(ProfileModel):
    api_key: NonEmptyText
    location: WeatherLocationProfile


class DisturbanceProfile(ProfileModel):
    startup_grace_seconds: int = Field(default=15, ge=0)
    idle_before_switch_seconds: int = Field(default=20, ge=0)
    maximum_deferral_minutes: int = Field(default=60, ge=0)
    cycle_interval_minutes: int = Field(default=15, ge=0)


class MatchingProfile(ProfileModel):
    preference_tiers: list[list[ContextVariable]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tiers(self) -> Self:
        """Raise ValueError for empty tiers or repeated variables."""
        if any(not tier for tier in self.preference_tiers):
            raise ValueError("preference tiers must not be empty")
        variables = [variable for tier in self.preference_tiers for variable in tier]
        if len(set(variables)) != len(variables):
            raise ValueError("preference variables must not repeat")
        return self


class Profile(ProfileModel):
    version: Literal[2] = 2
    setup_complete: Literal[True] = True
    wallpaper_engine_path: NonEmptyText
    language: Literal["zh", "en"] | None = None
    weather: WeatherProfile
    scenes: dict[SceneId, NonEmptyText] = Field(min_length=1)
    matching: MatchingProfile = Field(default_factory=MatchingProfile)
    disturbance: DisturbanceProfile = Field(default_factory=DisturbanceProfile)
