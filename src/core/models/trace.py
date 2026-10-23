from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.models.context import Context
    from core.models.scene import Scenes
    from core.models.scheduling import ActionResult, Decision, ScheduleResult
    from core.models.selection import Selection


@dataclass
class TickTrace:
    tick_id: int
    ts: float
    paused: bool
    pause_until: float
    schedule: ScheduleResult

    @property
    def context(self) -> Context:
        return self.schedule.context

    @property
    def selection(self) -> Selection:
        return self.schedule.selection

    @property
    def decision(self) -> Decision:
        return self.schedule.decision

    @property
    def action(self) -> ActionResult:
        return self.schedule.action

    @property
    def target(self) -> Scenes:
        return self.schedule.target
