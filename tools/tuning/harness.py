"""Use real Policies and the shared probability algorithm for calibration."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from configurations.profile import Profile
from configurations.profile_compiler import ProfileCompiler
from configurations.runtime_models import SchedulerConfig
from core.models.context import Context, WeatherData, WindowData
from core.models.scene import SceneId
from core.models.selection import SEMANTIC_ITEMS, VARIABLE_ITEMS, ContextVariable, Salience, Selection, SemanticItem
from core.policies import POLICY_REGISTRY
from core.runtime.selector import Selector, calculate_distribution

WEATHER_PRESETS: dict[str, tuple[int, str]] = {
    "clear": (800, "Clear"),
    "few_clouds": (801, "Clouds"),
    "overcast": (804, "Clouds"),
    "light_drizzle": (300, "Drizzle"),
    "drizzle": (301, "Drizzle"),
    "light_rain": (500, "Rain"),
    "mod_rain": (501, "Rain"),
    "heavy_rain": (502, "Rain"),
    "violent_rain": (504, "Rain"),
    "light_snow": (600, "Snow"),
    "heavy_snow": (602, "Snow"),
    "storm": (211, "Thunderstorm"),
    "storm_rain": (201, "Thunderstorm"),
    "heavy_storm": (212, "Thunderstorm"),
    "fog": (741, "Fog"),
}


type SceneSuite = Literal["single", "product", "pair-wx-doy", "pair-hour-doy", "pair-act-doy", "pair-wx-hour", "pair-wx-act", "pair-act-hour"]

SINGLE_SUITE_ITEMS = (
    SemanticItem.SPRING,
    SemanticItem.SUMMER,
    SemanticItem.AUTUMN,
    SemanticItem.WINTER,
    SemanticItem.CLEAR,
    SemanticItem.CLOUDY,
    SemanticItem.RAIN,
    SemanticItem.DAWN,
    SemanticItem.DAY,
    SemanticItem.SUNSET,
    SemanticItem.NIGHT,
    SemanticItem.FOCUS,
    SemanticItem.CHILL,
)


_PAIR_VARIABLES: dict[SceneSuite, tuple[ContextVariable, ContextVariable]] = {
    "pair-wx-doy": (ContextVariable.SEASON, ContextVariable.WEATHER),
    "pair-hour-doy": (ContextVariable.SEASON, ContextVariable.TIME),
    "pair-act-doy": (ContextVariable.SEASON, ContextVariable.ACTIVITY),
    "pair-wx-hour": (ContextVariable.WEATHER, ContextVariable.TIME),
    "pair-wx-act": (ContextVariable.WEATHER, ContextVariable.ACTIVITY),
    "pair-act-hour": (ContextVariable.TIME, ContextVariable.ACTIVITY),
}

PAIR_SCENES: dict[SceneSuite, dict[str, frozenset[SemanticItem]]] = {
    suite: {
        f"{left.value}_{right.value}": frozenset({left, right})
        for left, right in product(
            (item for item in VARIABLE_ITEMS[left_variable] if item in SINGLE_SUITE_ITEMS),
            (item for item in VARIABLE_ITEMS[right_variable] if item in SINGLE_SUITE_ITEMS),
        )
    }
    for suite, (left_variable, right_variable) in _PAIR_VARIABLES.items()
}


def suite_associations(config: SchedulerConfig, suite: SceneSuite) -> dict[str, frozenset[SemanticItem]]:
    """Give calibration Scenes their own identities and semantic associations."""
    if suite == "product":
        return {scene_id.value: scene.associations for scene_id, scene in config.scenes.items()}
    baseline = {item.value: frozenset({item}) for item in SINGLE_SUITE_ITEMS}
    return baseline if suite == "single" else {**baseline, **PAIR_SCENES[suite]}


def synthetic_config(enabled: tuple[SceneId, ...] = tuple(SceneId)) -> SchedulerConfig:
    """Compile dedicated calibration data without reading the real Profile."""
    profile = Profile(
        wallpaper_engine_path="C:/wallpaper_engine",
        language="zh",
        weather={"api_key": "tuning-key", "location": {"latitude": 39.9, "longitude": 116.4}},
        scenes={scene_id: f"playlist_{scene_id.value}" for scene_id in enabled},
    )
    return ProfileCompiler.compile(profile)


def build_selector(config: SchedulerConfig) -> Selector:
    policies = [cls(getattr(config.policies, cls.config_key)) for cls in POLICY_REGISTRY]
    return Selector({scene_id: scene.associations for scene_id, scene in config.scenes.items()}, policies, config.matching)


def build_context(hour: float, day_of_year: int, weather_name: str | None, activity_tag: str | None = None) -> Context:
    """Build a synthetic observation with local 06:00 sunrise and 18:00 sunset."""
    date = datetime(2025, 1, 1) + timedelta(days=day_of_year - 1, minutes=round(hour * 60))
    weather_id, main = WEATHER_PRESETS[weather_name] if weather_name is not None else (0, "")
    return Context(
        window=WindowData(process={"focus": "code.exe", "chill": "vlc.exe"}.get(activity_tag, "")),
        weather=WeatherData(
            id=weather_id, main=main, sunrise=int(date.replace(hour=6, minute=0).timestamp()), sunset=int(date.replace(hour=18, minute=0).timestamp())
        ),
        time=date.timetuple(),
    )


class TuningModel:
    """Static grids take activity salience directly; traces use Selector.select."""

    def __init__(self, config: SchedulerConfig, *, suite: SceneSuite = "product") -> None:
        self.config = config
        self.associations = suite_associations(config, suite)
        self.policies = [cls(getattr(config.policies, cls.config_key)) for cls in POLICY_REGISTRY if cls.config_key != "activity"]

    def evaluate(self, context: Context, activity_salience: float) -> Selection[str]:
        values = {item: 0.0 for item in SEMANTIC_ITEMS}
        for policy in self.policies:
            values.update(policy.evaluate(context).salience)
        values.update({SemanticItem.FOCUS: activity_salience, SemanticItem.CHILL: -activity_salience})
        return calculate_distribution(Salience(values), self.associations, self.config.matching)


def coerce_activity(value: object) -> float:
    """Convert grid labels into signed focus salience, not observation history."""
    if value is None:
        return 0.0
    if value == "#focus":
        return 1.0
    if value == "#chill":
        return -1.0
    return float(value)
