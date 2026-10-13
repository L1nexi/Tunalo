from __future__ import annotations

from core.models.scene import SceneId, Scenes


def test_scene_pool_equality_ignores_order() -> None:
    assert Scenes([SceneId.DAY_WORK, SceneId.RAIN]) == Scenes([SceneId.RAIN, SceneId.DAY_WORK])
