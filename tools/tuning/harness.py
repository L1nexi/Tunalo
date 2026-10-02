"""第一轮 Scene 调参的驱动层：合成 Profile 走真实 compiler/policies/Matcher。

管线与 ``Engine._build_components`` 同构（POLICY_REGISTRY + Matcher），只把
Sensor 换成合成 Context；不复制任何策略逻辑。活动信号按常数输入的 EMA 稳态
注入，使每个网格单元都是彼此独立的收敛快照。
"""

from __future__ import annotations

import sys
import time as time_module
from dataclasses import dataclass
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

_ACTIVITY_PROCESSES = {"focus": "focusapp.exe", "chill": "chillapp.exe"}


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


@dataclass(frozen=True)
class ContextPreset:
    """One fixed weather/activity situation; hour and day stay grid axes."""

    name: str
    weather_id: int
    weather_main: str
    activity: str  # "" | "focus" | "chill"


def build_context(preset: ContextPreset, hour: int, day_of_year: int) -> Context:
    """Build one synthetic tick snapshot for a grid cell."""
    now = time_module.localtime()
    # time 策略用 localtime 读取日出日落；固定为当地 06:00/18:00，让时间面可解释。
    sunrise = int(time_module.mktime((now.tm_year, now.tm_mon, now.tm_mday, 6, 0, 0, 0, now.tm_yday, -1)))
    sunset = int(time_module.mktime((now.tm_year, now.tm_mon, now.tm_mday, 18, 0, 0, 0, now.tm_yday, -1)))
    return Context(
        window=WindowData(title="", process=_ACTIVITY_PROCESSES.get(preset.activity, "")),
        weather=WeatherData(id=preset.weather_id, main=preset.weather_main, sunrise=sunrise, sunset=sunset),
        time=time_module.struct_time((now.tm_year, now.tm_mon, now.tm_mday, hour, 0, 0, 0, day_of_year, -1)),
    )


def match_once(config: SchedulerConfig, context: Context):
    """One independent, converged match for a grid cell."""
    matcher = build_matcher(config)
    _prime_activity(matcher, context)
    return matcher.match(context)


def _prime_activity(matcher: Matcher, context: Context) -> None:
    """ActivityPolicy 的 EMA 平滑窗约百 tick；常数输入的稳态即瞬时值，直接注入。"""
    for policy in matcher.policies:
        if not isinstance(policy, ActivityPolicy):
            continue
        policy.evaluate(context)
        state = policy.export_state()
        if not state["dir_ema"]:
            continue
        policy.import_state({"dir_ema": {tag: 1.0 for tag in state["dir_ema"]}, "mag_ema": 1.0})
