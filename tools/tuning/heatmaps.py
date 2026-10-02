"""第一轮 Scene 调参热图——完全沿用 legacytuning 的出图范式。

六种模式（wx-hour / act-hour / wx-act / wx-doy / act-doy / hour-doy）、同一份
case 目录、每模式一张聚合 winner 图：场景各自配色 + "no winner" 深色、
pcolormesh 平铺、白色虚线参考线、月份刻度。差异只在数据源：真实
ProfileCompiler/POLICY_REGISTRY/Matcher 取代旧工具复制的管线，playlist 换成
Scene，gamma 特性按裁定舍弃。
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mpl_colors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

from configurations.runtime_models import SchedulerConfig
from core.models.scene import SceneId
from tools.tuning.harness import (
    build_context,
    build_matcher,
    coerce_activity,
    prime_activity,
)

type HeatmapMode = Literal["wx-hour", "act-hour", "wx-act", "wx-doy", "act-doy", "hour-doy"]
type AxisName = Literal["weather", "hour", "activity", "day_of_year"]

WEATHER_HEATMAP_PRESETS: tuple[str | None, ...] = (
    None,
    "clear",
    "overcast",
    "drizzle",
    "mod_rain",
    "heavy_rain",
    "light_snow",
    "heavy_snow",
    "storm",
    "heavy_storm",
    "fog",
)

# legacytuning 的 case 目录原样移植；季节词 haru/natsu/aki/fuyu 与跨季边界日
# （fuyu-haru=35 等）沿用旧命名，便于和旧图对照。
@dataclass(frozen=True)
class HeatmapCase:
    name: str
    mode: str
    fixed: dict[str, object]


DEFAULT_HEATMAP_CASES: tuple[HeatmapCase, ...] = (
    HeatmapCase("wxhr-idle-haru", "wx-hour", {"activity": None, "day_of_year": 80}),
    HeatmapCase("wxhr-idle-natsu", "wx-hour", {"activity": None, "day_of_year": 172}),
    HeatmapCase("wxhr-idle-aki", "wx-hour", {"activity": None, "day_of_year": 265}),
    HeatmapCase("wxhr-idle-fuyu", "wx-hour", {"activity": None, "day_of_year": 355}),
    HeatmapCase("wxhr-idle-fuyu-haru", "wx-hour", {"activity": None, "day_of_year": 35}),
    HeatmapCase("wxhr-idle-haru-natsu", "wx-hour", {"activity": None, "day_of_year": 126}),
    HeatmapCase("wxhr-idle-natsu-aki", "wx-hour", {"activity": None, "day_of_year": 218}),
    HeatmapCase("wxhr-idle-aki-fuyu", "wx-hour", {"activity": None, "day_of_year": 310}),
    HeatmapCase("wxhr-focus-haru", "wx-hour", {"activity": "#focus", "day_of_year": 80}),
    HeatmapCase("wxhr-focus-natsu", "wx-hour", {"activity": "#focus", "day_of_year": 172}),
    HeatmapCase("wxhr-chill-natsu", "wx-hour", {"activity": "#chill", "day_of_year": 172}),
    HeatmapCase("wxhr-chill-fuyu", "wx-hour", {"activity": "#chill", "day_of_year": 355}),
    HeatmapCase("acthr-none-haru", "act-hour", {"weather": None, "day_of_year": 80}),
    HeatmapCase("acthr-none-natsu-aki", "act-hour", {"weather": None, "day_of_year": 218}),
    HeatmapCase("acthr-none-fuyu", "act-hour", {"weather": None, "day_of_year": 355}),
    HeatmapCase("acthr-clear-haru", "act-hour", {"weather": "clear", "day_of_year": 80}),
    HeatmapCase("acthr-clear-haru-natsu", "act-hour", {"weather": "clear", "day_of_year": 126}),
    HeatmapCase("acthr-clear-natsu", "act-hour", {"weather": "clear", "day_of_year": 172}),
    HeatmapCase("acthr-clear-fuyu", "act-hour", {"weather": "clear", "day_of_year": 355}),
    HeatmapCase("acthr-rain-natsu", "act-hour", {"weather": "mod_rain", "day_of_year": 172}),
    HeatmapCase("acthr-rain-aki-fuyu", "act-hour", {"weather": "mod_rain", "day_of_year": 310}),
    HeatmapCase("acthr-storm-fuyu-haru", "act-hour", {"weather": "storm", "day_of_year": 35}),
    HeatmapCase("acthr-storm-haru", "act-hour", {"weather": "storm", "day_of_year": 80}),
    HeatmapCase("acthr-storm-fuyu", "act-hour", {"weather": "storm", "day_of_year": 355}),
    HeatmapCase("wxdoy-idle-06", "wx-doy", {"activity": None, "hour": 6.0}),
    HeatmapCase("wxdoy-idle-10", "wx-doy", {"activity": None, "hour": 10.0}),
    HeatmapCase("wxdoy-idle-14", "wx-doy", {"activity": None, "hour": 14.0}),
    HeatmapCase("wxdoy-idle-18", "wx-doy", {"activity": None, "hour": 18.0}),
    HeatmapCase("wxdoy-idle-22", "wx-doy", {"activity": None, "hour": 22.0}),
    HeatmapCase("wxdoy-focus-10", "wx-doy", {"activity": "#focus", "hour": 10.0}),
    HeatmapCase("wxdoy-focus-22", "wx-doy", {"activity": "#focus", "hour": 22.0}),
    HeatmapCase("wxdoy-chill-14", "wx-doy", {"activity": "#chill", "hour": 14.0}),
    HeatmapCase("wxdoy-chill-20", "wx-doy", {"activity": "#chill", "hour": 20.0}),
    HeatmapCase("actdoy-none-10", "act-doy", {"weather": None, "hour": 10.0}),
    HeatmapCase("actdoy-none-22", "act-doy", {"weather": None, "hour": 22.0}),
    HeatmapCase("actdoy-clear-10", "act-doy", {"weather": "clear", "hour": 10.0}),
    HeatmapCase("actdoy-clear-14", "act-doy", {"weather": "clear", "hour": 14.0}),
    HeatmapCase("actdoy-clear-22", "act-doy", {"weather": "clear", "hour": 22.0}),
    HeatmapCase("actdoy-rain-10", "act-doy", {"weather": "mod_rain", "hour": 10.0}),
    HeatmapCase("actdoy-rain-22", "act-doy", {"weather": "mod_rain", "hour": 22.0}),
    HeatmapCase("actdoy-storm-14", "act-doy", {"weather": "storm", "hour": 14.0}),
    HeatmapCase("actdoy-storm-22", "act-doy", {"weather": "storm", "hour": 22.0}),
    HeatmapCase("wxact-haru-08", "wx-act", {"hour": 8.0, "day_of_year": 80}),
    HeatmapCase("wxact-haru-20", "wx-act", {"hour": 20.0, "day_of_year": 80}),
    HeatmapCase("wxact-natsu-14", "wx-act", {"hour": 14.0, "day_of_year": 172}),
    HeatmapCase("wxact-natsu-23", "wx-act", {"hour": 23.0, "day_of_year": 172}),
    HeatmapCase("wxact-aki-14", "wx-act", {"hour": 14.0, "day_of_year": 265}),
    HeatmapCase("wxact-aki-23", "wx-act", {"hour": 23.0, "day_of_year": 265}),
    HeatmapCase("wxact-fuyu-20", "wx-act", {"hour": 20.0, "day_of_year": 355}),
    HeatmapCase("wxact-fuyu-23", "wx-act", {"hour": 23.0, "day_of_year": 355}),
    HeatmapCase("wxact-fuyu-haru-14", "wx-act", {"hour": 14.0, "day_of_year": 35}),
    HeatmapCase("wxact-haru-natsu-14", "wx-act", {"hour": 14.0, "day_of_year": 126}),
    HeatmapCase("wxact-natsu-aki-14", "wx-act", {"hour": 14.0, "day_of_year": 218}),
    HeatmapCase("wxact-aki-fuyu-14", "wx-act", {"hour": 14.0, "day_of_year": 310}),
    HeatmapCase("hrdoy-idle-none", "hour-doy", {"activity": None, "weather": None}),
    HeatmapCase("hrdoy-idle-clear", "hour-doy", {"activity": None, "weather": "clear"}),
    HeatmapCase("hrdoy-idle-drizzle", "hour-doy", {"activity": None, "weather": "drizzle"}),
    HeatmapCase("hrdoy-idle-snow", "hour-doy", {"activity": None, "weather": "heavy_snow"}),
    HeatmapCase("hrdoy-focus-clear", "hour-doy", {"activity": "#focus", "weather": "clear"}),
    HeatmapCase("hrdoy-chill-clear", "hour-doy", {"activity": "#chill", "weather": "clear"}),
    HeatmapCase("hrdoy-focus-cloud", "hour-doy", {"activity": "#focus", "weather": "overcast"}),
    HeatmapCase("hrdoy-focus-rain", "hour-doy", {"activity": "#focus", "weather": "mod_rain"}),
    HeatmapCase("hrdoy-chill-rain", "hour-doy", {"activity": "#chill", "weather": "mod_rain"}),
)

_MODE_TO_AXES: dict[str, tuple[AxisName, AxisName]] = {
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
    values: tuple[float | int | str | None, ...]

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
    fixed: dict[str, object]
    # 行=y 轴序、列=x 轴序；值为场景索引+1，0=no winner。
    winner_indices: np.ndarray


_MODE_CASES: dict[str, list[HeatmapCase]] = {}
for _case in DEFAULT_HEATMAP_CASES:
    _MODE_CASES.setdefault(_case.mode, []).append(_case)


def evaluate_cases(
    config: SchedulerConfig,
    sampling: HeatmapSampling = HeatmapSampling(),
    modes: tuple[str, ...] | None = None,
) -> dict[str, list[tuple[HeatmapCase, HeatmapGrid]]]:
    """Run every case of the selected modes through the real match pipeline."""
    matcher = build_matcher(config)
    scenes = list(SceneId)
    index_by_scene = {scene: index + 1 for index, scene in enumerate(scenes)}
    min_similarity = matcher.pool_params.min_similarity

    selected = modes or tuple(_MODE_CASES)
    result: dict[str, list[tuple[HeatmapCase, HeatmapGrid]]] = {}
    for mode in selected:
        grids: list[tuple[HeatmapCase, HeatmapGrid]] = []
        for case in _MODE_CASES[mode]:
            grid = _evaluate_case(config, matcher, case, sampling, scenes, index_by_scene, min_similarity)
            grids.append((case, grid))
        result[mode] = grids
    return result


def _evaluate_case(
    config: SchedulerConfig,
    matcher,
    case: HeatmapCase,
    sampling: HeatmapSampling,
    scenes: list[SceneId],
    index_by_scene: dict[SceneId, int],
    min_similarity: float,
) -> HeatmapGrid:
    x_name, y_name = _MODE_TO_AXES[case.mode]
    x_axis = HeatmapAxis(x_name, _axis_values(x_name, sampling))
    y_axis = HeatmapAxis(y_name, _axis_values(y_name, sampling))
    winners = np.zeros((len(y_axis.values), len(x_axis.values)), dtype=float)

    for y_row, y_value in enumerate(y_axis.values):
        for x_col, x_value in enumerate(x_axis.values):
            values = dict(case.fixed)
            values[x_name] = x_value
            values[y_name] = y_value
            activity_tag, strength = coerce_activity(values.get("activity"))
            weather_name = values.get("weather")
            context = build_context(
                hour=float(values["hour"]),
                day_of_year=int(values["day_of_year"]),
                weather_name=None if weather_name is None else str(weather_name),
                activity_tag=activity_tag,
                activity_strength=strength,
            )
            prime_activity(matcher, config, activity_tag, strength)
            match = matcher.match(context)
            if match.scene_matches and match.scene_matches[0][1] > min_similarity:
                winners[y_row, x_col] = index_by_scene[match.scene_matches[0][0]]
    return HeatmapGrid(case=case, x_axis=x_axis, y_axis=y_axis, fixed=dict(case.fixed), winner_indices=winners)


def _axis_values(axis_name: AxisName, sampling: HeatmapSampling) -> tuple[float | int | str | None, ...]:
    if axis_name == "weather":
        return WEATHER_HEATMAP_PRESETS
    if axis_name == "hour":
        return tuple(_float_axis(0.0, 24.0 - sampling.hour_step, sampling.hour_step))
    if axis_name == "activity":
        return tuple(_float_axis(-1.0, 1.0, sampling.activity_step))
    if axis_name == "day_of_year":
        values = list(range(1, 366, sampling.day_step))
        if values[-1] != 365:
            values.append(365)
        return tuple(values)
    raise ValueError(f"unknown heatmap axis: {axis_name}")


def _float_axis(start: float, stop: float, step: float) -> list[float]:
    count = int(round((stop - start) / step))
    return [round(start + index * step, 10) for index in range(count + 1)]


# ── 渲染 ────────────────────────────────────────────────────────────

SCENE_COLORS: dict[SceneId, str] = {
    SceneId.DAY_WORK: "#1f77b4",
    SceneId.DAY_LEISURE: "#ff7f0e",
    SceneId.NIGHT_WORK: "#2ca02c",
    SceneId.NIGHT_LEISURE: "#d62728",
    SceneId.SPRING: "#9467bd",
    SceneId.SUMMER: "#8c564b",
    SceneId.AUTUMN: "#e377c2",
    SceneId.WINTER: "#7f7f7f",
    SceneId.SUNSET: "#bcbd22",
    SceneId.RAIN: "#17becf",
}


def render_mode_figures(
    config: SchedulerConfig,
    grids_by_mode: dict[str, list[tuple[HeatmapCase, HeatmapGrid]]],
    figures_dir: Path,
) -> list[Path]:
    """One aggregated winner-map PNG per mode, legacytuning layout."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for mode, grids in grids_by_mode.items():
        output_path = figures_dir / f"cur-{mode}.png"
        _render_mode_figure(grids, output_path, mode)
        written.append(output_path)
    return written


