from __future__ import annotations

import getpass
import json
import random
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.event_logger import JsonlEventLogger
from configurations.runtime_models import ActivityPolicyConfig, PoliciesConfig, SceneConfig, SchedulerConfig, SchedulingConfig, WeatherPolicyConfig
from core.models.scene import SceneId, Scenes
from core.models.scheduling import Action, Decision
from core.models.trace import TickTrace
from core.runtime.engine import Engine
from core.state.action_events import ActionEventWriter
from core.state.scheduler import SchedulerState
from ui.tick_history import build_tick_snapshot


@pytest.fixture
def desktop(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    state = SimpleNamespace(process="code.exe", title="", idle=100.0, now=1000.0, executed=True, playlists=[])
    monkeypatch.setattr("core.sensors.window.win32gui.GetForegroundWindow", lambda: 1)
    monkeypatch.setattr("core.sensors.window.win32gui.GetWindowText", lambda _hwnd: state.title)
    monkeypatch.setattr("core.sensors.window.win32process.GetWindowThreadProcessId", lambda _hwnd: (1, 1))
    monkeypatch.setattr("core.sensors.window.psutil.Process", lambda _pid: SimpleNamespace(name=lambda: state.process))
    monkeypatch.setattr("core.sensors.cpu.psutil.cpu_percent", lambda: 0.0)

    def last_input(info) -> int:
        info._obj.dwTime = 0
        return 1

    monkeypatch.setattr("core.sensors.idle._user32.GetLastInputInfo", last_input)
    monkeypatch.setattr("core.sensors.idle._kernel32.GetTickCount64", lambda: int(state.idle * 1000))
    monkeypatch.setattr("core.runtime.controller.time.monotonic", lambda: state.now)

    def execute(_executor, playlist: str) -> bool:
        state.playlists.append(playlist)
        return state.executed

    class FixedRandom(random.Random):
        def random(self) -> float:
            return 0.525

    monkeypatch.setattr("core.runtime.executor.WEExecutor.open_playlist", execute)
    monkeypatch.setattr(random, "choices", FixedRandom().choices)
    return state


def engine_at(tmp_path: Path, scenes: dict[SceneId, SceneConfig] | None = None, **timing: float) -> Engine:
    executable = tmp_path / "wallpaper64.exe"
    executable.write_text("fixture", encoding="utf-8")
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                getpass.getuser(): {
                    "general": {
                        "wallpaperconfig": {"selectedwallpapers": {"monitor": {"playlist": {"name": "WORK"}}}},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    config = SchedulerConfig(
        wallpaper_engine_path=str(executable),
        scenes=scenes
        or {
            SceneId.DAY_WORK: SceneConfig(playlist="WORK", associations={"focus"}),
            SceneId.NIGHT_WORK: SceneConfig(playlist="OTHER", associations={"focus", "cloudy"}),
        },
        policies=PoliciesConfig(
            activity=ActivityPolicyConfig(
                matchers=[
                    {"source": "process", "match": "exact", "pattern": "code", "tag": "focus"},
                    {"source": "process", "match": "exact", "pattern": "vlc", "tag": "chill"},
                ]
            )
        ),
        scheduling=SchedulingConfig(
            **({"startup_delay": 0, "idle_threshold": 10, "force_after": 3600, "cycle_cooldown": 0, "pause_on_fullscreen": False} | timing)
        ),
    )
    return Engine.from_config(config)


def reject_sampling(*_args: object, **_kwargs: object) -> None:
    """暂停或阻塞期间使用随机源会使测试失败。"""
    pytest.fail("暂停或阻塞期间不得抽样")


def test_paused_ticks_keep_observing_without_applying_a_playlist(desktop: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = engine_at(tmp_path)
    monkeypatch.setattr(random, "choices", reject_sampling)
    for _ in range(180):
        schedule = engine.schedule(Scenes(), paused=True, manual_requested=False)
    assert schedule.selection.salience["focus"] == pytest.approx(0.572826991, abs=1e-9)
    assert desktop.playlists == []


def test_same_candidate_set_uses_latest_distribution_when_rotation_is_allowed(desktop: SimpleNamespace, tmp_path: Path) -> None:
    engine = engine_at(tmp_path)
    first = engine.schedule(Scenes([SceneId.DAY_WORK, SceneId.NIGHT_WORK]), paused=False, manual_requested=False)
    for _ in range(599):
        engine.schedule(Scenes(), paused=True, manual_requested=False)
    latest = engine.schedule(first.selection.scenes, paused=False, manual_requested=False)
    assert first.decision.action == latest.decision.action == Action.CYCLE
    # 同一随机位置在初始弱证据下落入 OTHER，持续工作后应落入 WORK。
    # 若执行侧复用旧分布或均匀抽样，这里的实际播单序列会错误。
    assert desktop.playlists == ["OTHER", "WORK"]


def test_blocking_and_execution_failure_preserve_scheduler_cache(desktop: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = engine_at(tmp_path)
    desktop.idle = 0
    with monkeypatch.context() as blocked_random:
        blocked_random.setattr(random, "choices", reject_sampling)
        blocked = engine.schedule(Scenes([SceneId.DAY_WORK]), paused=False, manual_requested=False)
    assert blocked.decision.action == Action.HOLD
    assert desktop.playlists == []
    desktop.idle = 100
    desktop.executed = False
    failed = engine.schedule(Scenes([SceneId.DAY_WORK]), paused=False, manual_requested=False)
    trace = TickTrace(tick_id=2, ts=0, paused=False, pause_until=0, schedule=failed)
    state = SchedulerState(cached_scenes=Scenes([SceneId.DAY_WORK]))
    state.commit(trace)
    assert failed.decision.action == Action.SWITCH
    assert not failed.action.executed
    assert state.cached_scenes == Scenes([SceneId.DAY_WORK])
    assert trace.target == Scenes([SceneId.DAY_WORK])


def test_prepared_replacement_preserves_observations_at_preparation_time(desktop: SimpleNamespace, tmp_path: Path) -> None:
    engine = engine_at(tmp_path)
    control = Engine.from_config(engine.config)
    for _ in range(180):
        engine.schedule(Scenes(), paused=True, manual_requested=False)
        control.schedule(Scenes(), paused=True, manual_requested=False)
    prepared = engine.prepare_replacement(engine.config)
    for _ in range(120):
        engine.schedule(Scenes(), paused=True, manual_requested=False)
    engine.install_replacement(prepared)
    desktop.process = "chrome.exe"
    resumed = engine.schedule(Scenes(), paused=True, manual_requested=False)
    expected = control.schedule(Scenes(), paused=True, manual_requested=False)
    fresh = Engine.from_config(engine.config).schedule(Scenes(), paused=True, manual_requested=False)
    assert resumed.selection.salience == expected.selection.salience
    assert resumed.selection.salience["focus"] > 0
    assert fresh.selection.salience["focus"] == 0


def test_execution_uses_scene_probability_even_with_unequal_sizes_and_shared_playlist(desktop: SimpleNamespace, tmp_path: Path) -> None:
    scenes = {
        SceneId.DAY_WORK: SceneConfig(playlist="SHARED", associations={"focus"}, item_count=10000),
        SceneId.RAIN: SceneConfig(playlist="SHARED", associations={"rain"}, item_count=1),
    }
    engine = engine_at(tmp_path, scenes=scenes)
    result = engine.actuator.act(Decision(Action.SWITCH, Scenes(list(scenes)), probabilities={SceneId.DAY_WORK: 0.01, SceneId.RAIN: 0.99}))
    assert result.selected_scene == SceneId.RAIN
    assert result.target_playlist == "SHARED"
    assert result.executed


def test_tick_dto_and_sparse_event_preserve_full_probability_meaning(desktop: SimpleNamespace, tmp_path: Path) -> None:
    scenes = {scene_id: SceneConfig(playlist=scene_id.value, associations={"focus"}) for scene_id in SceneId}
    engine = engine_at(tmp_path, scenes=scenes)
    schedule = engine.schedule(Scenes(), paused=False, manual_requested=True)
    trace = TickTrace(tick_id=1, ts=0, paused=False, pause_until=0, schedule=schedule)
    snapshot = build_tick_snapshot(trace)
    assert len(snapshot["act"]["sceneProbabilities"]) == 10
    assert all(row["probability"] == 0.1 for row in snapshot["act"]["sceneProbabilities"])
    assert "similarity" not in snapshot["summary"]
    assert snapshot["think"]["salience"]
    events = JsonlEventLogger(str(tmp_path / "events"))
    ActionEventWriter(events).on_tick(trace)
    rows = [json.loads(line) for path in (tmp_path / "events").glob("*.jsonl") for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["data"]["probabilities"] == {scene_id.value: 0.1 for scene_id in SceneId}
    assert "directions" not in rows[0]["data"]


def test_hot_replacement_reinterprets_retained_observations_with_new_product_parameters(desktop: SimpleNamespace, tmp_path: Path) -> None:
    engine = engine_at(tmp_path)
    for _ in range(180):
        before = engine.schedule(Scenes(), paused=True, manual_requested=False)
    config = engine.config.model_copy(deep=True)
    config.policies.activity.age_scale = 500
    replacement = engine.prepare_replacement(config)
    engine.install_replacement(replacement)
    desktop.process = "chrome.exe"
    after = engine.schedule(Scenes(), paused=True, manual_requested=False)
    assert 0 < after.selection.salience["focus"] < before.selection.salience["focus"]
    assert after.selection.salience["chill"] == -after.selection.salience["focus"]


def test_config_replacement_rebuilds_weather_cache(desktop: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gate = threading.Event()

    class RainResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"weather": [{"id": 504, "main": "Rain"}], "sys": {"sunrise": 1, "sunset": 2}}

    def fetch(*_args, **_kwargs):
        assert gate.wait(1)
        return RainResponse()

    monkeypatch.setattr("integrations.openweather.requests.get", fetch)
    engine = engine_at(tmp_path)
    config = engine.config.model_copy(deep=True)
    config.policies.weather = WeatherPolicyConfig(api_key="fixture", lat=0, lon=0)
    engine.install_replacement(engine.prepare_replacement(config))
    try:
        initial = engine.schedule(Scenes(), paused=True, manual_requested=False)
        assert initial.context.weather is None
        gate.set()
        deadline = time.perf_counter() + 1
        observed = engine.schedule(Scenes(), paused=True, manual_requested=False)
        while observed.context.weather is None and time.perf_counter() < deadline:
            time.sleep(0.005)
            observed = engine.schedule(Scenes(), paused=True, manual_requested=False)
        assert observed.selection.salience["rain"] == 4
        gate.clear()
        engine.install_replacement(engine.prepare_replacement(config))
        replaced = engine.schedule(Scenes(), paused=True, manual_requested=False)
        assert replaced.context.weather is None
        assert replaced.selection.salience["rain"] == 0
    finally:
        gate.set()
