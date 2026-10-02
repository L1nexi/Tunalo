"""第一轮 Scene 调参扫描：legacytuning 的 case 目录 × 真实匹配管线。

对每个模式输出一张聚合 winner 热图（cur-<mode>.png）。用法::

    python tools/tuning/scan.py [--mode wx-hour ...] [--out runs/<name>]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.tuning.heatmaps import DEFAULT_HEATMAP_CASES, evaluate_cases, render_mode_figures
from tools.tuning.harness import synthetic_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Round-1 scene tuning scan (legacytuning paradigm)")
    parser.add_argument(
        "--mode",
        action="append",
        choices=sorted({case.mode for case in DEFAULT_HEATMAP_CASES}),
        help="restrict to one heatmap mode (repeatable); default renders all six",
    )
    parser.add_argument("--out", default=None, help="output dir under tools/tuning/runs/")
    args = parser.parse_args()

    run_name = args.out or datetime.now().strftime("run-%Y%m%d-%H%M%S")
    out_dir = Path(__file__).resolve().parent / "runs" / run_name

    config = synthetic_config()
    grids_by_mode = evaluate_cases(config, modes=tuple(args.mode) if args.mode else None)
    for path in render_mode_figures(config, grids_by_mode, out_dir):
        print(f"written: {path}")

    cell_total = sum(
        grid.winner_indices.size
        for grids in grids_by_mode.values()
        for _, grid in grids
    )
    print(f"cells evaluated: {cell_total}")
    print(f"output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
