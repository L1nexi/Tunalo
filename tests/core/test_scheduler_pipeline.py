from __future__ import annotations

import time
from pathlib import Path
from typing import TextIO

import pytest

from core.state.scheduler import SchedulerState


@pytest.fixture
def state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "state.json"

    def open_state(filename: str, mode: str = "r", *, encoding: str | None = None) -> TextIO:
        return open(path, mode, encoding=encoding)

    monkeypatch.setattr("core.state.persisted.open", open_state, raising=False)
    return path


def test_manual_apply_request_is_consumed_once() -> None:
    s = SchedulerState()
    s.request_manual_apply()
    assert s.consume_manual_apply_request() is True
    assert s.consume_manual_apply_request() is False


@pytest.mark.parametrize("seconds, expected_remaining", [(None, None), (60, 60.0)])
def test_paused_state_survives_reload(
    state_path: Path, monkeypatch: pytest.MonkeyPatch, seconds: int | None, expected_remaining: float | None
) -> None:
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    state = SchedulerState()
    state.pause(seconds)

    restored = SchedulerState()
    restored.restore_persisted_state()
    assert restored.paused
    assert restored.get_pause_remaining() == expected_remaining


@pytest.mark.parametrize("automatic", [False, True])
def test_resumed_state_survives_reload(state_path: Path, monkeypatch: pytest.MonkeyPatch, automatic: bool) -> None:
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    state = SchedulerState()
    state.pause(60)

    if automatic:
        monkeypatch.setattr(time, "time", lambda: 1061.0)
        assert state.maybe_auto_resume()
    else:
        assert state.resume()

    assert not state.resume()
    restored = SchedulerState()
    restored.restore_persisted_state()
    assert not restored.paused
