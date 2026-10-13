from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from configurations.profile import Profile
from configurations.profile_compiler import ProfileCompiler
from configurations.runtime_models import ActivityPolicyConfig, MatchingConfig, SeasonPolicyConfig, TimePolicyConfig, WeatherPolicyConfig
from core.models.context import Context, WeatherData, WindowData
from core.models.scene import SceneId
from core.models.selection import Selection
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


def activity_config(**parameters: float) -> ActivityPolicyConfig:
    return ActivityPolicyConfig(
        matchers=[
            {"source": "process", "match": "exact", "pattern": "code", "tag": "work"},
            {"source": "process", "match": "exact", "pattern": "vlc", "tag": "leisure"},
        ],
        **parameters,
    )


@pytest.mark.parametrize("slots, expected", [(1, 0.003327787), (60, 0.198914147), (120, 0.392275167), (180, 0.571668849), (600, 1)])
def test_s05_startup_uses_weighted_evidence_with_full_window_denominator(slots: int, expected: float) -> None:
    policy = ActivityPolicy(activity_config(age_scale=300))
    result = replay(policy, ["code.exe"] * slots)
    assert result["work"] == pytest.approx(expected, abs=1e-9)
    assert result["leisure"] == pytest.approx(-expected, abs=1e-9)


def test_s02_new_observation_has_more_effect_than_same_direction_at_oldest_slot() -> None:
    old = replay(ActivityPolicy(activity_config()), ["code.exe"] + ["chrome.exe"] * 599)
    new = replay(ActivityPolicy(activity_config()), ["chrome.exe"] * 599 + ["code.exe"])
    assert new["work"] > old["work"] > 0


def test_s02_sampling_intervals_do_not_change_slot_weights() -> None:
    fast, slow = ActivityPolicy(activity_config()), ActivityPolicy(activity_config())
    for index, process in enumerate(["code.exe"] * 100 + ["chrome.exe"] * 50 + ["vlc.exe"] * 20):
        a = fast.evaluate(observation(process, hour=12))
        b = slow.evaluate(observation(process, day=1 + index, hour=3))
    assert a.salience == b.salience


def test_s03_last_600_observations_completely_replace_previous_activity() -> None:
    policy = ActivityPolicy(activity_config())
    replay(policy, ["code.exe"] * 900)
    result = replay(policy, ["vlc.exe"] * 600)
    assert result == {"work": -1, "leisure": 1}


def test_s04_swap_work_and_leisure_reverses_weighted_evidence() -> None:
    first = replay(ActivityPolicy(activity_config()), ["code.exe"] * 120 + ["chrome.exe"] * 20 + ["vlc.exe"] * 80)
    second = replay(ActivityPolicy(activity_config()), ["vlc.exe"] * 120 + ["chrome.exe"] * 20 + ["code.exe"] * 80)
    assert first["work"] == pytest.approx(second["leisure"])
    assert first["leisure"] == pytest.approx(second["work"])


def test_other_adds_zero_direction_without_immediately_clearing_existing_history() -> None:
    policy = ActivityPolicy(activity_config())
    established = replay(policy, ["code.exe"] * 180)
    one_unknown = replay(policy, ["chrome.exe"])
    no_history = replay(policy, ["chrome.exe"] * 600)
    assert established["work"] > one_unknown["work"] > 0
    assert no_history == {"work": 0, "leisure": 0}


@pytest.mark.parametrize(
    "process,title,expected",
    [
        ("CODE.EXE", "", "work"),
        ("winword", "", "work"),
        ("dota2.exe", "", "leisure"),
        ("chrome.exe", "GitHub - pull request", "work"),
        ("msedge.exe", "bilibili", "leisure"),
        ("code.exe", "YouTube", "leisure"),
        ("Unknown", "腾讯文档", "work"),
        ("steam.exe", "", None),
        ("chrome.exe", "unknown website", None),
        ("", "", None),
    ],
)
def test_built_in_window_rules_and_title_priority(process: str, title: str, expected: str | None) -> None:
    profile = Profile(
        wallpaper_engine_path="C:/fixture/wallpaper64.exe",
        weather={"api_key": "fixture", "location": {"latitude": 0, "longitude": 0}},
        scenes={SceneId.DAY_WORK: "WORK"},
    )
    config = ProfileCompiler.compile(profile)
    result = ActivityPolicy(config.policies.activity).evaluate(observation(process, title))
    if expected is None:
        assert result.salience == {"work": 0, "leisure": 0}
    else:
        assert result.salience[expected] > 0


