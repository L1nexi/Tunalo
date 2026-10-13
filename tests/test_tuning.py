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


@pytest.mark.parametrize("activity, scene", [(1, "focus"), (-1, "chill")])
def test_single_scan_splits_four_equal_sources_into_quarters(single_scan: tuple[Path, dict[str, Any]], activity: int, scene: str) -> None:
    _, payload = single_scan
    probabilities = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, activity, "mod_rain")

    # ADR-0003：四个同等显著来源各占四分之一。
    assert {scene_id: chance for scene_id, chance in probabilities.items() if chance > 0} == pytest.approx(
        {"summer": 0.25, "rain": 0.25, "day": 0.25, scene: 0.25}
    )


def test_weather_scan_includes_every_decided_rain_severity(single_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = single_scan

    assert payload["grids"]
    for grid in payload["grids"]:
        assert {"light_rain", "mod_rain", "heavy_rain", "violent_rain"} <= set(grid["y"]["values"])


def test_weather_activity_pair_defaults_to_weather_and_activity_axes(pair_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = pair_scan

    assert {(grid["x"]["name"], grid["y"]["name"]) for grid in payload["grids"]} == {("activity", "weather")}


def test_rain_only_favors_rain_and_joint_evidence_favors_rain_focus(pair_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = pair_scan
    rain_only = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, 0, "mod_rain")
    both = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, 1, "mod_rain")

    # ADR-0003：复合场景的优势随两种情境是否同等显著而反转。
    assert rain_only["rain"] > rain_only["rain_focus"] > 0
    assert both["rain_focus"] > both["rain"] > 0


def test_clear_weather_excludes_rain_focus_even_with_full_focus(pair_scan: tuple[Path, dict[str, Any]]) -> None:
    _, payload = pair_scan
    probabilities = _exported_probabilities(payload, {"hour": 12, "day_of_year": 172}, 1, "clear")

    assert probabilities["rain_focus"] == 0
    assert probabilities["clear_focus"] > 0


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
