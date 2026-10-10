from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from configurations.runtime_models import ActivityPolicyConfig, MatchingConfig, SeasonPolicyConfig, TimePolicyConfig, WeatherPolicyConfig
from core.models.context import Context, WeatherData, WindowData
from core.models.scene import SceneId
from core.policies import ActivityPolicy, SeasonPolicy, TimePolicy, WeatherPolicy
from core.runtime.selector import Selector


def observation(process: str = "", title: str = "", *, day: int = 172, hour: float = 12, sunrise: float = 6, sunset: float = 18) -> Context:
    date = datetime(2025, 1, 1) + timedelta(days=day - 1, minutes=round(hour * 60))
    midnight = date.replace(hour=0, minute=0)
    return Context(
        window=WindowData(process=process, title=title),
        time=date.timetuple(),
        weather=WeatherData(
            id=800,
            main="Clear",
            sunrise=int((midnight + timedelta(hours=sunrise)).timestamp()),
            sunset=int((midnight + timedelta(hours=sunset)).timestamp()),
        ),
    )


def replay(policy: ActivityPolicy, processes: list[str]) -> dict[str, float]:
    for process in processes:
        result = policy.evaluate(observation(process))
    return result.salience


@pytest.mark.parametrize("slots, expected", [(1, 0.000000200), (60, 0.042110997), (120, 0.284477721), (180, 0.649890150), (600, 1)])
def test_s05_startup_uses_full_window_denominator_with_spec_numeric_anchors(slots: int, expected: float) -> None:
    policy = ActivityPolicy(ActivityPolicyConfig(age_scale=300, curve_q=0.5))
    result = replay(policy, ["code.exe"] * slots)
    assert result["focus"] == pytest.approx(expected, abs=1e-9)
    assert result["chill"] == pytest.approx(-expected, abs=1e-9)


def test_s02_new_observation_has_more_effect_than_same_direction_at_oldest_slot() -> None:
    old = replay(ActivityPolicy(ActivityPolicyConfig()), ["code.exe"] + ["chrome.exe"] * 599)
    new = replay(ActivityPolicy(ActivityPolicyConfig()), ["chrome.exe"] * 599 + ["code.exe"])
    assert new["focus"] > old["focus"] > 0


def test_s02_sampling_intervals_do_not_change_slot_weights() -> None:
    fast, slow = ActivityPolicy(ActivityPolicyConfig()), ActivityPolicy(ActivityPolicyConfig())
    for index, process in enumerate(["code.exe"] * 100 + ["chrome.exe"] * 50 + ["vlc.exe"] * 20):
        a = fast.evaluate(observation(process, hour=12))
        b = slow.evaluate(observation(process, day=1 + index, hour=3))
    assert a.salience == b.salience


def test_s03_last_600_observations_completely_replace_previous_activity() -> None:
    policy = ActivityPolicy(ActivityPolicyConfig())
    replay(policy, ["code.exe"] * 900)
    result = replay(policy, ["vlc.exe"] * 600)
    assert result == {"focus": -1, "chill": 1}


def test_s04_swap_work_and_leisure_before_nonlinear_mapping() -> None:
    first = replay(ActivityPolicy(ActivityPolicyConfig()), ["code.exe"] * 120 + ["chrome.exe"] * 20 + ["vlc.exe"] * 80)
    second = replay(ActivityPolicy(ActivityPolicyConfig()), ["vlc.exe"] * 120 + ["chrome.exe"] * 20 + ["code.exe"] * 80)
    assert first["focus"] == pytest.approx(second["chill"])
    assert first["chill"] == pytest.approx(second["focus"])


def test_other_adds_zero_direction_without_immediately_clearing_existing_history() -> None:
    policy = ActivityPolicy(ActivityPolicyConfig())
    established = replay(policy, ["code.exe"] * 180)
    one_unknown = replay(policy, ["chrome.exe"])
    no_history = replay(policy, ["chrome.exe"] * 600)
    assert established["focus"] > one_unknown["focus"] > 0
    assert no_history == {"focus": 0, "chill": 0}


@pytest.mark.parametrize(
    "process,title,expected",
    [
        ("CODE.EXE", "", "focus"),
        ("winword", "", "focus"),
        ("dota2.exe", "", "chill"),
        ("chrome.exe", "GitHub - pull request", "focus"),
        ("msedge.exe", "bilibili", "chill"),
        ("code.exe", "YouTube", "chill"),
        ("Unknown", "腾讯文档", "focus"),
        ("steam.exe", "", None),
        ("chrome.exe", "unknown website", None),
        ("", "", None),
    ],
)
def test_built_in_window_rules_and_title_priority(process: str, title: str, expected: str | None) -> None:
    result = ActivityPolicy(ActivityPolicyConfig()).evaluate(observation(process, title))
    if expected is None:
        assert result.salience == {"focus": 0, "chill": 0}
    else:
        assert result.salience[expected] > 0


def test_literal_activity_matching_keeps_unicode_casefolding() -> None:
    config = ActivityPolicyConfig(matchers=[{"source": "title", "match": "contains", "pattern": "STRASSE", "tag": "focus"}])
    assert ActivityPolicy(config).evaluate(observation(title="Straße")).salience["focus"] > 0


