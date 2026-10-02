"""第一轮调参出图：每场景得分面 + winner map + 池大小。

所有场景共用同一色标，保证跨场景可比；绘图方案细节按裁定留到下一阶段，
这里只做最小可读版本（英文标签，避开 CJK 字体问题）。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from core.models.scene import SceneId

_SCENE_ORDER: list[SceneId] = list(SceneId)
_COLORMAP = ListedColormap(plt.get_cmap("tab10").colors[: len(_SCENE_ORDER)])


def _scene_index(scene_id: SceneId) -> int:
    return _SCENE_ORDER.index(scene_id)


def plot_grid(result, out_dir: Path) -> list[Path]:
    """Write the winner/pool figure and the per-scene surfaces for one preset."""
    out_dir.mkdir(parents=True, exist_ok=True)
    hours = result.hours
    days = result.days
    extent = [hours[0] - 0.5, hours[-1] + 0.5, days[-1], days[0]]
    written: list[Path] = []

    # ── winner map + pool size ──────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    winner_image = axes[0].imshow(
        result.winners, aspect="auto", extent=extent, cmap=_COLORMAP, vmin=0, vmax=len(_SCENE_ORDER) - 1, interpolation="nearest"
    )
    axes[0].set_title(f"{result.preset.name} — winner scene")
    axes[0].set_ylabel("day of year")
    axes[1].imshow(result.pool_sizes, aspect="auto", extent=extent, cmap="viridis", vmin=1, vmax=3, interpolation="nearest")
    axes[1].set_title("pool size")
    axes[1].set_xlabel("hour")
    axes[1].set_ylabel("day of year")
    fig.legend(
        handles=[Patch(facecolor=_COLORMAP(i), label=scene.value) for i, scene in enumerate(_SCENE_ORDER)],
        loc="center right",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0, 0.86, 1))
    winner_path = out_dir / f"{result.preset.name}_winner_pool.png"
    fig.savefig(winner_path, dpi=130)
    plt.close(fig)
    written.append(winner_path)

    # ── per-scene score surfaces, shared color scale ───────────────
    shared_max = max(float(np.max(values)) for values in result.scores.values())
    fig, axes = plt.subplots(5, 2, figsize=(11, 13), sharex=True, sharey=True)
    for axis, scene in zip(axes.flat, _SCENE_ORDER):
        image = axis.imshow(result.scores[scene], aspect="auto", extent=extent, cmap="magma", vmin=0.0, vmax=shared_max, interpolation="nearest")
        axis.set_title(scene.value, fontsize=9)
    for axis in axes[-1]:
        axis.set_xlabel("hour")
    for axis in axes[:, 0]:
        axis.set_ylabel("day of year")
    fig.colorbar(image, ax=axes, label="cosine similarity", fraction=0.025)
    fig.suptitle(f"{result.preset.name} — per-scene score surfaces (shared scale 0–{shared_max:.2f})")
    surfaces_path = out_dir / f"{result.preset.name}_scene_surfaces.png"
    fig.savefig(surfaces_path, dpi=130)
    plt.close(fig)
    written.append(surfaces_path)

    return written