def test_literal_activity_matching_keeps_unicode_casefolding() -> None:
    config = ActivityPolicyConfig(matchers=[{"source": "title", "match": "contains", "pattern": "STRASSE", "tag": "work"}])
    assert ActivityPolicy(config).evaluate(observation(title="Straße")).salience["work"] > 0


def test_s01_semantics_independent_of_preference_scene_catalog_and_playlists() -> None:
    selectors = [
        Selector({SceneId.RAIN: frozenset({"rain"})}, [ActivityPolicy(activity_config()), WeatherPolicy(WeatherPolicyConfig())], MatchingConfig()),
        Selector(
            {SceneId.DAY_WORK: frozenset({"work", "day"})},
            [ActivityPolicy(activity_config()), WeatherPolicy(WeatherPolicyConfig())],
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
    assert all(policy.evaluate(observation(day=day)).salience[item] == 1 for day in range(peak - 7, peak + 8))
    assert policy.evaluate(observation(day=peak - 8)).salience[item] < 1
    assert policy.evaluate(observation(day=peak + 8)).salience[item] < 1


def test_s07_opposite_season_negative_and_adjacent_seasons_only_weak_evidence() -> None:
    policy = SeasonPolicy(SeasonPolicyConfig())
    summer = policy.evaluate(observation(day=172)).salience
    winter = policy.evaluate(observation(day=355)).salience
    assert (summer["summer"], summer["winter"]) == (1, -1)
    assert (winter["winter"], winter["summer"]) == (1, -1)
    assert all(abs(result[item]) < 0.1 for result in (summer, winter) for item in ("spring", "autumn"))


def test_s08_season_transitions_monotonic_connected_and_periodic() -> None:
    policy = SeasonPolicy(SeasonPolicyConfig())
    rising = [policy.evaluate(observation(day=day)).salience["summer"] for day in range(87, 166)]
    falling = [policy.evaluate(observation(day=day)).salience["summer"] for day in range(179, 259)]
    assert rising == sorted(rising)
    assert falling == sorted(falling, reverse=True)
    for boundary in [73, 87, 165, 179, 258, 272, 348, 362, 365]:
        before = policy.evaluate(observation(day=boundary - 1)).salience
        current = policy.evaluate(observation(day=boundary)).salience
        assert all(abs(before[item] - current[item]) < 0.03 for item in current)
    leap = Context(time=datetime(2024, 12, 31).timetuple())  # tm_yday=366, same periodic position as day 1
    assert policy.evaluate(leap).salience == policy.evaluate(observation(day=1)).salience


@pytest.mark.parametrize("alpha, expected", [(2, 0.96), (3, 0.9941860465116279)])
def test_time_maps_equal_distance_from_peak_to_equal_salience(alpha: float, expected: float) -> None:
    policy = TimePolicy(TimePolicyConfig(activation_alpha=alpha))
    morning = policy.evaluate(observation(hour=9)).salience
    afternoon = policy.evaluate(observation(hour=15)).salience
    assert morning["day"] == pytest.approx(expected)
    assert afternoon["day"] == pytest.approx(expected)
    assert morning["night"] == pytest.approx(-expected)
    assert afternoon["night"] == pytest.approx(-expected)


def test_season_alpha_strengthens_partial_support_without_moving_peak() -> None:
    mild = SeasonPolicy(SeasonPolicyConfig(activation_alpha=1.5))
    steep = SeasonPolicy(SeasonPolicyConfig(activation_alpha=3))
    assert 0 < mild.evaluate(observation(day=126)).salience["spring"] < steep.evaluate(observation(day=126)).salience["spring"] < 1
    assert mild.evaluate(observation(day=80)).salience["spring"] == steep.evaluate(observation(day=80)).salience["spring"] == 1


@pytest.mark.parametrize(
    "sunrise,sunset,peaks",
    [
        (6, 18, [(6, "dawn"), (12, "day"), (18, "sunset"), (0, "night")]),
        (5, 19, [(5, "dawn"), (12, "day"), (19, "sunset"), (0, "night")]),
        (7, 17, [(7, "dawn"), (12, "day"), (17, "sunset"), (0, "night")]),
        (8, 16, [(8, "dawn"), (12, "day"), (16, "sunset"), (0, "night")]),
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


def test_time_broadens_day_and_narrows_sunset_with_mirror_phase_mapping() -> None:
    policy = TimePolicy(TimePolicyConfig())
    morning = policy.evaluate(observation(hour=9)).salience
    evening = policy.evaluate(observation(hour=19.5)).salience
    assert morning["day"] == pytest.approx(0.96)
    assert morning["dawn"] == pytest.approx(0.4705882352941177)
    assert evening["sunset"] == pytest.approx(0.8545994065281899)
    assert evening["night"] == pytest.approx(0.7344262295081968)


def test_time_mirror_mapping_keeps_opposing_pairs_symmetric_and_closes_across_midnight() -> None:
    policy = TimePolicy(TimePolicyConfig())
    for half_hour in range(48):
        result = policy.evaluate(observation(hour=half_hour / 2)).salience
        assert result["day"] == pytest.approx(-result["night"], abs=1e-12, rel=0)
        assert result["dawn"] == pytest.approx(-result["sunset"], abs=1e-12, rel=0)
    before = policy.evaluate(observation(hour=23 + 59 / 60)).salience
    after = policy.evaluate(observation(hour=1 / 60)).salience
    assert before["night"] == pytest.approx(after["night"], abs=1e-12, rel=0)
    assert all(abs(before[item] - after[item]) < 0.0001 for item in before)
    midnight = policy.evaluate(observation(hour=0)).salience
    next_midnight = policy.evaluate(observation(hour=24)).salience
    assert midnight == next_midnight


def test_time_priority_cascades_after_early_sunset_instead_of_recalling_sunset_two_hours_later() -> None:
    selector = Selector(
        {SceneId.SUNSET: frozenset({"sunset"}), SceneId.NIGHT_WORK: frozenset({"night"}), SceneId.WINTER: frozenset({"winter"})},
        [TimePolicy(TimePolicyConfig()), SeasonPolicy(SeasonPolicyConfig())],
        MatchingConfig(preference_tiers=[["time"], ["season"]]),
    )
    result = selector.select(observation(day=355, hour=18, sunrise=8, sunset=16))
    assert result.sources == ["season"]
    assert result.probabilities == {SceneId.SUNSET: 0, SceneId.NIGHT_WORK: 0, SceneId.WINTER: 1}


def test_drizzle_strengthening_increases_rain_support() -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    light = policy.evaluate(Context(weather=WeatherData(id=300))).salience
    ordinary = policy.evaluate(Context(weather=WeatherData(id=301))).salience
    heavy = policy.evaluate(Context(weather=WeatherData(id=302))).salience
    assert 0 < light["rain"] < ordinary["rain"] < heavy["rain"] < 1


@pytest.mark.parametrize("code, strength", [(500, 0.75), (501, 1.0), (502, 2.0), (504, 4.0)])
def test_rain_levels_use_the_decided_salience_anchors(code: int, strength: float) -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=code))).salience
    assert result["rain"] == strength


@pytest.mark.parametrize("code", [210, 211, 212, 221])
def test_thunderstorm_is_strong_rain_scene_evidence_without_explicit_rain(code: int) -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=code, main="Thunderstorm"))).salience
    assert result["rain"] >= 2
    assert result["clear"] <= -0.5
    assert -0.5 < result["cloudy"] < 0
    assert result["snow"] == 0