def test_s01_semantics_independent_of_preference_scene_catalog_and_playlists() -> None:
    selectors = [
        Selector(
            {SceneId.RAIN: frozenset({"rain"})}, [ActivityPolicy(ActivityPolicyConfig()), WeatherPolicy(WeatherPolicyConfig())], MatchingConfig()
        ),
        Selector(
            {SceneId.DAY_WORK: frozenset({"focus", "day"})},
            [ActivityPolicy(ActivityPolicyConfig()), WeatherPolicy(WeatherPolicyConfig())],
            MatchingConfig(preference_tiers=[["activity"], ["weather"]]),
        ),
    ]
    for _ in range(180):
        results = [selector.select(observation("code.exe")) for selector in selectors]
    assert results[0].salience == results[1].salience
    assert results[0].probabilities != results[1].probabilities


@pytest.mark.parametrize("item, peak", [("spring", 80), ("summer", 172), ("autumn", 265), ("winter", 355)])
def test_s06_each_season_has_platform_including_both_endpoints(item: str, peak: int) -> None:
    policy = SeasonPolicy(SeasonPolicyConfig())
    assert all(policy.evaluate(observation(day=day)).salience[item] == 1 for day in range(peak - 10, peak + 11))
    assert policy.evaluate(observation(day=peak - 11)).salience[item] < 1
    assert policy.evaluate(observation(day=peak + 11)).salience[item] < 1


def test_s07_opposite_season_negative_and_adjacent_seasons_neutral() -> None:
    policy = SeasonPolicy(SeasonPolicyConfig())
    assert policy.evaluate(observation(day=172)).salience == {"spring": 0, "summer": 1, "autumn": 0, "winter": -1}
    assert policy.evaluate(observation(day=355)).salience == {"spring": 0, "summer": -1, "autumn": 0, "winter": 1}


def test_s08_season_transitions_monotonic_connected_and_periodic() -> None:
    policy = SeasonPolicy(SeasonPolicyConfig())
    rising = [policy.evaluate(observation(day=day)).salience["summer"] for day in range(90, 163)]
    falling = [policy.evaluate(observation(day=day)).salience["summer"] for day in range(182, 256)]
    assert rising == sorted(rising)
    assert falling == sorted(falling, reverse=True)
    for boundary in [70, 90, 162, 182, 255, 275, 345, 365]:
        before = policy.evaluate(observation(day=boundary - 1)).salience
        current = policy.evaluate(observation(day=boundary)).salience
        assert all(abs(before[item] - current[item]) < 0.03 for item in current)
    leap = Context(time=datetime(2024, 12, 31).timetuple())  # tm_yday=366, same periodic position as day 1
    assert policy.evaluate(leap).salience == policy.evaluate(observation(day=1)).salience


@pytest.mark.parametrize(
    "sunrise,sunset,peaks",
    [
        (6, 18, [(6, "dawn"), (12, "day"), (18, "sunset"), (0, "night")]),
        (5, 19, [(5, "dawn"), (12, "day"), (19, "sunset"), (0, "night")]),
        (7, 17, [(7, "dawn"), (12, "day"), (17, "sunset"), (0, "night")]),
    ],
)
def test_s09_time_anchors_follow_api_and_day_night_midpoints(sunrise: float, sunset: float, peaks: list[tuple[float, str]]) -> None:
    policy = TimePolicy(TimePolicyConfig())
    opposites = {"dawn": "sunset", "day": "night", "sunset": "dawn", "night": "day"}
    for hour, item in peaks:
        result = policy.evaluate(observation(hour=hour, sunrise=sunrise, sunset=sunset)).salience
        assert result[item] == 1
        assert result[opposites[item]] == -1
        assert all(value == 0 for other, value in result.items() if other not in {item, opposites[item]})
        neighbor = policy.evaluate(observation(hour=hour + 1 / 60, sunrise=sunrise, sunset=sunset)).salience[item]
        assert 0 < neighbor < 1


def test_time_missing_initial_weather_is_neutral_and_later_missing_weather_retains_peaks() -> None:
    policy = TimePolicy(TimePolicyConfig())
    context = observation(hour=12)
    missing = Context(time=context.time, weather=None)
    assert policy.evaluate(missing).salience == {"dawn": 0, "day": 0, "sunset": 0, "night": 0}
    established = policy.evaluate(context).salience
    assert policy.evaluate(missing).salience == established


@pytest.mark.parametrize(
    "code,rain,snow",
    [
        (300, 0.1, 0),
        (302, 0.35, 0),
        (500, 0.25, 0),
        (501, 0.5, 0),
        (502, 1, 0),
        (503, 1.5, 0),
        (504, 2, 0),
        (511, 0.75, 0),
        (615, 0.25, 0.25),
        (616, 0.5, 0.5),
        (601, 0, 0.75),
        (602, 0, 1.5),
        (621, 0, 0.85),
    ],
)
def test_s10_weather_code_mapping_preserves_intermediate_and_unbounded_strength(code: int, rain: float, snow: float) -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=code, main="Unknown")))
    assert result.salience == {"clear": 0, "cloudy": 0, "rain": rain, "snow": snow}


@pytest.mark.parametrize("code", [800, 801, 802, 803, 804])
def test_s11_clear_and_cloudy_are_neutral_even_when_main_says_rain(code: int) -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=code, main="Rain")))
    assert result.salience == {"clear": 0, "cloudy": 0, "rain": 0, "snow": 0}


@pytest.mark.parametrize("main,rain,snow", [("Rain", 0.5, 0), ("Drizzle", 0.2, 0), ("Snow", 0, 0.75), ("Thunderstorm", 0, 0), ("Unknown", 0, 0)])
def test_weather_unknown_code_falls_back_to_main_without_inventing_evidence(main: str, rain: float, snow: float) -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=999, main=main)))
    assert result.salience == {"clear": 0, "cloudy": 0, "rain": rain, "snow": snow}
