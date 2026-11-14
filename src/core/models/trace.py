from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.models.scheduling import ScheduleResult


@dataclass
class TickTrace:
    tick_id: int
    ts: float
    paused: bool
    pause_until: float
    schedule: ScheduleResult
