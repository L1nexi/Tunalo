r"""扫描场景概率，输出逐场景热图、胜者图与完整概率数据。

在仓库根目录运行：

单语义项 suite，扫描全部六种模式，使用 alpha=2、默认相位映射、当前边界 +0.9 / -0.1：
    .\.venv\Scripts\python.exe tools/tuning/scan.py --suite single --curve current --alpha 2 --out single-power-alpha2-gamma2-p0.9-n0.1

六套二项复合 suite，各自扫描对应的两条轴：
    .\.venv\Scripts\python.exe tools/tuning/scan.py --suite pairs --curve current --alpha 2 --out pairs-power-alpha2-gamma2-p0.9-n0.1

只扫描天气×活动的二项 suite：
    .\.venv\Scripts\python.exe tools/tuning/scan.py --suite pair-wx-act --alpha 2 --out pairs-power-alpha2-gamma2-p0.9-n0.1

只扫描单语义项 suite 的活动×日期模式，并比较 alpha=1.5（--mode 可以重复指定）：
    .\.venv\Scripts\python.exe tools/tuning/scan.py --suite single --alpha 1.5 --mode act-doy --out single-act-doy-alpha1.5

完整支持轴上的 Hann 对照：
    .\.venv\Scripts\python.exe tools/tuning/scan.py --suite single --curve hann --out single-hann-full-axis

产品场景，使用当前生产曲线：
    .\.venv\Scripts\python.exe tools/tuning/scan.py --suite product --curve current --out product-current

输出目录：tools/tuning/runs/<out>/<suite>/cur-<mode>/。
每个 suite 的 distributions.json 保存场景关联、参数和完整概率。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from contextlib import nullcontext
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.tuning.harness import PAIR_SCENES, SceneSuite, suite_associations, synthetic_config
from tools.tuning.heatmaps import MODE_AXES, HeatmapSampling, evaluate_cases, fixed_axis_points, render_mode_figures


def hann_activation(value: float, alpha: float = 2.0) -> float:
    """Use Hann on the complete [-1, 1] support axis; alpha is unused."""
    return math.sin(math.pi * value / 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scene probability calibration scan")
    parser.add_argument(
        "--suite",
        choices=("single", "product", "pairs", *PAIR_SCENES),
        default="single",
        help="single semantics (default), product presets, one pair suite, or all six pairs",
    )
    parser.add_argument(
        "--curve", choices=("current", "hann"), default="current", help="periodic activation: symmetric power (default) or full-axis Hann comparison"
    )
    parser.add_argument("--alpha", type=float, default=2.0, help="Time/Season power-curve exponent (>1, default 2); unused by Hann")
    parser.add_argument(
        "--mode",
        action="append",
        choices=sorted(MODE_AXES),
        help="override the suite's default scan modes (repeatable); pair suites default to their corresponding two axes",
    )
    parser.add_argument("--out", default=None, help="output dir under tools/tuning/runs/")
    args = parser.parse_args()

    run_name = args.out or datetime.now().strftime("run-%Y%m%d-%H%M%S")
    run_dir = Path(__file__).resolve().parent / "runs" / run_name
    suites: tuple[SceneSuite, ...] = tuple(PAIR_SCENES) if args.suite == "pairs" else (args.suite,)
    config = synthetic_config(activation_alpha=args.alpha)
    sampling = HeatmapSampling()
    for suite in suites:
        out_dir = run_dir / suite
        # Hann is an isolated calibration experiment, using the real periodic Policies.
        with patch("core.math_utils.salience_activation", hann_activation) if args.curve == "hann" else nullcontext():
            grids_by_mode = evaluate_cases(config, sampling, modes=tuple(args.mode) if args.mode else None, suite=suite)
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "suite": suite,
            "curve": args.curve,
            "alpha": args.alpha,
            "periodic_policies": {"time": config.policies.time.model_dump(), "season": config.policies.season.model_dump()},
            "scenes": {scene: sorted(item.value for item in items) for scene, items in suite_associations(config, suite).items()},
            "sampling": asdict(sampling),
            "fixed_points": {axis: [asdict(point) for point in points] for axis, points in fixed_axis_points(config).items()},
            "matching": config.matching.model_dump(mode="json"),
            "activity_axis": "signed focus salience; chill is its opposite",
            "grids": [
                {
                    "case": case.name,
                    "fixed": grid.fixed,
                    "x": {"name": grid.x_axis.name, "values": grid.x_axis.values},
                    "y": {"name": grid.y_axis.name, "values": grid.y_axis.values},
                    "probabilities": {scene: values.tolist() for scene, values in grid.probabilities.items()},
                }
                for grids in grids_by_mode.values()
                for case, grid in grids
            ],
        }
        (out_dir / "distributions.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        paths = render_mode_figures(grids_by_mode, out_dir)
        cell_total = sum(len(grid.x_axis.values) * len(grid.y_axis.values) for grids in grids_by_mode.values() for _, grid in grids)
        print(f"{suite}: rendered {len(paths)} images; evaluated {cell_total} cells; output: {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
