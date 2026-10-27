from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from core.models.event import EventLogger, EventType
from core.models.trace import TickTrace
from core.runtime.engine import Engine
from core.runtime.profile_manager import ProfileManager
from core.state.action_events import ActionEventWriter
from core.state.scheduler import SchedulerState

logger = logging.getLogger("Tunalo.Core")
type TickListener = Callable[[TickTrace], None]


class Scheduler:
    def __init__(self, profile_manager: ProfileManager, event_logger: EventLogger) -> None:
        self.event_logger = event_logger
        self.initialized = False
        self.running = False
        self.thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self._state_lock = threading.RLock()
        self._profile_manager = profile_manager
        self.engine: Engine

        self.on_auto_resume: Callable[[], None] | None = None
        self._tick_listeners: list[TickListener] = []
        self.add_tick_listener(ActionEventWriter(event_logger).on_tick)

        self.state = SchedulerState()

    @property
    def paused(self) -> bool:
        return self.state.paused

    @property
    def last_tick_trace(self) -> TickTrace | None:
        return self.state.last_tick_trace

    def initialize(self) -> None:
        config = self._profile_manager.compile_initial_config()
        self.engine = Engine.from_config(config)
        self.state.restore_persisted_state()

        logger.info("Scheduler initialized successfully.")
        self.initialized = True

    def start(self) -> None:
        if self.running:
            logger.warning("Scheduler is already running.")
            return

        assert self.initialized, "Scheduler must be initialized before start."

        self._profile_manager.accept_updates()
        self.running = True
        self.stop_event.clear()
        self.event_logger.write(EventType.START, {})
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Scheduler started.")

    def stop(self) -> None:
        if not self.running:
            return
        self._profile_manager.reject_updates()
        self.stop_event.set()
        if self.thread:
            # 不使用 timeout 参数，确保退出前完成当前调度和 tick listener
            self.thread.join()
        self.running = False
        self.state.save()
        self.event_logger.write(EventType.STOP, {})
        logger.info("Scheduler stopped.")

    def pause(self, seconds: int | None = None) -> None:
        with self._state_lock:
            self.state.pause(seconds)
            self.event_logger.write(EventType.PAUSE, {"duration": seconds})

    def resume(self) -> None:
        with self._state_lock:
            if not self.state.resume():
                return
            self.event_logger.write(EventType.RESUME, {})

    def add_tick_listener(self, listener: TickListener) -> None:
        self._tick_listeners.append(listener)

    def get_pause_remaining(self) -> float | None:
        return self.state.get_pause_remaining()

    def get_scene_name(self, scene_id: str) -> str | None:
        return self.engine.get_scene_name(scene_id)

    def _run_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                with self._state_lock:
                    self._profile_manager.process_pending(self.engine)
                    if self.stop_event.is_set():
                        break
                    self._maybe_auto_resume()
                    self.engine.ensure_we_alive(paused=self.state.paused)
                    schedule = self.engine.schedule(
                        paused=self.state.paused,
                        manual_requested=self.state.consume_manual_apply_request(),
                    )
                    trace = self.state.commit(schedule)
                    self._notify_tick_listeners(trace)

            except Exception:
                logger.exception("Error in main loop")

            self.stop_event.wait(1)

    def _maybe_auto_resume(self) -> None:
        if not self.state.maybe_auto_resume():
            return

        self.event_logger.write(EventType.RESUME, {})
        if self.on_auto_resume:
            try:
                self.on_auto_resume()
            except Exception:
                logger.exception("on_auto_resume hook failed")

    def apply_current_match_now(self) -> None:
        logger.info("Manual apply requested.")
        with self._state_lock:
            self.state.request_manual_apply()

    def _notify_tick_listeners(self, trace: TickTrace) -> None:
        for listener in list(self._tick_listeners):
            try:
                listener(trace)
            except Exception:
                logger.exception("tick listener failed")