def _render_mode_figure(grids: list[tuple[HeatmapCase, HeatmapGrid]], output_path: Path, mode: str) -> None:
    n_cases = len(grids)
    ncols = 4 if n_cases > 9 else 3
    nrows = math.ceil(n_cases / ncols)
    fig_w, fig_h = (ncols * 6.0, nrows * (5.5 if mode == "hour-doy" else 5.0))

    fig, axes_array = plt.subplots(nrows, ncols, figsize=(fig_w, fig_h))
    axes_flat = [axes_array] if not hasattr(axes_array, "flat") else list(axes_array.flat)

    for index, (case, grid) in enumerate(grids):
        axis = axes_flat[index]
        _draw_winner_map(axis, grid)
        _style_axes(axis, grid)
        fixed = ", ".join(f"{key}={_value_label(value)}" for key, value in sorted(grid.fixed.items()))
        axis.set_title(f"{case.name}\n{fixed}", fontsize=8, pad=4)
    for axis in axes_flat[n_cases:]:
        axis.set_visible(False)

    _add_winner_legend(fig)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _draw_winner_map(ax, grid: HeatmapGrid) -> None:
    scenes = list(SceneId)
    colors = ["#111827", *(SCENE_COLORS[scene] for scene in scenes)]
    cmap = mpl_colors.ListedColormap(colors)
    norm = mpl_colors.BoundaryNorm(np.arange(len(colors) + 1) - 0.5, len(colors))
    ax.pcolormesh(
        _axis_edges(grid.x_axis),
        _axis_edges(grid.y_axis),
        grid.winner_indices,
        cmap=cmap,
        norm=norm,
        shading="flat",
        rasterized=True,
    )


