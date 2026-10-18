from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.models.activity_target import normalize_match_text, normalize_process_name
from core.models.scene import SceneId
from core.models.selection import ContextVariable


class ProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


NonEmptyText = Annotated[str, Field(min_length=1)]
PROFILE_VERSION: Literal[2] = 2


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


class ActivityProfile(ProfileModel):
    work_processes: list[NonEmptyText] = Field(default_factory=list)
    leisure_processes: list[NonEmptyText] = Field(default_factory=list)
    work_title_keywords: list[NonEmptyText] = Field(default_factory=list)
    leisure_title_keywords: list[NonEmptyText] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_conflicting_targets(self) -> Self:
        """Raise ValueError for targets classified as both work and leisure."""
        process_conflicts = {normalize_process_name(value, case_sensitive=False) for value in self.work_processes} & {
            normalize_process_name(value, case_sensitive=False) for value in self.leisure_processes
        }
        title_conflicts = {normalize_match_text(value, case_sensitive=False) for value in self.work_title_keywords} & {
            normalize_match_text(value, case_sensitive=False) for value in self.leisure_title_keywords
        }
        conflicts = sorted(process_conflicts | title_conflicts)
        if conflicts:
            raise ValueError(f"activity targets cannot be both work and leisure: {', '.join(conflicts)}")
        return self


class Profile(ProfileModel):
    version: Literal[2] = PROFILE_VERSION
    setup_complete: Literal[True] = True
    wallpaper_engine_path: NonEmptyText
    language: Literal["zh", "en"] | None = None
    weather: WeatherProfile
    scenes: dict[SceneId, NonEmptyText] = Field(min_length=1)
    matching: MatchingProfile = Field(default_factory=MatchingProfile)
    disturbance: DisturbanceProfile = Field(default_factory=DisturbanceProfile)
    activity: ActivityProfile | None = None
