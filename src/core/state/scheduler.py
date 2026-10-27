from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from core.models.scheduling import ScheduleResult
from core.models.trace import TickTrace
from core.state.persisted import PersistedState

logger = logging.getLogger("Tunalo.State")


@dataclass
class SchedulerState:
    paused: bool = False
    pause_until: float = 0.0
    last_tick_trace: TickTrace | None = None
    tick_id: int = 0
    _manual_apply_pending: bool = False

    def pause(self, seconds: int | None = None) -> None:
        ts = time.time()
        self.paused = True
        if seconds is not None:
            self.pause_until = ts + seconds
            logger.info(
                "Scheduler paused for %ss (until %s).",
                seconds,
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.pause_until)),
            )
        else:
            self.pause_until = 0.0
            logger.info("Scheduler paused indefinitely.")
        self.save()

    def resume(self) -> bool:
        if not self.paused:
            return False
        self.paused = False
        self.pause_until = 0.0
        logger.info("Scheduler resumed.")
        self.save()
        return True

    def get_pause_remaining(self) -> float | None:
        if not self.paused or self.pause_until == 0:
            return None
        remaining = self.pause_until - time.time()
        return max(0.0, remaining)

    def maybe_auto_resume(self) -> bool:
        if not self.paused or self.pause_until <= 0:
            return False

        if time.time() < self.pause_until:
            return False

        logger.info("Timed pause expired.")
        return self.resume()

    def request_manual_apply(self) -> None:
        self._manual_apply_pending = True

    def consume_manual_apply_request(self) -> bool:
        if not self._manual_apply_pending:
            return False
        self._manual_apply_pending = False
        return True

    def commit(self, schedule: ScheduleResult) -> TickTrace:
        self.tick_id += 1
        trace = TickTrace(
            tick_id=self.tick_id,
            ts=time.time(),
            paused=self.paused,
            pause_until=self.pause_until,
            schedule=schedule,
        )

        self.last_tick_trace = trace
        return trace

    def save(self) -> None:
        PersistedState(paused=self.paused, pause_until=self.pause_until).save()

    def restore_persisted_state(self) -> None:
        state = PersistedState.load()
        self.paused = False
        self.pause_until = 0.0

        if state.pause_until > time.time():
            self.paused = True
            self.pause_until = state.pause_until
            logger.info(
                "Restored timed pause (until %s).",
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state.pause_until)),
            )
        elif state.paused and state.pause_until == 0:
            self.paused = True
            self.pause_until = 0.0
            logger.info("Restored indefinite pause.")
