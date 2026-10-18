"""Group Scene probability maps and winner maps by calibration mode."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mpl_colors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import QuadMesh
from matplotlib.ticker import PercentFormatter

from configurations.runtime_models import SchedulerConfig
from core.models.selection import VARIABLE_SEMANTIC_ITEMS, ContextVariable, Salience, SemanticItem
from core.policies import SeasonPolicy, TimePolicy, WeatherPolicy
from core.runtime.selector import calculate_distribution
from tools.tuning.harness import (
    PAIR_SCENES,
    SceneSuite,
    build_context,
    suite_associations,
)

type HeatmapMode = Literal["wx-hour", "act-hour", "wx-act", "wx-doy", "act-doy", "hour-doy"]
type AxisName = Literal["weather", "hour", "activity", "day_of_year"]
type AxisValue = float | int | str | None

WEATHER_HEATMAP_PRESETS: tuple[str | None, ...] = (
    None,
    "clear",
    "overcast",
    "drizzle",
    "light_rain",
    "mod_rain",
    "heavy_rain",
    "violent_rain",
    "light_snow",
    "heavy_snow",
    "storm",
    "heavy_storm",
    "fog",
)


@dataclass(frozen=True)
class HeatmapCase:
    name: str
    mode: HeatmapMode
    fixed: dict[AxisName, AxisValue]


MODE_AXES: dict[HeatmapMode, tuple[AxisName, AxisName]] = {
    "wx-hour": ("hour", "weather"),
    "act-hour": ("hour", "activity"),
    "wx-act": ("activity", "weather"),
    "wx-doy": ("day_of_year", "weather"),
    "act-doy": ("day_of_year", "activity"),
    "hour-doy": ("hour", "day_of_year"),
}


@dataclass(frozen=True)
class HeatmapSampling:
    hour_step: float = 0.5
    day_step: int = 4
    activity_step: float = 0.05


@dataclass(frozen=True)
class HeatmapAxis:
    name: AxisName
    values: tuple[AxisValue, ...]

    @property
    def label(self) -> str:
        if self.name == "day_of_year":
            return "Day of year"
        return self.name.replace("_", " ").title()


@dataclass(frozen=True)
class HeatmapGrid:
    case: HeatmapCase
    x_axis: HeatmapAxis
    y_axis: HeatmapAxis
    # 行=y 轴序、列=x 轴序；各场景使用同一采样网格。
    probabilities: dict[str, np.ndarray]


@dataclass(frozen=True)
class FixedPoint:
    name: str
    value: AxisValue


def fixed_axis_points(config: SchedulerConfig) -> dict[AxisName, tuple[FixedPoint, ...]]:
    """Use adjacent peaks, a midpoint and one biased transition per fixed axis."""
    season = config.policies.season
    span = (season.summer_peak - season.spring_peak) % 365
    return {
        "day_of_year": (
            FixedPoint("haru_peak", season.spring_peak),
            FixedPoint("haru_bias", round(season.spring_peak + span / 4)),
            FixedPoint("haru_natsu", round(season.spring_peak + span / 2)),
            FixedPoint("natsu_peak", season.summer_peak),
        ),
        "hour": (FixedPoint("day_peak", 12.0), FixedPoint("day_bias", 13.5), FixedPoint("day_sunset", 15.0), FixedPoint("sunset_peak", 18.0)),
        "activity": (FixedPoint("work_peak", 1.0), FixedPoint("work_bias", 0.75), FixedPoint("work_mid", 0.5), FixedPoint("neutral", 0.0)),
        "weather": (
            FixedPoint("none", None),
            FixedPoint("light_rain", "light_rain"),
            FixedPoint("mod_rain", "mod_rain"),
            FixedPoint("heavy_rain", "heavy_rain"),
        ),
    }


def heatmap_cases(config: SchedulerConfig) -> tuple[HeatmapCase, ...]:
    """Combine the two remaining fixed axes in the same order for every mode."""
    points = fixed_axis_points(config)
    cases: list[HeatmapCase] = []
    for mode, scanned_axes in MODE_AXES.items():
        left_axis, right_axis = (axis for axis in points if axis not in scanned_axes)
        for left, right in product(points[left_axis], points[right_axis]):
            cases.append(HeatmapCase(f"{mode}-{left.name}-{right.name}", mode, {left_axis: left.value, right_axis: right.value}))
    return tuple(cases)


def evaluate_cases(
    config: SchedulerConfig,
    sampling: HeatmapSampling = HeatmapSampling(),
    modes: tuple[str, ...] | None = None,
    *,
    suite: SceneSuite = "product",
) -> dict[str, list[HeatmapGrid]]:
    """Evaluate every cell with the shared salience and probability calculation."""
    associations = suite_associations(config, suite)
    time_policy = TimePolicy(config.policies.time)
    season_policy = SeasonPolicy(config.policies.season)
    weather_policy = WeatherPolicy(config.policies.weather)
    temporal_items = (*VARIABLE_SEMANTIC_ITEMS[ContextVariable.SEASON], *VARIABLE_SEMANTIC_ITEMS[ContextVariable.TIME])
    weather_items = VARIABLE_SEMANTIC_ITEMS[ContextVariable.WEATHER]
    non_activity_items = (*temporal_items, *weather_items)

    @lru_cache(maxsize=8192)
    def temporal_salience(hour: float, day_of_year: int) -> tuple[float, ...]:
        context = build_context(hour, day_of_year, None)
        # Synthetic grids have fixed solar anchors and no observation history.
        values = {**time_policy.evaluate(context).salience, **season_policy.evaluate(context).salience}
        return tuple(values[item] for item in temporal_items)

    @lru_cache(maxsize=128)
    def weather_salience(weather_name: str | None) -> tuple[float, ...]:
        values = weather_policy.evaluate(build_context(12, 1, weather_name)).salience
        return tuple(values[item] for item in weather_items)

    @lru_cache(maxsize=4096)
    def distribution(values: tuple[float, ...], activity_salience: float) -> dict[str, float]:
        salience = dict(zip(non_activity_items, values))
        salience.update({SemanticItem.WORK: activity_salience, SemanticItem.LEISURE: -activity_salience})
        return calculate_distribution(Salience(salience), associations, config.matching).probabilities

    def evaluate(hour: float, day_of_year: int, weather_name: str | None, activity_salience: float) -> dict[str, float]:
        return distribution(temporal_salience(hour, day_of_year) + weather_salience(weather_name), activity_salience)

    scenes = list(associations)
    cases = heatmap_cases(config)

    selected = modes or ((suite.removeprefix("pair-"),) if suite in PAIR_SCENES else tuple(MODE_AXES))
    return {mode: [_evaluate_case(evaluate, case, sampling, scenes) for case in cases if case.mode == mode] for mode in selected}


def _evaluate_case(
    evaluate: Callable[[float, int, str | None, float], dict[str, float]],
    case: HeatmapCase,
    sampling: HeatmapSampling,
    scenes: list[str],
) -> HeatmapGrid:
    x_name, y_name = MODE_AXES[case.mode]
    x_axis = HeatmapAxis(x_name, _axis_values(x_name, sampling))
    y_axis = HeatmapAxis(y_name, _axis_values(y_name, sampling))
    shape = (len(y_axis.values), len(x_axis.values))
    probabilities = {scene: np.zeros(shape, dtype=float) for scene in scenes}

    for y_row, y_value in enumerate(y_axis.values):
        for x_col, x_value in enumerate(x_axis.values):
            values = dict(case.fixed)
            values[x_name] = x_value
            values[y_name] = y_value
            weather_name = values["weather"]
            distribution = evaluate(
                float(values["hour"]),
                int(values["day_of_year"]),
                None if weather_name is None else str(weather_name),
                float(values["activity"]),
            )
            for scene, probability in distribution.items():
                probabilities[scene][y_row, x_col] = probability
    return HeatmapGrid(case=case, x_axis=x_axis, y_axis=y_axis, probabilities=probabilities)


def _axis_values(axis_name: AxisName, sampling: HeatmapSampling) -> tuple[AxisValue, ...]:
    if axis_name == "weather":
        return WEATHER_HEATMAP_PRESETS
    if axis_name == "hour":
        return _float_axis(0.0, 24.0 - sampling.hour_step, sampling.hour_step)
    if axis_name == "activity":
        return _float_axis(-1.0, 1.0, sampling.activity_step)
    if axis_name == "day_of_year":
        values = list(range(1, 366, sampling.day_step))
        if values[-1] != 365:
            values.append(365)
        return tuple(values)
    raise ValueError(f"unknown heatmap axis: {axis_name}")


def _float_axis(start: float, stop: float, step: float) -> tuple[float, ...]:
    count = int(round((stop - start) / step))
    return tuple(round(start + index * step, 10) for index in range(count + 1))


# ── 渲染 ────────────────────────────────────────────────────────────

SCENE_COLORS: dict[str, str] = {
    # 工作用蓝色、娱乐用粉紫色；日间浅、夜间深。
    "day_work": "#74A9D4",
    "day_leisure": "#E9A3B2",
    "night_work": "#355782",
    "night_leisure": "#815C83",
    # 四季对应新绿、日光金、落叶赭与冰蓝，黄昏和雨景各取天空意象。
    "spring": "#79B77B",
    "summer": "#F2CA5B",
    "autumn": "#BC7A49",
    "winter": "#C7DFE5",
    "clear": "#68BAD0",
    "cloudy": "#A6ABB0",
    "rain": "#6E8E99",
    "dawn": "#E8B7A2",
    "day": "#F3D56B",
    "sunset": "#E58B62",
    "night": "#37416A",
    "work": "#477FAA",
    "leisure": "#AC76A0",
}


# 二项场景混合两个语义色，再略微压暗，与单项基线区分。
for _compounds in PAIR_SCENES.values():
    for _scene, _items in _compounds.items():
        if _scene in SCENE_COLORS:
            continue
        _rgb = np.mean([mpl_colors.to_rgb(SCENE_COLORS[item.value]) for item in sorted(_items)], axis=0) * 0.9
        SCENE_COLORS[_scene] = mpl_colors.to_hex(_rgb)

def render_mode_figures(
    grids_by_mode: dict[str, list[HeatmapGrid]],
    figures_dir: Path,
) -> list[Path]:
    """Write each mode's Scene probability maps and one winner map together.

    All probability maps use the same 0–100% scale.

    Raises:
        OSError: If an output directory or PNG cannot be written.
    """
    written: list[Path] = []
    for mode, grids in grids_by_mode.items():
        mode_dir = figures_dir / f"cur-{mode}"
        mode_dir.mkdir(parents=True, exist_ok=True)
        scene_ids = tuple(grids[0].probabilities)
        if scene_ids:
            written.extend(_render_mode_figures(grids, mode_dir, mode, scene_ids))
        written.extend(_render_mode_figures(grids, mode_dir, mode, (None,)))
    return written


def _render_mode_figures(grids: list[HeatmapGrid], figures_dir: Path, mode: str, scene_ids: tuple[str | None, ...]) -> list[Path]:
    """Reuse a mode's axes for probability maps, or draw its winner overview.

    Raises:
        OSError: If the output PNG cannot be written.
    """
    n_cases = len(grids)
    ncols = 4 if n_cases > 9 else 3
    nrows = math.ceil(n_cases / ncols)
    fig_w, fig_h = (ncols * 6.0, nrows * (5.5 if mode == "hour-doy" else 5.0))

    scene_id = scene_ids[0]
    fig, axes_array = plt.subplots(nrows, ncols, figsize=(fig_w, fig_h))
    title = fig.suptitle(scene_id if scene_id is not None else "Highest-probability Scene", fontsize=14)
    axes_flat = list(axes_array.flat)
    probability_maps: list[QuadMesh] = []

    for index, grid in enumerate(grids):
        axis = axes_flat[index]
        if scene_id is None:
            _draw_winner_map(axis, grid)
        else:
            probability_map = axis.pcolormesh(
                _axis_edges(grid.x_axis),
                _axis_edges(grid.y_axis),
                grid.probabilities[scene_id],
                cmap="Blues",
                vmin=0,
                vmax=1,
                shading="flat",
                rasterized=True,
            )
            probability_maps.append(probability_map)
        _style_axes(axis, grid)
        fixed = ", ".join(f"{key}={_value_label(value)}" for key, value in sorted(grid.case.fixed.items()))
        axis.set_title(f"{grid.case.name}\n{fixed}", fontsize=8, pad=4)
    for axis in axes_flat[n_cases:]:
        axis.set_visible(False)

    spacing_keys = ("left", "bottom", "right", "top", "wspace", "hspace")
    initial_spacing = {key: getattr(fig.subplotpars, key) for key in spacing_keys}
    layouts: dict[float, dict[str, float]] = {}
    title_heights: dict[str | None, float] = {}
    # tight_layout uses the suptitle's height; underscores can change it.
    for candidate in scene_ids:
        title.set_text(candidate if candidate is not None else "Highest-probability Scene")
        height = title.get_window_extent().height
        title_heights[candidate] = height
        if height not in layouts:
            fig.subplots_adjust(**initial_spacing)
            fig.tight_layout(rect=[0, 0.06, 1, 0.97])
            layouts[height] = {key: getattr(fig.subplotpars, key) for key in spacing_keys}
    if scene_id is None:
        handles = [patches.Patch(facecolor="#111827", label="no winner")]
        handles.extend(patches.Patch(facecolor=SCENE_COLORS[scene], label=scene) for scene in grids[0].probabilities)
        fig.legend(handles=handles, loc="lower center", ncol=5, frameon=True, fontsize=8, title="Scene")
    else:
        colorbar_axis = fig.add_axes([0.25, 0.035, 0.5, 0.012])
        colorbar = fig.colorbar(
            probability_map,
            cax=colorbar_axis,
            orientation="horizontal",
            ticks=np.linspace(0, 1, 6),
            format=PercentFormatter(1, decimals=0),
        )
        colorbar.set_label("Scene selection probability", fontsize=9)
        colorbar.ax.tick_params(labelsize=8)
    written: list[Path] = []
    try:
        for scene_id in scene_ids:
            fig.subplots_adjust(**layouts[title_heights[scene_id]])
            if scene_id is not None:
                title.set_text(scene_id)
                for probability_map, grid in zip(probability_maps, grids):
                    probability_map.set_array(grid.probabilities[scene_id])
            output_path = figures_dir / (f"{scene_id}.png" if scene_id is not None else "winner-map.png")
            fig.savefig(output_path, dpi=150, bbox_inches="tight")
            written.append(output_path)
    finally:
        plt.close(fig)
    return written


def _draw_winner_map(ax: Axes, grid: HeatmapGrid) -> None:
    winners = np.zeros((len(grid.y_axis.values), len(grid.x_axis.values)), dtype=int)
    if grid.probabilities:
        probabilities = np.stack(list(grid.probabilities.values()))
        winners = np.where(probabilities.max(axis=0) > 0, probabilities.argmax(axis=0) + 1, 0)
    colors = ["#111827", *(SCENE_COLORS[scene] for scene in grid.probabilities)]
    ax.pcolormesh(
        _axis_edges(grid.x_axis),
        _axis_edges(grid.y_axis),
        winners,
        cmap=mpl_colors.ListedColormap(colors),
        norm=mpl_colors.BoundaryNorm(np.arange(len(colors) + 1) - 0.5, len(colors)),
        shading="flat",
        rasterized=True,
    )


def _style_axes(ax: Axes, grid: HeatmapGrid) -> None:
    for orientation, axis in (("x", grid.x_axis), ("y", grid.y_axis)):
        _style_single_axis(ax, orientation, axis)
        line = ax.axvline if orientation == "x" else ax.axhline
        if axis.name == "hour":
            for hour in (6, 12, 18):
                line(hour, color="white", linewidth=0.6, linestyle="--", alpha=0.45)
        elif axis.name == "activity":
            line(0, color="white", linewidth=0.8, linestyle="--", alpha=0.65)


def _style_single_axis(ax: Axes, orientation: Literal["x", "y"], axis: HeatmapAxis) -> None:
    if orientation == "x":
        set_label, set_limits, set_ticks, set_ticklabels = ax.set_xlabel, ax.set_xlim, ax.set_xticks, ax.set_xticklabels
    else:
        set_label, set_limits, set_ticks, set_ticklabels = ax.set_ylabel, ax.set_ylim, ax.set_yticks, ax.set_yticklabels
    set_label(axis.label)
    if axis.name == "weather":
        ticks = [index + 0.5 for index in range(len(axis.values))]
        labels = [_value_label(value) for value in axis.values]
    elif axis.name == "hour":
        set_limits(0, 24)
        ticks = list(range(0, 25, 4))
        labels = [f"{hour:02d}:00" for hour in ticks]
    elif axis.name == "activity":
        set_limits(-1, 1)
        ticks = [-1, -0.5, 0, 0.5, 1]
        labels = ["leisure 1.0", "0.5", "neutral", "0.5", "work 1.0"]
    else:
        set_limits(1, 365)
        ticks = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    set_ticks(ticks)
    if axis.name == "weather" and orientation == "x":
        set_ticklabels(labels, rotation=35, ha="right", fontsize=8)
    else:
        set_ticklabels(labels, fontsize=8)
    if orientation == "y" and axis.name in ("weather", "day_of_year"):
        ax.invert_yaxis()


def _axis_edges(axis: HeatmapAxis) -> np.ndarray:
    values = axis.values
    if axis.name == "weather":
        return np.arange(len(values) + 1)
    numeric = [float(value) for value in values]
    if axis.name == "hour":
        step = numeric[1] - numeric[0] if len(numeric) > 1 else 1.0
        return np.append(np.array(numeric), numeric[-1] + step)
    if axis.name == "activity":
        return _midpoint_edges(numeric, -1.0, 1.0)
    if axis.name == "day_of_year":
        return _midpoint_edges(numeric, 1.0, 365.0)
    raise ValueError(f"unknown heatmap axis: {axis.name}")


def _midpoint_edges(values: list[float], lower: float, upper: float) -> np.ndarray:
    if len(values) == 1:
        return np.array([lower, upper])
    mids = [(left + right) / 2 for left, right in zip(values, values[1:])]
    return np.array([lower, *mids, upper])


def _value_label(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


__all__ = [
    "MODE_AXES",
    "HeatmapCase",
    "HeatmapGrid",
    "HeatmapSampling",
    "evaluate_cases",
    "fixed_axis_points",
    "heatmap_cases",
    "render_mode_figures",
]
