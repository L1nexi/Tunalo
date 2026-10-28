from __future__ import annotations

import getpass
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from queue import Queue
from typing import TextIO

import pytest

from app.event_logger import JsonlEventLogger
from configurations.profile import Profile
from configurations.profile_store import ProfileStore
from configurations.runtime_models import PoliciesConfig, SceneConfig, SchedulerConfig, WeatherPolicyConfig
from core.models.association import Association
from core.models.selection import SemanticItem
from core.models.trace import TickTrace
from core.runtime.engine import Engine
from core.runtime.profile_manager import ProfileManager
from core.runtime.scheduler import Scheduler
from core.state.tick_history import TickHistoryStore


@pytest.mark.parametrize("returncode", [0, 1])
def test_scheduler_commits_before_profile_updates_and_waits_for_current_tick_on_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, returncode: int
) -> None:
    executable = tmp_path / "wallpaper64.exe"
    executable.touch()
    (tmp_path / "config.json").write_text(
        json.dumps({getpass.getuser(): {"general": {"playlists": [{"name": "WORK", "items": ["one"]}, {"name": "NEW", "items": ["two"]}]}}}),
        encoding="utf-8",
    )
    profile = Profile.model_validate(
        {
            "wallpaper_engine_path": str(executable),
            "weather": {"api_key": "test-key", "location": {"latitude": 31, "longitude": 121}},
            "scenes": {"work": {"name": "工作", "associations": {"activity": ["work"]}, "playlist": "WORK"}},
        }
    )
    ProfileStore(str(tmp_path)).commit(profile)
    manager = ProfileManager(str(tmp_path))
    manager.load_initial_profile()

    commands: Queue[tuple[list[str], threading.Event]] = Queue()
    releases: list[threading.Event] = []
    weather_threads: list[threading.Thread] = []
    release_weather = threading.Event()

    class Process:
        def __init__(self, args: list[str], **kwargs: object) -> None:
            self.returncode = returncode
            self.args = args

        def wait(self, timeout: float) -> int:
            release = threading.Event()
            releases.append(release)
            commands.put((self.args, release))
            assert release.wait(5)
            return self.returncode

    class WeatherResponse:
        status_code = 200

        def json(self) -> dict[str, object]:
            return {"weather": [{"id": 800, "main": "Clear"}]}

    def request_weather(*args: object, **kwargs: object) -> WeatherResponse:
        weather_threads.append(threading.current_thread())
        assert release_weather.wait(5)
        return WeatherResponse()

    def open_state(path: str, mode: str = "r", *, encoding: str | None = None) -> TextIO:
        return open(tmp_path / "state.json", mode, encoding=encoding)

    monkeypatch.setattr("core.runtime.executor.subprocess.Popen", Process)
    monkeypatch.setattr("integrations.openweather.requests.get", request_weather)
    monkeypatch.setattr("win32gui.GetForegroundWindow", lambda: 0)
    monkeypatch.setattr("ctypes.windll.shell32.SHQueryUserNotificationState", lambda pointer: 0)
    monkeypatch.setattr("psutil.cpu_percent", lambda: 0.0)
    monkeypatch.setattr("core.state.persisted.open", open_state, raising=False)

    event_logger = JsonlEventLogger(str(tmp_path))
    history = TickHistoryStore()
    observed: list[tuple[TickTrace, str, int]] = []

    def observe(trace: TickTrace) -> None:
        current = manager.get_profile()
        assert current is not None
        observed.append((trace, current.scenes["work"].playlist, threading.get_ident()))

    scheduler = Scheduler(manager, event_logger)
    scheduler.add_tick_listener(history.update)
    scheduler.add_tick_listener(observe)
    scheduler.initialize()

    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            scheduler.start()
            first_command, release_first = commands.get(timeout=5)
            assert first_command[-1] == "WORK"
            assert scheduler.last_tick_trace is None
            assert history.read_window().traces == ()
            release_weather.set()
            for worker in weather_threads:
                worker.join(timeout=1)
                assert not worker.is_alive()

            replacement = profile.model_copy(deep=True)
            replacement.scenes["work"].playlist = "NEW"
            updating = executor.submit(manager.apply_profile, replacement, timeout=5)
            release_first.set()

            deadline = time.monotonic() + 5
            while scheduler.last_tick_trace is None and time.monotonic() < deadline:
                time.sleep(0.005)
            first_trace = scheduler.last_tick_trace
            assert first_trace is not None
            assert first_trace.context.weather is not None
            assert first_trace.context.weather.last_success_at is None
            assert first_trace.context.sun_times is not None
            assert any(first_trace.selection.salience[item] != 0 for item in ("dawn", "day", "sunset", "night"))

            second_command, release_second = commands.get(timeout=5)
            assert second_command[-1] == "NEW"
            assert updating.result(timeout=5) == replacement
            assert [trace.tick_id for trace in history.read_window().traces] == [1]
            assert observed[0][1] == "WORK"
            assert first_trace.action.target_playlist == "WORK"

            stop_started = threading.Event()

            def stop() -> None:
                stop_started.set()
                scheduler.stop()

            stopping = executor.submit(stop)
            assert stop_started.wait(5)
            with pytest.raises(FutureTimeoutError):
                stopping.result(timeout=2.1)
            release_second.set()
            stopping.result(timeout=5)
        finally:
            scheduler.stop_event.set()
            release_weather.set()
            for release in releases:
                release.set()
            scheduler.stop()
            for worker in weather_threads:
                worker.join(timeout=5)
                assert not worker.is_alive()

    window = history.read_window()
    assert window.live_tick_id == 2
    assert [trace.tick_id for trace in window.traces] == [1, 2]
    assert [trace.action.target_playlist for trace in window.traces] == ["WORK", "NEW"]
    assert all(trace.action.executed == (returncode == 0) for trace in window.traces)
    assert [trace.tick_id for trace, _, _ in observed] == [1, 2]
    assert observed[1][1] == "NEW"
    second_weather = observed[1][0].context.weather
    assert second_weather is not None
    assert second_weather.last_success_at is not None
    assert second_weather.id == 800
    assert second_weather.source_fingerprint == first_trace.context.weather.source_fingerprint
    assert first_trace.context.weather.last_success_at is None
    assert "test-key" not in repr(window.traces)
    assert scheduler.thread is not None
    assert {thread_id for _, _, thread_id in observed} == {scheduler.thread.ident}
    assert scheduler.thread.ident != threading.get_ident()
    assert not scheduler.thread.is_alive()
    assert not scheduler.running

    records = [json.loads(line) for path in sorted(tmp_path.glob("events-*.jsonl")) for line in path.read_text(encoding="utf-8").splitlines()]
    action_type = "scenes_applied" if returncode == 0 else "actuation_failed"
    assert [record["type"] for record in records] == ["start", action_type, action_type, "stop"]


