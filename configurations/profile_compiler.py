from __future__ import annotations

from collections.abc import Mapping

from configurations.activity_rules import RULE_GROUPS
from configurations.profile import ActivityProfile, Profile
from configurations.runtime_models import (
    ActivityMatcherConfig,
    ActivityPolicyConfig,
    MatchingConfig,
    PoliciesConfig,
    SceneConfig,
    SchedulerConfig,
    SchedulingConfig,
    WeatherPolicyConfig,
)
from core.models.scene import SceneId
from core.models.selection import SemanticItem

_SCENE_PRESETS: dict[SceneId, frozenset[SemanticItem]] = {
    SceneId.DAY_WORK: frozenset({SemanticItem.DAY, SemanticItem.FOCUS}),
    SceneId.DAY_LEISURE: frozenset({SemanticItem.DAY, SemanticItem.CHILL}),
    SceneId.NIGHT_WORK: frozenset({SemanticItem.NIGHT, SemanticItem.FOCUS}),
    SceneId.NIGHT_LEISURE: frozenset({SemanticItem.NIGHT, SemanticItem.CHILL}),
    SceneId.SPRING: frozenset({SemanticItem.SPRING}),
    SceneId.SUMMER: frozenset({SemanticItem.SUMMER}),
    SceneId.AUTUMN: frozenset({SemanticItem.AUTUMN}),
    SceneId.WINTER: frozenset({SemanticItem.WINTER}),
    SceneId.SUNSET: frozenset({SemanticItem.SUNSET}),
    SceneId.RAIN: frozenset({SemanticItem.RAIN}),
}


class ProfileCompiler:
    @classmethod
    def compile(cls, profile: Profile, *, playlist_item_counts: Mapping[str, int] | None = None) -> SchedulerConfig:
        """Compile a validated Profile into product parameters and runtime inputs."""
        item_counts = playlist_item_counts if playlist_item_counts is not None else {}
        location = profile.weather.location
        disturbance = profile.disturbance
        return SchedulerConfig(
            wallpaper_engine_path=profile.wallpaper_engine_path,
            language=profile.language,
            scenes={
                scene_id: SceneConfig(playlist=playlist, associations=_SCENE_PRESETS[scene_id], item_count=item_counts.get(playlist, 0))
                for scene_id, playlist in profile.scenes.items()
            },
            matching=MatchingConfig(preference_tiers=profile.matching.preference_tiers),
            policies=PoliciesConfig(
                activity=ActivityPolicyConfig(matchers=cls._compile_activity_matchers(profile.activity)),
                weather=WeatherPolicyConfig(
                    api_key=profile.weather.api_key,
                    lat=location.latitude,
                    lon=location.longitude,
                    fetch_interval=600,
                    request_timeout=10,
                ),
            ),
            scheduling=SchedulingConfig(
                startup_delay=disturbance.startup_grace_seconds,
                idle_threshold=disturbance.idle_before_switch_seconds,
                force_after=disturbance.maximum_deferral_minutes * 60,
                cycle_cooldown=disturbance.cycle_interval_minutes * 60,
                cpu_threshold=85,
                cpu_sample_window=10,
            ),
        )

    @staticmethod
    def _compile_activity_matchers(activity: ActivityProfile | None) -> list[ActivityMatcherConfig]:
        """Compile user rules, or product defaults when no rules are supplied."""
        groups = (
            RULE_GROUPS
            if activity is None
            else (
                ("process", "focus", activity.work_processes),
                ("process", "chill", activity.leisure_processes),
                ("title", "focus", activity.work_title_keywords),
                ("title", "chill", activity.leisure_title_keywords),
            )
        )
        return [
            ActivityMatcherConfig(source=source, match="exact" if source == "process" else "contains", pattern=pattern, tag=tag)
            for source, tag, patterns in groups
            for pattern in patterns
        ]