def test_thunderstorm_severity_strengthens_rain_scene_support() -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    light, ordinary, heavy = [
        policy.evaluate(Context(weather=WeatherData(id=code, main="Thunderstorm"))).salience["rain"] for code in [210, 211, 212]
    ]
    heavy_rain = policy.evaluate(Context(weather=WeatherData(id=502, main="Rain"))).salience["rain"]
    violent_rain = policy.evaluate(Context(weather=WeatherData(id=504, main="Rain"))).salience["rain"]
    assert light < ordinary < heavy
    assert ordinary > heavy_rain
    assert heavy >= violent_rain


@pytest.mark.parametrize("code", [200, 201, 202, 230, 231, 232])
def test_light_precipitation_does_not_dilute_thunderstorm_salience(code: int) -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    thunderstorm = policy.evaluate(Context(weather=WeatherData(id=code, main="Thunderstorm"))).salience["rain"]
    heavy_rain = policy.evaluate(Context(weather=WeatherData(id=502, main="Rain"))).salience["rain"]
    assert thunderstorm > heavy_rain


@pytest.mark.parametrize("code", [211, 212, 999])
def test_thunderstorm_rain_scene_outweighs_established_work_without_preferences(code: int) -> None:
    config = ProfileCompiler.compile(
        Profile(
            wallpaper_engine_path="C:/wallpaper_engine",
            weather={"api_key": "test-key", "location": {"latitude": 31.0, "longitude": 121.0}},
            scenes={SceneId.RAIN: "rain-playlist", SceneId.DAY_WORK: "work-playlist"},
            activity={"work_processes": ["code"]},
        )
    )
    selector = Selector(
        {scene: settings.associations for scene, settings in config.scenes.items()},
        [
            ActivityPolicy(config.policies.activity),
            WeatherPolicy(config.policies.weather),
            TimePolicy(config.policies.time),
            SeasonPolicy(config.policies.season),
        ],
        config.matching,
    )
    context = observation(process="code.exe", hour=12)
    context.weather.id = code
    context.weather.main = "Thunderstorm"
    for _ in range(600):
        result = selector.select(context)
    assert result.probabilities[SceneId.RAIN] > result.probabilities[SceneId.DAY_WORK] > 0