def test_paused_engine_senses_local_sun_times_and_replaces_location_without_weather(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable = tmp_path / "wallpaper64.exe"
    executable.touch()
    config = SchedulerConfig(
        wallpaper_engine_path=str(executable),
        scenes={"day": SceneConfig(name="Day", playlist="DAY", associations=Association(SemanticItem.DAY))},
        policies=PoliciesConfig(weather=WeatherPolicyConfig(lat=31.23, lon=121.47)),
    )

    def reject_external_call(*args: object, **kwargs: object) -> None:
        raise AssertionError("Paused local sun times must not request weather or execute Wallpaper Engine")

    monkeypatch.setattr("requests.sessions.Session.request", reject_external_call)
    monkeypatch.setattr("subprocess.Popen", reject_external_call)
    monkeypatch.setattr("win32gui.GetForegroundWindow", lambda: 0)
    monkeypatch.setattr("ctypes.windll.shell32.SHQueryUserNotificationState", lambda pointer: 0)
    monkeypatch.setattr("psutil.cpu_percent", lambda: 0.0)

    engine = Engine.from_config(config)
    first = engine.schedule(paused=True, manual_requested=False)
    assert first.context.weather is None
    original = first.context.sun_times
    assert original is not None
    original_times = (original.sunrise, original.sunset)
    assert any(first.selection.salience[item] != 0 for item in ("dawn", "day", "sunset", "night"))

    updated = config.model_copy(deep=True)
    updated.policies.weather.lon = 91.47
    engine.install_replacement(engine.prepare_replacement(updated))
    following = engine.schedule(paused=True, manual_requested=False)
    assert following.context.weather is None
    assert following.context.sun_times is not None
    assert 3600 < following.context.sun_times.sunrise - original.sunrise < 10800
    assert first.context.sun_times is not None
    assert (first.context.sun_times.sunrise, first.context.sun_times.sunset) == original_times
    assert not first.action.executed and not following.action.executed
