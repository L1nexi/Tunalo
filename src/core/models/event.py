from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable


class EventType(StrEnum):
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    SCENES_APPLIED = "scenes_applied"
    ACTUATION_FAILED = "actuation_failed"


@runtime_checkable
class EventLogger(Protocol):
    def write(self, event_type: str, data: dict[str, object], *, ts: float | None = None) -> int: ...
