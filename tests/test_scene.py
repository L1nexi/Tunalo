from __future__ import annotations

import pytest

from configurations.runtime_models import SceneConfig
from core.models.scene import SceneId, Scenes


@pytest.fixture(autouse=True)
def _reset_registry():
    Scenes.configure({})
    yield
    Scenes.configure({})


@pytest.fixture
def configured_scenes():
    Scenes.configure(
        {
            SceneId.DAY_WORK: SceneConfig(playlist="WORK", associations={"work"}, item_count=10),
            SceneId.NIGHT_WORK: SceneConfig(playlist="WORK", associations={"work"}, item_count=10),
            SceneId.RAIN: SceneConfig(playlist="RAIN", associations={"work"}, item_count=5),
            SceneId.SUNSET: SceneConfig(playlist="SUNSET", associations={"work"}, item_count=0),
        }
    )


def test_playlist_reverse_lookup_preserves_many_to_one_scenes(configured_scenes):
    assert Scenes.manages_playlist("WORK") is True
    assert Scenes.manages_playlist("UNKNOWN") is False
    assert Scenes.for_playlist("WORK") == Scenes([SceneId.DAY_WORK, SceneId.NIGHT_WORK])


def test_scene_pool_detects_target_playlist(configured_scenes):
    scenes = Scenes([SceneId.DAY_WORK, SceneId.RAIN])

    assert scenes.targets_playlist("WORK") is True
    assert scenes.targets_playlist("SUNSET") is False


def test_scene_pool_equality_ignores_order(configured_scenes):
    assert Scenes([SceneId.DAY_WORK, SceneId.RAIN]) == Scenes([SceneId.RAIN, SceneId.DAY_WORK])
