"""Render calibration grids and export their complete probability distributions."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.tuning.harness import synthetic_config
from tools.tuning.heatmaps import DEFAULT_HEATMAP_CASES, evaluate_cases, render_mode_figures


def main() -> int:
    parser = argparse.ArgumentParser(description="Scene probability calibration scan")
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
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "matching": config.matching.model_dump(mode="json"),
        "activity_axis": "signed focus salience; chill is its opposite",
        "grids": [
            {
                "case": case.name,
                "fixed": grid.fixed,
                "x": {"name": grid.x_axis.name, "values": grid.x_axis.values},
                "y": {"name": grid.y_axis.name, "values": grid.y_axis.values},
                "probabilities": {scene.value: values.tolist() for scene, values in grid.probabilities.items()},
            }
            for grids in grids_by_mode.values()
            for case, grid in grids
        ],
    }
    (out_dir / "distributions.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    for path in render_mode_figures(config, grids_by_mode, out_dir):
        print(f"written: {path}")

    cell_total = sum(grid.winner_indices.size for grids in grids_by_mode.values() for _, grid in grids)
    print(f"cells evaluated: {cell_total}")
    print(f"output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
