from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from PIL import Image


def _run_scan(directory: Path, suite: str, mode: str | None = None) -> tuple[Path, dict[str, Any]]:
    """运行公开扫描命令；命令失败时抛出 subprocess.CalledProcessError。"""
    script = Path(__file__).resolve().parents[1] / "tools/tuning/scan.py"
    command = [sys.executable, str(script), "--suite", suite, "--out", str(directory)]
    if mode is not None:
        command.extend(["--mode", mode])
    subprocess.run(command, cwd=directory, check=True, capture_output=True, text=True)
    output = directory / suite
    return output, json.loads((output / "distributions.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def single_scan(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    return _run_scan(tmp_path_factory.mktemp("single-scan"), "single", "wx-act")


@pytest.fixture(scope="module")
def pair_scan(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    return _run_scan(tmp_path_factory.mktemp("pair-scan"), "pair-wx-act")


@pytest.fixture(scope="module")
def product_scan(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    return _run_scan(tmp_path_factory.mktemp("product-scan"), "product", "wx-hour")


def _exported_probabilities(payload: dict[str, Any], fixed: dict[str, float | int], x_value: float, weather: str) -> dict[str, float]:
    """读取指定观测点；缺少观测点时抛出 StopIteration 或 ValueError。"""
    grid = next(grid for grid in payload["grids"] if all(grid["fixed"][key] == value for key, value in fixed.items()))
    row, col = grid["y"]["values"].index(weather), grid["x"]["values"].index(x_value)
    return {scene: probabilities[row][col] for scene, probabilities in grid["probabilities"].items()}


@pytest.mark.parametrize("activity, scene", [(1, "work"), (-1, "leisure")])
def test_single_scan_without_preferences_keeps_zero_evidence_scenes_eligible(
    single_scan: tuple[Path, dict[str, Any]], activity: int, scene: str
) -> None:
    _, payload = single_scan
    probabilities = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, activity, "mod_rain")

    for candidates in (
        ("spring", "summer", "autumn", "winter"),
        ("dawn", "day", "sunset", "night"),
        ("clear", "cloudy", "rain"),
        ("work", "leisure"),
    ):
        assert sum(probabilities[scene_id] for scene_id in candidates) == pytest.approx(0.25)
    assert probabilities["rain"] == pytest.approx(probabilities[scene])
    assert 0 < probabilities["dawn"] < probabilities["day"] < probabilities[scene]
    assert probabilities["dawn"] == pytest.approx(probabilities["sunset"])
    assert probabilities["winter"] == probabilities["night"] == 0
    assert sum(probabilities.values()) == pytest.approx(1)


def test_weather_scan_includes_every_decided_rain_severity(single_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = single_scan

    assert payload["grids"]
    for grid in payload["grids"]:
        assert {"light_rain", "mod_rain", "heavy_rain", "violent_rain"} <= set(grid["y"]["values"])


def test_weather_activity_pair_defaults_to_weather_and_activity_axes(pair_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = pair_scan

    assert {(grid["x"]["name"], grid["y"]["name"]) for grid in payload["grids"]} == {("activity", "weather")}


def test_rain_work_receives_both_source_budgets_even_when_activity_is_neutral(pair_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = pair_scan
    rain_only = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, 0, "mod_rain")
    both = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, 1, "mod_rain")

    assert rain_only["rain_work"] > rain_only["rain"] > 0
    assert both["rain_work"] > both["rain"] > 0
    assert both["rain_work"] > rain_only["rain_work"]


def test_clear_weather_excludes_rain_work_even_with_full_work(pair_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = pair_scan
    probabilities = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, 1, "clear")

    assert probabilities["rain_work"] == 0
    assert probabilities["clear_work"] > 0


@pytest.mark.parametrize("hour", [8.5, 15.5])
def test_daytime_work_excludes_night_work_from_product_scan(product_scan: tuple[Path, dict[str, Any]], hour: float) -> None:
    _, payload = product_scan
    probabilities = _exported_probabilities(payload, {"day_of_year": 126, "activity": 1}, hour, "clear")

    assert probabilities["night_work"] == 0
    assert probabilities["day_work"] > 0


@pytest.mark.parametrize("fixture_name, mode", [("single_scan", "wx-act"), ("pair_scan", "wx-act"), ("product_scan", "wx-hour")])
def test_scans_export_viewable_probability_and_winner_pngs(request: pytest.FixtureRequest, fixture_name: str, mode: str) -> None:
    output, _ = request.getfixturevalue(fixture_name)

    for filename in ("rain.png", "winner-map.png"):
        with Image.open(output / f"cur-{mode}" / filename) as preview:
            assert preview.format == "PNG"
            preview.verify()
