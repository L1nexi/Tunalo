from __future__ import annotations

from core.models.scene import Scenes


def test_scene_pool_equality_ignores_order() -> None:
    assert Scenes(["day_work", "rain"]) == Scenes(["rain", "day_work"])
