from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from configurations.runtime_models import BasePolicyConfig
from core.models.context import Context
from core.models.trace import PolicyEvaluation


def _s_curve(z: float, q: float) -> float:
    """Map a calibrated [0, 1] input to [0, 1] without losing its magnitude."""
    # expm1 keeps the numerator and denominator accurate near zero.
    return -math.expm1(-math.log(2) * (z / q) ** 3) / -math.expm1(-math.log(2) * (1 / q) ** 3)


def _periodic_salience(position: float, anchors: list[tuple[float, float]], period: float, half_width: float, q: float) -> float:
    """Interpolate between signed periodic anchors, with optional platforms.

    Raises:
        ValueError: If the anchors do not cover the complete cycle.
    """
    for index, (start, start_value) in enumerate(anchors):
        distance = (position - start) % period
        if distance <= half_width or distance >= period - half_width:
            return start_value
        end, end_value = anchors[(index + 1) % len(anchors)]
        span = (end - start) % period
        if distance < span - half_width:
            progress = (distance - half_width) / (span - 2 * half_width)
            return start_value + (end_value - start_value) * _s_curve(progress, q)
    raise ValueError("periodic anchors must cover the complete cycle")


class Policy(ABC):
    config_key: ClassVar[str]

    def __init__(self, config: BasePolicyConfig) -> None:
        self.config = config

    @abstractmethod
    def evaluate(self, context: Context) -> PolicyEvaluation: ...

    def export_state(self) -> dict[str, Any]:
        return {}

    def import_state(self, state: dict[str, Any]) -> None:
        pass
