from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from configurations.runtime_models import SchedulingConfig
from core.models.context import Context
from core.models.scene import Scenes
from core.models.trace import (
    Action,
    ActPlan,
    Blocker,
    BlockerEvaluation,
    Decision,
    DecisionMode,
    Selection,
)

logger = logging.getLogger("Tunalo.Controller")


class Intent(StrEnum):
    SWITCH = "switch"
    CYCLE = "cycle"


class CpuGate:
    def __init__(self, threshold: float):
        self.threshold = threshold

    def evaluate(self, context: Context) -> Blocker | None:
        if self.threshold > 0 and context.cpu >= self.threshold:
            logger.debug(
                "CPU gate: %.1f%% >= %.0f%%, deferring",
                context.cpu,
                self.threshold,
            )
            return Blocker.CPU
        return None


class FullscreenGate:
    def evaluate(self, context: Context) -> Blocker | None:
        if context.fullscreen:
            logger.debug("Fullscreen gate: deferring switch")
            return Blocker.FULLSCREEN
        return None


class Controller:
    def __init__(self, config: SchedulingConfig, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock if clock is not None else time.monotonic
        self.idle_threshold = config.idle_threshold
        self.force_after = config.force_after
        self.cycle_cooldown = config.cycle_cooldown
        self.cpu_threshold = config.cpu_threshold
        self.pause_on_fullscreen = config.pause_on_fullscreen

        startup_delay = max(config.startup_delay, 0)
        now = self._clock()
        self.startup_end = now + startup_delay
        self.last_action_time = now
        self._gates: list[CpuGate | FullscreenGate] = []
        if self.cpu_threshold > 0:
            self._gates.append(CpuGate(self.cpu_threshold))
        if self.pause_on_fullscreen:
            self._gates.append(FullscreenGate())

    def decide_action(
        self,
        plan: ActPlan,
        context: Context,
        selection: Selection,
    ) -> Decision:
        selected = selection.scenes
        probabilities = dict(selection.probabilities)
        if plan.mode == DecisionMode.PAUSE:
            return Decision(Action.PAUSE, selected, probabilities=probabilities)
        if not selected:
            return Decision(Action.HOLD if plan.active_scenes else Action.NONE, Scenes())

        intent = Intent.CYCLE if selected == plan.active_scenes else Intent.SWITCH
        if plan.mode == DecisionMode.RECOVERY:
            intent = Intent.SWITCH
        evaluation = self._evaluate_blockers(context, intent) if plan.mode == DecisionMode.NORMAL else None
        action = Action.SWITCH if intent == Intent.SWITCH else Action.CYCLE
        if evaluation is not None and not evaluation.allowed:
            action = Action.HOLD
        return Decision(action, selected, evaluation=evaluation, probabilities=probabilities)

    def _evaluate_blockers(
        self,
        context: Context,
        intent: Intent,
    ) -> BlockerEvaluation:
        current_time = self._clock()

        blocked_by: list[Blocker] = []
        warmup_remaining = max(0.0, self.startup_end - current_time)
        if warmup_remaining > 0:
            blocked_by.append(Blocker.COOLDOWN)
        blocked_by.extend(self._evaluate_gates(context))

        time_since_last = current_time - self.last_action_time
        force_after_remaining = max(0.0, self.force_after - time_since_last)

        if intent == Intent.SWITCH:
            cooldown_remaining = 0.0
        else:
            cooldown_remaining = max(0.0, self.cycle_cooldown - time_since_last)

        if cooldown_remaining > 0 and Blocker.COOLDOWN not in blocked_by:
            blocked_by.append(Blocker.COOLDOWN)

        idle_seconds = context.idle
        if intent == Intent.SWITCH:
            idle_ready = idle_seconds >= self.idle_threshold
            force_ready = time_since_last >= self.force_after
            if not idle_ready and not force_ready:
                blocked_by.append(Blocker.IDLE)
        elif idle_seconds < self.idle_threshold:
            blocked_by.append(Blocker.IDLE)

        return BlockerEvaluation(
            blocked_by=blocked_by,
            cooldown_remaining=warmup_remaining if warmup_remaining > 0 else cooldown_remaining,
            idle_seconds=idle_seconds,
            idle_threshold=self.idle_threshold,
            cpu_percent=context.cpu,
            cpu_threshold=self.cpu_threshold if self.cpu_threshold > 0 else None,
            fullscreen=context.fullscreen,
            force_after_remaining=force_after_remaining,
        )

    def _evaluate_gates(self, context: Context) -> list[Blocker]:
        blocked_by: list[Blocker] = []
        for gate in self._gates:
            blocker = gate.evaluate(context)
            if blocker is not None:
                blocked_by.append(blocker)
        return blocked_by

    def notify_executed(self, decision: Decision) -> None:
        self.last_action_time = self._clock()

    def export_state(self) -> dict[str, Any]:
        return {
            "last_action_time": self.last_action_time,
            "startup_end": self.startup_end,
        }

    def import_state(self, state: dict[str, Any]) -> None:
        self.last_action_time = state["last_action_time"]
        self.startup_end = state["startup_end"]
