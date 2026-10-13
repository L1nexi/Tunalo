from __future__ import annotations

import json
import threading

import pytest

from app.event_logger import JsonlEventLogger
from core.models.event import EventType


@pytest.fixture
def event_logger(tmp_path):
    return JsonlEventLogger(str(tmp_path))


def test_write_returns_monotonically_incrementing_id(event_logger):
    assert event_logger.write(EventType.START, {"playlist": "A"}) == 1
    assert event_logger.write(EventType.PAUSE, {"reason": "idle"}) == 2
    assert event_logger.write(EventType.RESUME, {"playlist": "A"}) == 3


def test_write_persists_to_jsonl(event_logger, tmp_path):
    event_logger.write(EventType.START, {"playlist": "test"})

    files = list(tmp_path.glob("events-*.jsonl"))
    assert len(files) == 1
    with files[0].open(encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["type"] == EventType.START
    assert record["data"] == {"playlist": "test"}
    assert "ts" in record


def test_concurrent_writes_preserve_ids(event_logger):
    errors = []
    n_per_thread = 50
    n_threads = 4

    def writer():
        for _ in range(n_per_thread):
            try:
                event_logger.write(EventType.START, {})
            except Exception as exc:
                errors.append(exc)

    threads = [threading.Thread(target=writer) for _ in range(n_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert event_logger.write(EventType.STOP, {}) == n_per_thread * n_threads + 1


def test_write_failure_rolls_back_event_id(event_logger, monkeypatch):
    def failing_open(*args, **kwargs):
        raise OSError("disk full")

    event_logger.write(EventType.START, {})
    monkeypatch.setattr("builtins.open", failing_open)

    assert event_logger.write(EventType.PAUSE, {}) == 1
