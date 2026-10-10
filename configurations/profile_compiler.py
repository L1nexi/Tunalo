from __future__ import annotations

from collections.abc import Mapping

from configurations.profile import Profile
from configurations.runtime_models import MatchingConfig, PoliciesConfig, SceneConfig, SchedulerConfig, SchedulingConfig, WeatherPolicyConfig
from core.models.scene import SceneId
from core.models.semantics import SemanticItem

_SCENE_PRESETS: dict[SceneId, frozenset[SemanticItem]] = {
    SceneId.DAY_WORK: frozenset({"day", "focus"}),
    SceneId.DAY_LEISURE: frozenset({"day", "chill"}),
    SceneId.NIGHT_WORK: frozenset({"night", "focus"}),
    SceneId.NIGHT_LEISURE: frozenset({"night", "chill"}),
    SceneId.SPRING: frozenset({"spring"}),
    SceneId.SUMMER: frozenset({"summer"}),
    SceneId.AUTUMN: frozenset({"autumn"}),
    SceneId.WINTER: frozenset({"winter"}),
    SceneId.SUNSET: frozenset({"sunset"}),
    SceneId.RAIN: frozenset({"rain"}),
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
                weather=WeatherPolicyConfig(
                    api_key=profile.weather.api_key,
                    lat=location.latitude,
                    lon=location.longitude,
                    fetch_interval=600,
                    request_timeout=10,
                )
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
