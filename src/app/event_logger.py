from __future__ import annotations

import json
import logging
import os
import threading
from datetime import UTC, datetime

logger = logging.getLogger("Tunalo.Events")


class JsonlEventLogger:
    def __init__(self, data_dir: str) -> None:
        self._data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, event_type: str, data: dict[str, object], *, ts: float | None = None) -> None:

        occurred_at = datetime.now(UTC) if ts is None else datetime.fromtimestamp(ts, UTC)
        record = {
            "ts": occurred_at.isoformat(timespec="seconds"),
            "type": event_type,
            "data": data,
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        filepath = os.path.join(self._data_dir, f"events-{occurred_at:%Y-%m}.jsonl")

        with self._lock:
            try:
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(line)
            except OSError:
                logger.warning("Failed to write event", exc_info=True)