def _style_axes(ax, grid: HeatmapGrid) -> None:
    _style_single_axis(ax, "x", grid.x_axis)
    _style_single_axis(ax, "y", grid.y_axis)
    if grid.x_axis.name == "hour":
        for hour in (8, 14, 20, 23):
            ax.axvline(hour, color="white", linewidth=0.6, linestyle="--", alpha=0.45)
    if grid.y_axis.name == "hour":
        for hour in (8, 14, 20, 23):
            ax.axhline(hour, color="white", linewidth=0.6, linestyle="--", alpha=0.45)
    if grid.x_axis.name == "activity":
        ax.axvline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.65)
    if grid.y_axis.name == "activity":
        ax.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.65)


def _style_single_axis(ax, orientation: Literal["x", "y"], axis: HeatmapAxis) -> None:
    values = axis.values
    setter_label = ax.set_xlabel if orientation == "x" else ax.set_ylabel
    setter_label(axis.label)
    if axis.name == "weather":
        ticks = [index + 0.5 for index in range(len(values))]
        labels = [_value_label(value) for value in values]
        if orientation == "x":
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        else:
            ax.set_yticks(ticks)
            ax.set_yticklabels(labels, fontsize=8)
            ax.invert_yaxis()
        return
    if axis.name == "hour":
        ticks = list(range(0, 25, 4))
        labels = [f"{hour:02d}:00" for hour in ticks]
        if orientation == "x":
            ax.set_xlim(0, 24)
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, fontsize=8)
        else:
            ax.set_ylim(0, 24)
            ax.set_yticks(ticks)
            ax.set_yticklabels(labels, fontsize=8)
        return
    if axis.name == "activity":
        ticks = [-1, -0.5, 0, 0.5, 1]
        labels = ["chill 1.0", "0.5", "idle", "0.5", "focus 1.0"]
        if orientation == "x":
            ax.set_xlim(-1, 1)
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, fontsize=8)
        else:
            ax.set_ylim(-1, 1)
            ax.set_yticks(ticks)
            ax.set_yticklabels(labels, fontsize=8)
        return
    if axis.name == "day_of_year":
        ticks = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if orientation == "x":
            ax.set_xlim(1, 365)
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, fontsize=8)
        else:
            ax.set_ylim(1, 365)
            ax.set_yticks(ticks)
            ax.set_yticklabels(labels, fontsize=8)
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


def _add_winner_legend(fig) -> None:
    handles = [patches.Patch(facecolor=color, label=scene.value) for scene, color in SCENE_COLORS.items()]
    handles.insert(0, patches.Patch(facecolor="#111827", label="no winner"))
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=min(5, len(handles)),
        frameon=True,
        fontsize=8,
        title="Scene",
    )


def _value_label(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


__all__ = [
    "DEFAULT_HEATMAP_CASES",
    "HeatmapCase",
    "HeatmapGrid",
    "HeatmapSampling",
    "SCENE_COLORS",
    "evaluate_cases",
    "render_mode_figures",
]
