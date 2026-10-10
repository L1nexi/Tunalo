from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import FiniteFloat, RootModel, model_validator


class ContextVariable(StrEnum):
    SEASON = "season"
    TIME = "time"
    WEATHER = "weather"
    ACTIVITY = "activity"


type SemanticItem = Literal[
    "spring",
    "summer",
    "autumn",
    "winter",
    "dawn",
    "day",
    "sunset",
    "night",
    "clear",
    "cloudy",
    "rain",
    "snow",
    "focus",
    "chill",
]

VARIABLE_ITEMS: dict[ContextVariable, tuple[SemanticItem, ...]] = {
    ContextVariable.SEASON: ("spring", "summer", "autumn", "winter"),
    ContextVariable.TIME: ("dawn", "day", "sunset", "night"),
    ContextVariable.WEATHER: ("clear", "cloudy", "rain", "snow"),
    ContextVariable.ACTIVITY: ("focus", "chill"),
}
SEMANTIC_ITEMS: tuple[SemanticItem, ...] = tuple(item for items in VARIABLE_ITEMS.values() for item in items)


class Salience(RootModel[dict[SemanticItem, FiniteFloat]]):
    """Validated model input; omitted semantic items have neutral evidence."""

    @model_validator(mode="after")
    def complete_vocabulary(self) -> Self:
        self.root = {item: self.root.get(item, 0.0) for item in SEMANTIC_ITEMS}
        return self
