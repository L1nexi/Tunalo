from __future__ import annotations

import pytest

from core.math_utils import periodic_salience, salience_activation, time_decaying_activation


@pytest.mark.parametrize("value, expected", [(-1, -1), (-0.5, -0.8), (0, 0), (0.5, 0.8), (1, 1)])
def test_salience_activation_default_worked_values(value: float, expected: float) -> None:
    assert salience_activation(value) == pytest.approx(expected)


@pytest.mark.parametrize("alpha", [1.5, 2, 3])
def test_alpha_changes_steepness_without_moving_zero_or_endpoints(alpha: float) -> None:
    positions = [-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1]
    values = [salience_activation(value, alpha) for value in positions]
    assert values == sorted(values)
    assert (values[0], values[4], values[-1]) == (-1, 0, 1)
    assert values == pytest.approx([-value for value in reversed(values)])


def test_larger_alpha_strengthens_partial_support() -> None:
    assert salience_activation(0.5, 3) == pytest.approx(0.9285714285714286)
    assert salience_activation(0.5, 3) > salience_activation(0.5, 2)


@pytest.mark.parametrize("age, expected", [(0, 1), (150, 0.9), (300, 0.5), (450, 0.1), (600, 0), (900, 0)])
def test_time_decay_half_weight_and_finite_end(age: float, expected: float) -> None:
    assert time_decaying_activation(age, scale=300) == pytest.approx(expected)


def test_time_decay_scale_changes_age_units() -> None:
    assert time_decaying_activation(0.5) == pytest.approx(0.9)
    assert time_decaying_activation(1) == 0.5
    assert time_decaying_activation(2) == 0


@pytest.mark.parametrize("position, expected", [(0, -1), (6, 0), (9, 0.8), (12, 1), (15, 0.8), (18, 0), (24, -1)])
def test_periodic_salience_maps_peak_neutral_and_opposite(position: float, expected: float) -> None:
    assert periodic_salience(position, 12, 24) == pytest.approx(expected)


def test_periodic_salience_uses_short_arc_across_year_boundary() -> None:
    current = periodic_salience(360, 5, 365)
    assert current > 0.99
    assert current == periodic_salience(-5, 5, 365)
    assert current == periodic_salience(370, 360, 365)


@pytest.mark.parametrize("position, expected", [(73, 1), (87, 1), (255.5, -1), (269.5, -1), (171.25, 0)])
def test_periodic_platform_includes_both_ends_and_keeps_neutral_midpoint(position: float, expected: float) -> None:
    assert periodic_salience(position, 80, 365, plateau_half_width=7) == expected


def test_periodic_curve_leaves_platforms_continuously() -> None:
    assert 0.999 < periodic_salience(88, 80, 365, plateau_half_width=7) < 1
    assert -1 < periodic_salience(254.5, 80, 365, plateau_half_width=7) < -0.999
