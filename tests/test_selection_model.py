from __future__ import annotations

import math

import pytest

from configurations.runtime_models import MatchingConfig, SceneConfig
from core.models.scene import SceneId
from core.models.selection import VARIABLE_SEMANTIC_ITEMS, Salience, Selection
from core.runtime.selector import calculate_distribution

RAIN = SceneId.RAIN
WORK = SceneId.DAY_WORK
RAIN_WORK = SceneId.NIGHT_WORK
SUMMER = SceneId.SUMMER
SUMMER_WORK = SceneId.DAY_LEISURE
WINTER_WORK = SceneId.NIGHT_LEISURE
DAY = SceneId.SUNSET


def choose(values: dict[str, float], scenes: dict[SceneId, set[str]], tiers: list[list[str]] | None = None, **params: float) -> Selection:
    associations = {scene_id: SceneConfig(playlist="fixture", associations=items).associations for scene_id, items in scenes.items()}
    return calculate_distribution(Salience(values), associations, MatchingConfig(preference_tiers=tiers or [], **params))


def test_m01_four_equal_single_item_scenes_without_preferences_are_uniform() -> None:
    selection = choose({"rain": 1, "work": 1, "day": 1, "summer": 1}, {RAIN: {"rain"}, WORK: {"work"}, DAY: {"day"}, SUMMER: {"summer"}})
    assert selection.probabilities == pytest.approx({RAIN: 0.25, WORK: 0.25, DAY: 0.25, SUMMER: 0.25})
    assert selection.reason == "best_effort"
    assert selection.sources == list(VARIABLE_SEMANTIC_ITEMS)


def test_two_significant_time_items_share_one_source_budget() -> None:
    values = {"day": 0.95, "sunset": 0.95, "rain": 1}
    tiers = [["time", "weather"]]
    one = choose(values, {DAY: {"day"}, RAIN: {"rain"}}, tiers).probabilities
    two = choose(values, {DAY: {"day"}, WORK: {"sunset"}, RAIN: {"rain"}}, tiers).probabilities
    assert two[RAIN] == pytest.approx(one[RAIN])
    assert two[DAY] + two[WORK] == pytest.approx(one[DAY])
    assert two[DAY] == pytest.approx(two[WORK])


def test_m02_m03_compound_scene_advantage_within_weather_budget_reverses_when_both_contexts_are_clear() -> None:
    scenes = {RAIN: {"rain"}, RAIN_WORK: {"rain", "work"}}
    rain_only = choose({"rain": 1}, scenes, [["weather"]]).probabilities
    both = choose({"rain": 1, "work": 1}, scenes, [["weather"]]).probabilities
    assert rain_only[RAIN] > rain_only[RAIN_WORK] > 0
    assert both[RAIN_WORK] > both[RAIN] > 0


def test_m04_stronger_rain_gets_more_budget_than_summer() -> None:
    p = choose({"rain": 2, "summer": 1}, {RAIN: {"rain"}, SUMMER: {"summer"}}, [["weather", "season"]]).probabilities
    assert p[RAIN] > p[SUMMER] > 0


@pytest.mark.parametrize("tiers", [None, [["weather", "activity", "time"]]])
def test_m05_spec_independent_numeric_example(tiers: list[list[str]] | None) -> None:
    p = choose(
        {"rain": 2, "work": 1, "day": 1},
        {RAIN: {"rain"}, WORK: {"work", "day"}},
        tiers,
        variable_temperature=1.4,
        scene_temperature=1.5,
    ).probabilities
    assert p == pytest.approx({RAIN: 0.5052844367, WORK: 0.4947155633})


def test_m06_negative_association_excludes_scene_from_every_source() -> None:
    result = choose({"summer": 1, "winter": -1, "work": 1}, {SUMMER_WORK: {"summer", "work"}, WINTER_WORK: {"winter", "work"}})
    assert result.probabilities == {SUMMER_WORK: 1, WINTER_WORK: 0}
    assert result.excluded_scenes == {WINTER_WORK: {"winter"}}


def test_m07_m08_m09_neutral_weather_equal_contexts_and_violent_rain_within_activity_budget() -> None:
    scenes = {SUMMER_WORK: {"summer", "work"}, WORK: {"work"}, RAIN_WORK: {"rain", "work"}}
    neutral = choose({"summer": 1, "work": 1}, scenes, [["activity"]]).probabilities
    equal = choose({"summer": 1, "work": 1, "rain": 1}, scenes, [["activity"]]).probabilities
    violent = choose({"summer": 1, "work": 1, "rain": 2}, scenes, [["activity"]]).probabilities
    assert neutral[SUMMER_WORK] > neutral[WORK] > neutral[RAIN_WORK] > 0
    assert equal[SUMMER_WORK] == pytest.approx(equal[RAIN_WORK])
    assert equal[RAIN_WORK] > equal[WORK]
    assert violent[RAIN_WORK] > violent[SUMMER_WORK] > 0


