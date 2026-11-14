from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.event_logger import JsonlEventLogger
from core.models.event import EventType


@pytest.fixture
def event_logger(tmp_path: Path) -> JsonlEventLogger:
    return JsonlEventLogger(str(tmp_path))


def test_write_persists_to_jsonl(event_logger: JsonlEventLogger, tmp_path: Path) -> None:
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


def test_delayed_records_use_occurrence_time_across_months(tmp_path: Path) -> None:
    event_logger = JsonlEventLogger(str(tmp_path))
    october = datetime(2026, 10, 1, tzinfo=UTC)
    september = datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC)
    event_logger.write(EventType.RESUME, {}, ts=october.timestamp())
    event_logger.write(EventType.PAUSE, {"duration": 60}, ts=september.timestamp())

    october_record = json.loads((tmp_path / "events-2026-10.jsonl").read_text(encoding="utf-8"))
    september_record = json.loads((tmp_path / "events-2026-09.jsonl").read_text(encoding="utf-8"))
    assert october_record == {"ts": "2026-10-01T00:00:00+00:00", "type": "resume", "data": {}}
    assert september_record == {"ts": "2026-09-30T23:59:59+00:00", "type": "pause", "data": {"duration": 60}}


def test_concurrent_writes_preserve_complete_records(event_logger: JsonlEventLogger, tmp_path: Path) -> None:
    n_per_thread = 50
    n_threads = 4
    barrier = threading.Barrier(n_threads)

    def writer(worker: int) -> None:
        barrier.wait(timeout=5)
        for sequence in range(n_per_thread):
            event_logger.write(EventType.START, {"worker": worker, "sequence": sequence}, ts=0.0)

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = [executor.submit(writer, worker) for worker in range(n_threads)]
        for future in futures:
            future.result(timeout=5)

    records = [json.loads(line) for line in (tmp_path / "events-1970-01.jsonl").read_text(encoding="utf-8").splitlines()]
    assert sorted((record["data"]["worker"], record["data"]["sequence"]) for record in records) == [
        (worker, sequence) for worker in range(n_threads) for sequence in range(n_per_thread)
    ]


def test_file_error_is_reported_and_later_writes_succeed(event_logger: JsonlEventLogger, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    filepath = tmp_path / "events-1970-01.jsonl"
    filepath.mkdir()

    event_logger.write(EventType.PAUSE, {}, ts=0.0)
    assert "Failed to write event" in caplog.text

    filepath.rmdir()
    event_logger.write(EventType.RESUME, {}, ts=1.0)
    assert json.loads(filepath.read_text(encoding="utf-8")) == {"ts": "1970-01-01T00:00:01+00:00", "type": "resume", "data": {}}
