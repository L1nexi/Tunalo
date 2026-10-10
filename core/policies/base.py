from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from configurations.runtime_models import BasePolicyConfig
from core.models.context import Context
from core.models.selection import PolicyEvaluation


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