def test_m10_preference_controls_sources_but_all_evidence_still_scores_and_excludes() -> None:
    scenes = {RAIN: {"rain"}, WORK: {"work"}, RAIN_WORK: {"rain", "work"}, WINTER_WORK: {"winter", "work"}}
    result = choose({"work": 1, "rain": 2, "winter": -1}, scenes, [["activity"], ["weather"]])
    assert result.probabilities[RAIN] == 0
    assert result.probabilities[WINTER_WORK] == 0
    assert result.probabilities[RAIN_WORK] > result.probabilities[WORK] > 0
    assert result.sources == ["activity"]


@pytest.mark.parametrize("tiers", [[["activity"], ["weather"]], [["season"], ["activity"], ["time"], ["weather"]]])
def test_m11_multiple_empty_or_excluded_tiers_keep_cascading(tiers: list[list[str]]) -> None:
    p = choose({"work": 1, "rain": 1, "winter": -1}, {WINTER_WORK: {"winter", "work"}, RAIN: {"rain"}}, tiers).probabilities
    assert p == {WINTER_WORK: 0, RAIN: 1}


def test_m12_partial_empty_tier_renormalizes_without_adding_lower_sources() -> None:
    p = choose(
        {"rain": 2, "work": 1, "day": 1, "summer": 1},
        {WORK: {"work"}, DAY: {"day"}, SUMMER: {"summer"}},
        [["weather", "activity", "time"], ["season"]],
    ).probabilities
    assert p == {WORK: 0.5, DAY: 0.5, SUMMER: 0}


def test_m13_exhausted_preferences_use_all_safe_variable_sources() -> None:
    values = {"summer": 1, "work": 0.3, "winter": -1}
    scenes = {SUMMER: {"summer"}, WORK: {"work"}, WINTER_WORK: {"winter", "work"}}
    result = choose(values, scenes, [["weather"], ["activity"]])
    assert result.reason == "best_effort"
    assert result.selected_tier is None
    assert result.sources == ["season", "activity"]
    assert result.probabilities[SUMMER] > result.probabilities[WORK] > 0
    assert result.probabilities[WINTER_WORK] == 0
    assert result.probabilities == choose(values, scenes).probabilities


@pytest.mark.parametrize("variable_temperature", [0.2, 10])
def test_empty_preferences_use_variable_temperature_to_budget_unrecalled_sources(variable_temperature: float) -> None:
    scenes = {RAIN: {"rain"}, WORK: {"work"}, WINTER_WORK: {"winter", "work"}}
    result = choose({"rain": 1, "winter": -1}, scenes, variable_temperature=variable_temperature, scene_temperature=1.5)
    assert result.reason == "best_effort"
    assert result.selected_tier is None
    assert result.sources == ["weather", "activity"]
    rain_budget = 1 / (1 + math.exp(-1 / variable_temperature))
    assert result.probabilities == pytest.approx({RAIN: rain_budget, WORK: 1 - rain_budget, WINTER_WORK: 0})


@pytest.mark.parametrize("tiers", [None, [["season"]]])
@pytest.mark.parametrize("strength", [0, 0.3, 1])
def test_best_effort_preserves_variable_budgets_when_scene_counts_differ(tiers: list[list[str]] | None, strength: float) -> None:
    values = {"rain": strength, "work": strength}
    scenes = {RAIN: {"rain"}, RAIN_WORK: {"rain"}, WORK: {"work"}}
    unpreferred = choose(values, scenes, tiers)
    assert unpreferred.reason == "best_effort"
    assert unpreferred.selected_tier is None
    assert unpreferred.probabilities == pytest.approx({RAIN: 0.25, RAIN_WORK: 0.25, WORK: 0.5})
    assert unpreferred.sources == ["weather", "activity"]


def test_best_effort_renormalizes_budgets_after_unavailable_sources_are_removed() -> None:
    result = choose({"rain": 1, "work": 1, "summer": 100}, {RAIN: {"rain"}, WORK: {"work"}})
    assert result.probabilities == {RAIN: 0.5, WORK: 0.5}
    assert result.sources == ["weather", "activity"]


@pytest.mark.parametrize("tiers", [None, [["weather", "activity"]]])
def test_m14_scene_count_changes_internal_allocation_not_variable_budget(tiers: list[list[str]] | None) -> None:
    base = {RAIN: {"rain"}, WORK: {"work"}}
    expanded = {**base, RAIN_WORK: {"rain", "cloudy"}}
    p = choose({"rain": 1, "work": 1}, base, tiers).probabilities
    q = choose({"rain": 1, "work": 1}, expanded, tiers).probabilities
    assert p[RAIN] == pytest.approx(q[RAIN] + q[RAIN_WORK])
    assert p[WORK] == pytest.approx(q[WORK])


