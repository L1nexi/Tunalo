"""第一轮 Scene 调参的驱动层：合成 Profile 走真实 compiler/policies/Matcher。

管线与 ``Engine._build_components`` 同构（POLICY_REGISTRY + Matcher），只把
Sensor 换成合成 Context；不复制任何策略逻辑。活动信号按 legacytuning 的
DirectActivityPolicy 语义注入——常数输入的 EMA 稳态等价于直接给
raw_direction={tag:1.0}、salience=1、intensity=强度。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from configurations.profile import Profile
from configurations.profile_compiler import ProfileCompiler
from configurations.runtime_models import SchedulerConfig
from core.models.context import Context, WeatherData, WindowData
from core.models.scene import SceneId
from core.policies import POLICY_REGISTRY
from core.policies.activity import ActivityPolicy
from core.runtime.matcher import Matcher

# 全部场景启用、等量播单：winner 分布只反映匹配本身，不受壁纸数量影响。
SYNTHETIC_ITEM_COUNT = 20
_EVAL_YEAR = 2025
_SUNRISE_HOUR = 6
_SUNSET_HOUR = 18


def synthetic_config(enabled: tuple[SceneId, ...] = tuple(SceneId)) -> SchedulerConfig:
    """Compile a full-scene synthetic profile with the real ProfileCompiler."""
    profile = Profile(
        wallpaper_engine_path="C:/wallpaper_engine",
        language="zh",
        weather={
            "api_key": "tuning-key",
            "location": {"latitude": 39.9, "longitude": 116.4},
        },
        scenes={scene_id: f"playlist_{scene_id.value}" for scene_id in enabled},
        activity={
            "work_processes": ["focusapp.exe"],
            "leisure_processes": ["chillapp.exe"],
        },
    )
    counts = {f"playlist_{scene_id.value}": SYNTHETIC_ITEM_COUNT for scene_id in enabled}
    return ProfileCompiler.compile(profile, playlist_item_counts=counts)


def build_matcher(config: SchedulerConfig) -> Matcher:
    """Assemble policies and Matcher exactly like ``Engine._build_components``."""
    policies = [cls(getattr(config.policies, cls.config_key)) for cls in POLICY_REGISTRY]
    return Matcher(config.scenes, policies, config.tags)


def activity_alpha(config: SchedulerConfig) -> float:
    """ActivityPolicy EMA 的单 tick 系数（smoothing_window 来自编译配置）。"""
    return 2.0 / (config.policies.activity.smoothing_window + 1.0)


@dataclass(frozen=True)
class WeatherInput:
    weather_id: int
    main: str


# legacytuning 的天气命名预设：热图天气轴与旧图逐格同义。
WEATHER_PRESETS: dict[str, WeatherInput] = {
    "clear": WeatherInput(800, "Clear"),
    "few_clouds": WeatherInput(801, "Clouds"),
    "overcast": WeatherInput(804, "Clouds"),
    "light_drizzle": WeatherInput(300, "Drizzle"),
    "drizzle": WeatherInput(301, "Drizzle"),
    "light_rain": WeatherInput(500, "Rain"),
    "mod_rain": WeatherInput(501, "Rain"),
    "heavy_rain": WeatherInput(502, "Rain"),
    "light_snow": WeatherInput(600, "Snow"),
    "heavy_snow": WeatherInput(602, "Snow"),
    "storm": WeatherInput(211, "Thunderstorm"),
    "storm_rain": WeatherInput(201, "Thunderstorm"),
    "heavy_storm": WeatherInput(212, "Thunderstorm"),
    "fog": WeatherInput(741, "Fog"),
}


def build_context(
    hour: float,
    day_of_year: int,
    weather_name: str | None,
    activity_tag: str | None,
    activity_strength: float,
) -> Context:
    """Build one synthetic tick snapshot (legacytuning 的 Scenario 语义)。

    天气预设为 None 时天气策略静默，但日出日落仍固定提供（当地 06:00/18:00），
    使 TimePolicy 的 hour 轴在无天气行也保持可解释——这是与旧工具的关键差异：
    旧 WeatherData 没有日出日落字段，现行 TimePolicy 需要它们才有峰。
    """
    date = datetime(_EVAL_YEAR, 1, 1) + timedelta(days=day_of_year - 1, minutes=round(hour * 60))
    sunrise = int(date.replace(hour=_SUNRISE_HOUR).timestamp())
    sunset = int(date.replace(hour=_SUNSET_HOUR).timestamp())

    weather_data = None
    if weather_name is not None:
        preset = WEATHER_PRESETS[weather_name]
        weather_data = WeatherData(id=preset.weather_id, main=preset.main, sunrise=sunrise, sunset=sunset)
    else:
        weather_data = WeatherData(id=0, main="", sunrise=sunrise, sunset=sunset)

    process = {"focus": "focusapp.exe", "chill": "chillapp.exe"}.get(activity_tag or "", "")
    return Context(
        window=WindowData(title="", process=process),
        weather=weather_data,
        time=date.timetuple(),
    )


def prime_activity(matcher: Matcher, config: SchedulerConfig, activity_tag: str | None, strength: float) -> None:
    """把 ActivityPolicy 精确置于 DirectActivityPolicy 的等价状态。

    match() 内部会先 evaluate 一次再计分，因此注入的是“再走一格后恰好等于
    稳态”的 pre-state：dir_ema={tag:1.0}（常数输入下不变），mag_ema 按
    (v - alpha) / (1 - alpha) 回推；无活动时注入空状态。
    """
    policy = next(policy for policy in matcher.policies if isinstance(policy, ActivityPolicy))
    if activity_tag is None or strength <= 0:
        policy.import_state({"dir_ema": {}, "mag_ema": 0.0})
        return
    alpha = activity_alpha(config)
    policy.import_state({"dir_ema": {activity_tag: 1.0}, "mag_ema": (strength - alpha) / (1.0 - alpha)})


def activity_from_axis(value: float) -> tuple[str | None, float]:
    """活动轴取值语义与 legacytuning 一致：0=idle，负=chill，正=focus。"""
    if abs(value) <= 1e-9:
        return None, 0.0
    if value < 0:
        return "chill", abs(value)
    return "focus", value


def coerce_activity(value: object) -> tuple[str | None, float]:
    """fixed 值里的活动写法：None / "#focus" / "#chill" / 数值强度。"""
    if value is None:
        return None, 0.0
    if value == "#focus":
        return "focus", 1.0
    if value == "#chill":
        return "chill", 1.0
    return activity_from_axis(float(value))  # type: ignore[arg-type]
