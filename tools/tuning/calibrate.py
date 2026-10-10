"""Export curves and an observation replay using the implemented public inputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.models.context import WindowData
from core.policies.activity import ActivityPolicy
from core.policies.season import SeasonPolicy
from core.policies.time import TimePolicy
from tools.tuning.harness import build_context, build_selector, synthetic_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Export product salience curves and full Scene distributions")
    parser.add_argument("--out", type=Path, default=Path("tools/tuning/runs/model-calibration"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = synthetic_config()
    activity = ActivityPolicy(config.policies.activity)
    season = SeasonPolicy(config.policies.season)
    time_policy = TimePolicy(config.policies.time)
    selector = build_selector(config)
    activity_rows: list[dict[str, float | int]] = [{"slot": 0, "focus": 0, "chill": 0}]
    replay: list[dict[str, object]] = []
    for slot in range(1, 1801):
        context = build_context(12, 172, "violent_rain")
        context.window = WindowData(process="code.exe" if slot <= 600 else "vlc.exe" if slot <= 1200 else "chrome.exe")
        evaluation = activity.evaluate(context)
        selection = selector.select(context)
        activity_rows.append({"slot": slot, **evaluation.salience})
        replay.append(
            {
                "slot": slot,
                "process": context.window.process,
                "salience": selection.salience,
                "probabilities": selection.probabilities,
                "reason": selection.reason,
            }
        )
    season_rows = [{"day": day, **season.evaluate(build_context(12, day, None)).salience} for day in range(1, 366)]
    time_rows = [{"hour": minute / 60, **time_policy.evaluate(build_context(minute / 60, 172, None)).salience} for minute in range(1440)]
    datasets = {"activity": activity_rows, "season": season_rows, "time": time_rows}
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), layout="constrained")
    for axis, (name, rows) in zip(axes, datasets.items()):
        fields = list(rows[0])
        with (args.out / f"{name}.csv").open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        for item in fields[1:]:
            axis.plot([row[fields[0]] for row in rows], [row[item] for row in rows], label=item)
        axis.axhline(config.matching.positive_boundary, color="grey", linestyle="--", linewidth=0.7)
        axis.axhline(-config.matching.negative_boundary, color="grey", linestyle="--", linewidth=0.7)
        axis.set(title=name, xlabel=fields[0], ylabel="signed salience", ylim=(-1.1, 1.1))
        axis.legend(loc="upper right")
    fig.savefig(args.out / "salience-curves.png", dpi=160)
    plt.close(fig)
    (args.out / "replay.json").write_text(json.dumps(replay, ensure_ascii=False), encoding="utf-8")
    print(f"written curves and 1800 full distributions: {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