def test_m15_mixed_rain_and_snow_use_max_weather_salience() -> None:
    scenes = {RAIN: {"rain"}, RAIN_WORK: {"snow"}, WORK: {"work"}}
    tiers = [["weather", "activity"]]
    p = choose({"rain": 1, "work": 1}, scenes, tiers).probabilities
    q = choose({"rain": 1, "snow": 0.95, "work": 1}, scenes, tiers).probabilities
    assert p[RAIN] == pytest.approx(q[RAIN] + q[RAIN_WORK])
    assert q[WORK] == 0.5


def test_m16_cloudy_work_cannot_take_rain_budget() -> None:
    p = choose({"rain": 1, "work": 1, "cloudy": 0}, {RAIN: {"rain"}, WORK: {"cloudy", "work"}}, [["weather", "activity"]]).probabilities
    assert p == {RAIN: 0.5, WORK: 0.5}


def test_m17_zero_evidence_uniform_variable_budgets_accumulate_on_compound_scenes() -> None:
    scenes = {RAIN: {"rain"}, WORK: {"day", "work"}, SUMMER: {"summer", "day", "work"}}
    zero = choose({}, scenes).probabilities
    tiny = choose({"rain": 1e-10, "work": 1e-10}, scenes).probabilities
    assert zero == pytest.approx({RAIN: 0.25, WORK: 0.25, SUMMER: 0.5})
    assert tiny == pytest.approx(zero, abs=1e-9)


def test_m18_best_effort_preserves_exclusions_and_weak_signed_evidence() -> None:
    result = choose(
        {"winter": -1, "work": 0.3, "rain": -0.05},
        {WINTER_WORK: {"winter", "work"}, WORK: {"work"}, RAIN: {"rain"}, DAY: {"clear"}},
        [["activity"]],
    )
    assert result.reason == "best_effort"
    assert result.probabilities[WINTER_WORK] == 0
    assert result.probabilities[WORK] > result.probabilities[DAY] > result.probabilities[RAIN] > 0


@pytest.mark.parametrize("scenes", [{}, {WINTER_WORK: {"winter"}}])
def test_m19_no_available_or_safe_scenes_returns_empty_distribution(scenes: dict[SceneId, set[str]]) -> None:
    result = choose({"winter": -1}, scenes)
    assert result.probabilities == {}


@pytest.mark.parametrize("rain, expected", [(0.899999, "best_effort"), (0.9, "preference"), (0.900001, "preference")])
def test_positive_boundary_includes_equality(rain: float, expected: str) -> None:
    result = choose({"rain": rain}, {RAIN: {"rain"}}, [["weather"]])
    assert result.reason == expected


@pytest.mark.parametrize("rain, source", [(0.75, "activity"), (0.899999, "activity"), (0.9, "weather")])
def test_positive_boundary_controls_when_preferred_weather_stops_cascading(rain: float, source: str) -> None:
    result = choose({"rain": rain, "work": 1}, {RAIN: {"rain"}, WORK: {"work"}}, [["weather"], ["activity"]])
    assert result.sources == [source]
    assert result.probabilities[RAIN if source == "weather" else WORK] == 1


@pytest.mark.parametrize("winter, excluded", [(-0.099999, False), (-0.1, True), (-0.100001, True)])
def test_negative_boundary_includes_equality(winter: float, excluded: bool) -> None:
    result = choose({"winter": winter}, {WINTER_WORK: {"winter"}, RAIN: {"rain"}})
    assert (result.probabilities[WINTER_WORK] == 0) is excluded


def test_equivalent_associations_and_input_orders_have_equivalent_probabilities() -> None:
    scenes = {WORK: {"work", "day"}, RAIN_WORK: {"day", "work"}, RAIN: {"rain"}}
    values = {"work": 1, "day": 1, "rain": 1}
    p = choose(values, scenes, [["activity", "weather", "time"]]).probabilities
    q = choose(dict(reversed(list(values.items()))), dict(reversed(list(scenes.items()))), [["time", "weather", "activity"]]).probabilities
    assert p == pytest.approx(q)
    assert p[WORK] == pytest.approx(p[RAIN_WORK])


def test_product_evidence_produces_a_complete_probability_distribution() -> None:
    p = choose(
        {"work": 1, "day": 1, "summer": 1, "rain": 2},
        {WORK: {"work", "day", "summer"}, RAIN: {"rain", "work"}},
    ).probabilities
    assert all(math.isfinite(value) and value >= 0 for value in p.values())
    assert math.fsum(p.values()) == pytest.approx(1)
