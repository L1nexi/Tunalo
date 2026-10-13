from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SceneId(StrEnum):
    DAY_WORK = "day_work"
    DAY_LEISURE = "day_leisure"
    NIGHT_WORK = "night_work"
    NIGHT_LEISURE = "night_leisure"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    SUNSET = "sunset"
    RAIN = "rain"


@dataclass(frozen=True)
class SceneBinding:
    playlist: str


class Scenes:
    def __init__(self, ids: list[SceneId] | None = None) -> None:
        self._ids = list(dict.fromkeys(ids or []))

    def ids(self) -> list[SceneId]:
        return list(self._ids)

    def __len__(self) -> int:
        return len(self._ids)

    def __bool__(self) -> bool:
        return bool(self._ids)

    def __getitem__(self, index: int) -> SceneId:
        return self._ids[index]

    def __contains__(self, scene_id: object) -> bool:
        return scene_id in self._ids

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Scenes):
            return NotImplemented
        return set(self._ids) == set(other._ids)

    def __hash__(self) -> int:
        return hash(frozenset(self._ids))

    def __repr__(self) -> str:
        return f"Scenes({self._ids!r})"