def test_rain_strength_follows_weather_severity_and_can_exceed_one() -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    results = [policy.evaluate(Context(weather=WeatherData(id=code))).salience for code in [500, 501, 502, 503, 504]]
    strengths = [result["rain"] for result in results]
    assert all(earlier < later for earlier, later in zip(strengths, strengths[1:]))
    assert strengths[-1] > 1
    assert all(result["snow"] == 0 for result in results)


def test_snow_strength_increases_without_inventing_rain() -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    ordinary = policy.evaluate(Context(weather=WeatherData(id=601))).salience
    heavy = policy.evaluate(Context(weather=WeatherData(id=602))).salience
    assert 0 < ordinary["snow"] < heavy["snow"]
    assert ordinary["rain"] == heavy["rain"] == 0


def test_freezing_rain_remains_rain_evidence() -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=511, main="Snow"))).salience
    assert result["rain"] > 0
    assert result["snow"] == 0


def test_mixed_precipitation_does_not_double_the_common_reverse_evidence() -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    rain = policy.evaluate(Context(weather=WeatherData(id=501))).salience
    mixed = policy.evaluate(Context(weather=WeatherData(id=616))).salience
    assert mixed["rain"] > 0 and mixed["snow"] > 0
    assert mixed["clear"] == rain["clear"]
    assert mixed["cloudy"] == rain["cloudy"]


def test_heavier_rain_strengthens_clear_opposition_but_cloudy_stays_weakly_opposed() -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    moderate = policy.evaluate(Context(weather=WeatherData(id=501))).salience
    violent = policy.evaluate(Context(weather=WeatherData(id=504))).salience
    assert violent["clear"] < moderate["clear"] < 0
    assert -0.5 < moderate["cloudy"] < 0
    assert -0.5 < violent["cloudy"] < 0


