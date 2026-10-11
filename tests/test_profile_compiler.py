from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from configurations.profile import Profile
from configurations.profile_compiler import ProfileCompiler
from configurations.profile_store import ProfileStore
from configurations.runtime_models import SceneConfig
from core.models.context import Context, WeatherData, WindowData
from core.models.scene import SceneId
from core.policies import POLICY_REGISTRY
from core.runtime.selector import Selector


def profile(**overrides) -> Profile:
    values = {
        "wallpaper_engine_path": "C:/fixture/wallpaper64.exe",
        "language": "zh",
        "weather": {"api_key": "fixture", "location": {"latitude": 31.23, "longitude": 121.47}},
        "scenes": {"day_work": "WORK", "rain": "RAIN", "summer": "SUMMER"},
    }
    return Profile.model_validate(values | overrides)


def selector_for(user_profile: Profile, counts: dict[str, int]) -> Selector:
    config = ProfileCompiler.compile(user_profile, playlist_item_counts=counts)
    policies = [cls(getattr(config.policies, cls.config_key)) for cls in POLICY_REGISTRY]
    return Selector({scene_id: scene.associations for scene_id, scene in config.scenes.items()}, policies, config.matching)


@pytest.mark.parametrize("tiers", [[[]], [["activity"], ["activity"]], [["time", "time"]], [["unknown"]]])
def test_profile_rejects_empty_repeated_or_unknown_preference_variables(tiers):
    with pytest.raises(ValidationError):
        profile(matching={"preference_tiers": tiers})


@pytest.mark.parametrize("overrides", [{"version": 1}, {"matching": {"response_style": "balanced"}}, {"policies": {}}])
def test_profile_rejects_old_format_and_internal_configuration(overrides):
    with pytest.raises(ValidationError):
        profile(**overrides)


@pytest.mark.parametrize("field", ["avoid_fullscreen", "high_load_threshold_percent", "preset", "overrides"])
def test_profile_rejects_hidden_or_presentation_disturbance_fields(field):
    with pytest.raises(ValidationError):
        profile(disturbance={field: 1})


def test_profile_requires_an_enabled_scene():
    with pytest.raises(ValidationError):
        profile(scenes={})


@pytest.mark.parametrize("items", [set(), {"unknown"}])
def test_runtime_scene_associations_reject_empty_or_unknown_semantics(items):
    with pytest.raises(ValidationError):
        SceneConfig(playlist="fixture", associations=items)


def test_compiled_preference_changes_distribution_using_real_policies():
    neutral = selector_for(profile(), {})
    preferred = selector_for(profile(matching={"preference_tiers": [["weather"], ["activity", "season"]]}), {})
    context = Context(window=WindowData(process="code.exe"), weather=WeatherData(id=502, main="Rain"))
    for _ in range(600):
        ordinary = neutral.select(context)
        weather_first = preferred.select(context)
    assert weather_first.probabilities[SceneId.RAIN] == 1
    assert ordinary.probabilities[SceneId.DAY_WORK] > 0
    assert ordinary.salience == weather_first.salience


def test_m20_playlist_name_size_and_many_to_one_binding_do_not_change_scene_probabilities():
    first = selector_for(profile(scenes={"day_work": "WORK", "rain": "RAIN"}), {"WORK": 1, "RAIN": 9000})
    second = selector_for(profile(scenes={"day_work": "SHARED", "rain": "SHARED"}), {"SHARED": 0})
    context = Context(window=WindowData(process="code.exe"), weather=WeatherData(id=502, main="Rain"))
    for _ in range(600):
        a, b = first.select(context), second.select(context)
    assert a.probabilities == b.probabilities
    assert a.probabilities[SceneId.RAIN] > 0
    assert a.probabilities[SceneId.DAY_WORK] > 0


def test_product_defaults_satisfy_strength_two_rain_budget_constraint():
    from core.models.selection import Salience
    from core.runtime.selector import calculate_distribution

    config = ProfileCompiler.compile(profile())
    result = calculate_distribution(
        Salience({"rain": 2, "focus": 1, "day": 1}), {scene_id: scene.associations for scene_id, scene in config.scenes.items()}, config.matching
    )
    assert result.probabilities[SceneId.RAIN] > result.probabilities[SceneId.DAY_WORK]


@pytest.mark.parametrize(
    "activity, process, title, expected",
    [
        ({"work_processes": ["custom.EXE"]}, "CUSTOM.exe", "", "focus"),
        ({"leisure_processes": ["code"]}, "code.exe", "", "chill"),
        ({"work_title_keywords": ["YouTube"]}, "chrome.exe", "YouTube - watch", "focus"),
        ({"leisure_title_keywords": ["GitHub"]}, "chrome.exe", "GitHub - review", "chill"),
    ],
)
def test_user_activity_rules_replace_defaults_and_classify_all_four_groups(
    activity: dict[str, list[str]], process: str, title: str, expected: str
) -> None:
    selector = selector_for(profile(activity=activity), {})
    result = selector.select(Context(window=WindowData(process=process, title=title)))
    assert result.salience[expected] > 0
    # Product-only rules must not sneak into a custom classifier.
    unrelated = selector_for(profile(activity=activity), {}).select(Context(window=WindowData(process="vlc.exe")))
    assert unrelated.salience["focus"] == unrelated.salience["chill"] == 0


@pytest.mark.parametrize(
    "activity",
    [
        {"work_processes": ["CODE.EXE"], "leisure_processes": ["code"]},
        {"work_title_keywords": ["Straße"], "leisure_title_keywords": ["STRASSE"]},
        {"work_processes": [" "]},
    ],
)
def test_user_activity_rules_reject_normalized_conflicts_and_empty_targets(activity: dict[str, list[str]]) -> None:
    with pytest.raises(ValidationError):
        profile(activity=activity)


@pytest.mark.parametrize("activity, supported_item", [(None, "focus"), ({"leisure_processes": ["code.exe"]}, "chill")])
def test_activity_default_and_custom_rules_survive_profile_store_round_trip(
    tmp_path: Path, activity: dict[str, list[str]] | None, supported_item: str
) -> None:
    current = profile(activity=activity)
    store = ProfileStore(str(tmp_path))
    store.commit(current)
    restored = store.load()
    assert restored is not None
    context = Context(window=WindowData(process="code.exe"))
    before = selector_for(current, {}).select(context)
    after = selector_for(restored, {}).select(context)
    assert after.salience == before.salience
    assert after.salience[supported_item] > 0


def test_empty_activity_rules_do_not_reenable_defaults_after_profile_reload(tmp_path: Path) -> None:
    store = ProfileStore(str(tmp_path))
    store.commit(profile(activity={}))
    restored = store.load()
    assert restored is not None
    result = selector_for(restored, {}).select(Context(window=WindowData(process="code.exe")))
    assert result.salience["focus"] == result.salience["chill"] == 0
