from __future__ import annotations

import pytest

from tools.tuning.harness import TuningModel, build_context, synthetic_config
from tools.tuning.heatmaps import HeatmapSampling, evaluate_cases


def test_single_semantic_suite_splits_four_equal_sources_into_quarters() -> None:
    model = TuningModel(synthetic_config(), suite="single")
    selection = model.evaluate(build_context(12, 172, "mod_rain"), 1.0)

    assert set(selection.probabilities) == {
        "spring",
        "summer",
        "autumn",
        "winter",
        "clear",
        "cloudy",
        "rain",
        "dawn",
        "day",
        "sunset",
        "night",
        "focus",
        "chill",
    }
    assert {scene: chance for scene, chance in selection.probabilities.items() if chance > 0} == pytest.approx(
        {"summer": 0.25, "rain": 0.25, "day": 0.25, "focus": 0.25}
    )


def test_weather_activity_scan_covers_every_standard_time_season_pair() -> None:
    grids = evaluate_cases(synthetic_config(), HeatmapSampling(activity_step=0.5), modes=("wx-act",), suite="single")["wx-act"]

    assert {(grid.fixed["hour"], grid.fixed["day_of_year"]) for _, grid in grids} == {
        (12, 80),
        (12, 103),
        (12, 126),
        (12, 172),
        (13.5, 80),
        (13.5, 103),
        (13.5, 126),
        (13.5, 172),
        (15, 80),
        (15, 103),
        (15, 126),
        (15, 172),
        (18, 80),
        (18, 103),
        (18, 126),
        (18, 172),
    }
    assert len(grids) == 16
    for _, grid in grids:
        assert grid.x_axis.values == (-1, -0.5, 0, 0.5, 1)
        assert "light_rain" in grid.y_axis.values and "violent_rain" in grid.y_axis.values
        assert set(grid.probabilities) == {
            "spring",
            "summer",
            "autumn",
            "winter",
            "clear",
            "cloudy",
            "rain",
            "dawn",
            "day",
            "sunset",
            "night",
            "focus",
            "chill",
        }


def test_activity_season_scan_covers_every_standard_time_weather_pair() -> None:
    grids = evaluate_cases(synthetic_config(), HeatmapSampling(day_step=182, activity_step=1), modes=("act-doy",), suite="single")["act-doy"]

    assert {(grid.fixed["hour"], grid.fixed["weather"]) for _, grid in grids} == {
        (12, None),
        (12, "light_rain"),
        (12, "mod_rain"),
        (12, "heavy_rain"),
        (13.5, None),
        (13.5, "light_rain"),
        (13.5, "mod_rain"),
        (13.5, "heavy_rain"),
        (15, None),
        (15, "light_rain"),
        (15, "mod_rain"),
        (15, "heavy_rain"),
        (18, None),
        (18, "light_rain"),
        (18, "mod_rain"),
        (18, "heavy_rain"),
    }


@pytest.mark.parametrize(
    "suite, mode, compound_count",
    [
        ("pair-wx-doy", "wx-doy", 12),
        ("pair-hour-doy", "hour-doy", 16),
        ("pair-act-doy", "act-doy", 8),
        ("pair-wx-hour", "wx-hour", 12),
        ("pair-wx-act", "wx-act", 6),
        ("pair-act-hour", "act-hour", 8),
    ],
)
def test_pair_suites_keep_single_scenes_and_default_to_the_corresponding_scan(suite: str, mode: str, compound_count: int) -> None:
    config = synthetic_config()
    baseline = TuningModel(config, suite="single").evaluate(build_context(12, 172, "mod_rain"), 1).probabilities
    grids_by_mode = evaluate_cases(config, HeatmapSampling(hour_step=6, day_step=182, activity_step=1), suite=suite)

    assert set(grids_by_mode) == {mode}
    assert len(grids_by_mode[mode]) == 16
    for _, grid in grids_by_mode[mode]:
        assert set(baseline) <= set(grid.probabilities)
        assert len(grid.probabilities) == 13 + compound_count


def test_weather_activity_suite_has_all_six_compounds_and_preserves_rain_only_advantage() -> None:
    model = TuningModel(synthetic_config(), suite="pair-wx-act")
    rain_only = model.evaluate(build_context(12, 172, "mod_rain"), 0)
    both = model.evaluate(build_context(12, 172, "mod_rain"), 1)

    assert {scene for scene in both.probabilities if "_" in scene} == {
        "clear_focus",
        "clear_chill",
        "cloudy_focus",
        "cloudy_chill",
        "rain_focus",
        "rain_chill",
    }
    assert rain_only.probabilities["rain"] > rain_only.probabilities["rain_focus"]
    assert both.probabilities["rain_focus"] > both.probabilities["rain"]


def test_work_cannot_recall_rain_work_during_clear_weather() -> None:
    selection = TuningModel(synthetic_config(), suite="pair-wx-act").evaluate(build_context(12, 172, "clear"), 1)

    assert selection.probabilities["rain_focus"] == 0
    assert selection.excluded_scenes["rain_focus"] == {"rain"}


@pytest.mark.parametrize("hour", [8.5, 15.5])
def test_clear_daytime_work_excludes_night_work(hour: float) -> None:
    selection = TuningModel(synthetic_config()).evaluate(build_context(hour, 126, "clear"), 1)

    assert selection.probabilities["night_work"] == 0
    assert selection.excluded_scenes["night_work"] == {"night"}
    assert selection.probabilities["day_work"] > 0


def test_tuning_alpha_changes_both_periodic_policies() -> None:
    context = build_context(15, 126, None)
    default = TuningModel(synthetic_config()).evaluate(context, 0)
    steeper = TuningModel(synthetic_config(activation_alpha=3)).evaluate(context, 0)

    assert default.salience["day"] == pytest.approx(0.8)
    assert steeper.salience["day"] == pytest.approx(0.9285714285714286)
    assert steeper.salience["spring"] > default.salience["spring"]


def test_hann_comparison_uses_the_complete_support_axis() -> None:
    from tools.tuning.scan import hann_activation

    assert (hann_activation(-1), hann_activation(0), hann_activation(1)) == (-1, 0, 1)
    assert hann_activation(0.5) == pytest.approx(0.7071067811865476)