def test_sunny_sky_supports_clear_and_opposes_precipitation() -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=800, main="Rain"))).salience
    assert result["clear"] >= 0.5
    assert result["rain"] <= -0.5 and result["snow"] <= -0.5
    assert -0.5 < result["cloudy"] < 0


def test_overcast_sky_supports_cloudy_but_only_weakly_opposes_clear_and_precipitation() -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=804))).salience
    assert result["cloudy"] >= 0.5
    assert all(-0.5 < result[item] < 0 for item in ["clear", "rain", "snow"])


def test_cloud_cover_changes_clear_and_cloudy_evidence_gradually() -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    results = [policy.evaluate(Context(weather=WeatherData(id=code))).salience for code in [800, 801, 802, 803, 804]]
    assert all(before["clear"] > after["clear"] for before, after in zip(results, results[1:]))
    assert all(before["cloudy"] < after["cloudy"] for before, after in zip(results, results[1:]))


@pytest.mark.parametrize("main, known_code", [("Rain", 501), ("Thunderstorm", 211), ("Drizzle", 301), ("Snow", 601), ("Clear", 800), ("cLoUdS", 804)])
def test_unknown_weather_code_uses_the_main_category(main: str, known_code: int) -> None:
    policy = WeatherPolicy(WeatherPolicyConfig())
    known = policy.evaluate(Context(weather=WeatherData(id=known_code)))
    fallback = policy.evaluate(Context(weather=WeatherData(id=999, main=main)))
    assert fallback.salience == known.salience


def test_known_neutral_code_takes_precedence_over_main_rain() -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=WeatherData(id=741, main="Rain")))
    assert result.salience == {"clear": 0, "cloudy": 0, "rain": 0, "snow": 0}


@pytest.mark.parametrize("weather", [None, WeatherData(id=999, main="Unknown")])
def test_missing_or_unrecognized_weather_has_no_evidence(weather: WeatherData | None) -> None:
    result = WeatherPolicy(WeatherPolicyConfig()).evaluate(Context(weather=weather))
    assert result.salience == {"clear": 0, "cloudy": 0, "rain": 0, "snow": 0}


def established_work_selection(weather_code: int) -> Selection:
    selector = Selector(
        {
            SceneId.DAY_WORK: frozenset({"work"}),
            SceneId.DAY_LEISURE: frozenset({"work", "clear"}),
            SceneId.NIGHT_WORK: frozenset({"work", "cloudy"}),
            SceneId.RAIN: frozenset({"work", "rain"}),
        },
        [ActivityPolicy(activity_config()), WeatherPolicy(WeatherPolicyConfig())],
        MatchingConfig(preference_tiers=[["activity"]]),
    )
    context = Context(window=WindowData(process="code.exe"), weather=WeatherData(id=weather_code))
    for _ in range(600):
        result = selector.select(context)
    return result


@pytest.mark.parametrize(
    "code, preferred, excluded",
    [
        (800, SceneId.DAY_LEISURE, SceneId.RAIN),
        (502, SceneId.RAIN, SceneId.DAY_LEISURE),
        (211, SceneId.RAIN, SceneId.DAY_LEISURE),
        (212, SceneId.RAIN, SceneId.DAY_LEISURE),
    ],
)
def test_weather_strong_opposition_excludes_scenes_even_when_activity_has_priority(code: int, preferred: SceneId, excluded: SceneId) -> None:
    result = established_work_selection(code)
    assert result.probabilities[excluded] == 0
    assert max(result.probabilities, key=result.probabilities.__getitem__) == preferred


def test_overcast_opposition_excludes_clear_work_and_rain_work_even_when_activity_has_priority() -> None:
    result = established_work_selection(804)
    assert result.probabilities[SceneId.RAIN] == 0
    assert result.probabilities[SceneId.DAY_LEISURE] == 0
    assert result.excluded_scenes == {SceneId.RAIN: {"rain"}, SceneId.DAY_LEISURE: {"clear"}}
    assert result.probabilities[SceneId.NIGHT_WORK] > result.probabilities[SceneId.DAY_WORK] > 0
