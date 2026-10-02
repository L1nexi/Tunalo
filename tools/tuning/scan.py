"""第一轮 Scene 调参扫描：固定情境预设 × hour×day_of_year 网格。

对每个情境输出 winner map + 池大小 + 每场景得分面，并打印 winner 分布汇总。
用法::

    python tools/tuning/scan.py [--out runs/<name>]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from tools.tuning.harness import ContextPreset, build_context, match_once, synthetic_config
from tools.tuning.plotting import _SCENE_ORDER, plot_grid

_PRESETS = [
    ContextPreset("clear_idle", weather_id=800, weather_main="Clear", activity=""),
    ContextPreset("clear_focus", weather_id=800, weather_main="Clear", activity="focus"),
    ContextPreset("rain_idle", weather_id=501, weather_main="Rain", activity=""),
]
_HOURS = range(24)
_DAYS = range(1, 366, 3)


def scan_preset(config, preset: ContextPreset):
    """Scan one preset over the hour×day grid; returns arrays for plotting."""
    scores = {scene: np.zeros((len(_DAYS), len(_HOURS))) for scene in _SCENE_ORDER}
    pool_sizes = np.zeros((len(_DAYS), len(_HOURS)), dtype=int)
    winners = np.zeros((len(_DAYS), len(_HOURS)), dtype=int)

    for day_index, day in enumerate(_DAYS):
        for hour_index, hour in enumerate(_HOURS):
            match = match_once(config, build_context(preset, hour, day))
            lookup = dict(match.scene_matches)
            for scene, score in lookup.items():
                scores[scene][day_index, hour_index] = score
            pool_sizes[day_index, hour_index] = len(match.best_scenes)
            if match.scene_matches:
                winners[day_index, hour_index] = _SCENE_ORDER.index(match.scene_matches[0][0])

    class _Result:  # 轻量容器，避免为一次扫描引入 dataclass 样板
        pass

    result = _Result()
    result.preset = preset
    result.hours = list(_HOURS)
    result.days = list(_DAYS)
    result.scores = scores
    result.pool_sizes = pool_sizes
    result.winners = winners
    return result


def summarize(result) -> str:
    counts = Counter(_SCENE_ORDER[index].value for index in result.winners.flat)
    total = int(result.winners.size)
    lines = [f"[{result.preset.name}] mean pool size: {result.pool_sizes.mean():.2f}"]
    for scene in _SCENE_ORDER:
        share = counts.get(scene.value, 0) / total * 100
        bar = "#" * round(share / 2)
        lines.append(f"  {scene.value:<13} {share:5.1f}% {bar}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Round-1 scene tuning scan")
    parser.add_argument("--out", default=None, help="output dir under tools/tuning/runs/")
    args = parser.parse_args()

    run_name = args.out or datetime.now().strftime("run-%Y%m%d-%H%M%S")
    out_dir = Path(__file__).resolve().parent / "runs" / run_name

    config = synthetic_config()
    for preset in _PRESETS:
        result = scan_preset(config, preset)
        for path in plot_grid(result, out_dir):
            print(f"written: {path.relative_to(out_dir.parents[2])}")
        print(summarize(result))
        print()
    print(f"output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
