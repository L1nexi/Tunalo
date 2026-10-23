from __future__ import annotations

from collections.abc import Mapping

from configurations.profile import ActivityProfile, Profile
from configurations.runtime_models import (
    ActivityMatcherConfig,
    ActivityPolicyConfig,
    DisturbanceConfig,
    MatchingConfig,
    PoliciesConfig,
    SceneConfig,
    SchedulerConfig,
    TimingConfig,
    WeatherPolicyConfig,
)


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
                scene_id: SceneConfig(
                    name=scene.name, playlist=scene.playlist, associations=scene.associations, item_count=item_counts.get(scene.playlist, 0)
                )
                for scene_id, scene in profile.scenes.items()
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
            timing=TimingConfig(
                startup_delay=disturbance.startup_grace_seconds,
                cycle_interval=disturbance.cycle_interval_minutes * 60,
            ),
            disturbance=DisturbanceConfig(
                idle_threshold=disturbance.idle_before_switch_seconds,
                cpu_threshold=85,
                cpu_sample_window=10,
            ),
        )

    @staticmethod
    def _compile_activity_matchers(activity: ActivityProfile | None) -> list[ActivityMatcherConfig]:
        """Compile only the rules explicitly supplied by the user."""
        if activity is None:
            return []
        groups = (
            ("process", "work", activity.work_processes),
            ("process", "leisure", activity.leisure_processes),
            ("title", "work", activity.work_title_keywords),
            ("title", "leisure", activity.leisure_title_keywords),
        )
        return [
            ActivityMatcherConfig(source=source, match="exact" if source == "process" else "contains", pattern=pattern, tag=tag)
            for source, tag, patterns in groups
            for pattern in patterns
        ]
