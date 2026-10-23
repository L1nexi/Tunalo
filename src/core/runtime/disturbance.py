from __future__ import annotations

from configurations.runtime_models import DisturbanceConfig
from core.models.context import Context
from core.models.scheduling import Blocker, DisturbanceEvaluation


class DisturbanceControl:
    def __init__(self, config: DisturbanceConfig) -> None:
        self._config = config

    def evaluate(self, context: Context) -> DisturbanceEvaluation:
        config = self._config
        blocked_by: list[Blocker] = []
        if config.cpu_threshold > 0 and context.cpu >= config.cpu_threshold:
            blocked_by.append(Blocker.CPU)
        if config.pause_on_fullscreen and context.fullscreen:
            blocked_by.append(Blocker.FULLSCREEN)
        if context.idle < config.idle_threshold:
            blocked_by.append(Blocker.IDLE)
        return DisturbanceEvaluation(
            blocked_by=blocked_by,
            idle_seconds=context.idle,
            idle_threshold=config.idle_threshold,
            cpu_percent=context.cpu,
            cpu_threshold=config.cpu_threshold if config.cpu_threshold > 0 else None,
            fullscreen=context.fullscreen,
        )
