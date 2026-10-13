from __future__ import annotations

import pytest

from core.models.scene import SceneBinding, SceneId, Scenes
from core.models.scheduling import DecisionMode
from core.runtime.act_plan import plan_actuation
from core.runtime.we_config import FactualPlaylistState, FactualPlaylistStatus


@pytest.fixture
def scene_bindings() -> dict[SceneId, SceneBinding]:
    return {
        SceneId.DAY_WORK: SceneBinding(playlist="A"),
        SceneId.DAY_LEISURE: SceneBinding(playlist="A"),
        SceneId.NIGHT_WORK: SceneBinding(playlist="B"),
        SceneId.RAIN: SceneBinding(playlist="C"),
    }


def test_manual_requested_takes_priority_over_paused(scene_bindings: dict[SceneId, SceneBinding]) -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.UNKNOWN),
        cached_scenes=Scenes([SceneId.DAY_WORK]),
        paused=True,
        manual_requested=True,
        scene_bindings=scene_bindings,
    )
    assert plan.mode == DecisionMode.MANUAL


def test_paused_takes_priority_over_recovery(scene_bindings: dict[SceneId, SceneBinding]) -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.NO_PLAYLIST),
        cached_scenes=Scenes([SceneId.DAY_WORK]),
        paused=True,
        manual_requested=False,
        scene_bindings=scene_bindings,
    )
    assert plan.mode == DecisionMode.PAUSE


def test_no_factual_playlist_triggers_recovery_when_not_paused(scene_bindings: dict[SceneId, SceneBinding]) -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.NO_PLAYLIST),
        cached_scenes=Scenes([SceneId.DAY_WORK]),
        paused=False,
        manual_requested=False,
        scene_bindings=scene_bindings,
    )
    assert plan.mode == DecisionMode.RECOVERY


def test_unmanaged_factual_playlist_triggers_recovery(scene_bindings: dict[SceneId, SceneBinding]) -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.PLAYLIST, playlist="Other"),
        cached_scenes=Scenes([SceneId.DAY_WORK]),
        paused=False,
        manual_requested=False,
        scene_bindings=scene_bindings,
    )
    assert plan.mode == DecisionMode.RECOVERY
    assert plan.active_scenes == Scenes()


def test_factual_playlist_targeted_by_cached_scene_preserves_cached_pool(scene_bindings: dict[SceneId, SceneBinding]) -> None:
    cached = Scenes([SceneId.DAY_WORK, SceneId.NIGHT_WORK])

    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.PLAYLIST, playlist="A"),
        cached_scenes=cached,
        paused=False,
        manual_requested=False,
        scene_bindings=scene_bindings,
    )

    assert plan.mode == DecisionMode.NORMAL
    assert plan.active_scenes == cached


def test_factual_playlist_outside_cache_recovers_every_bound_scene(scene_bindings: dict[SceneId, SceneBinding]) -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.PLAYLIST, playlist="A"),
        cached_scenes=Scenes([SceneId.RAIN]),
        paused=False,
        manual_requested=False,
        scene_bindings=scene_bindings,
    )

    assert plan.active_scenes == Scenes([SceneId.DAY_WORK, SceneId.DAY_LEISURE])


@pytest.mark.parametrize("status", [FactualPlaylistStatus.UNKNOWN, FactualPlaylistStatus.AMBIGUOUS])
def test_unknown_factual_state_preserves_cached_scenes(status: FactualPlaylistStatus, scene_bindings: dict[SceneId, SceneBinding]) -> None:
    cached = Scenes([SceneId.DAY_WORK, SceneId.NIGHT_WORK])

    plan = plan_actuation(
        factual=FactualPlaylistState(status=status),
        cached_scenes=cached,
        paused=False,
        manual_requested=False,
        scene_bindings=scene_bindings,
    )

    assert plan.mode == DecisionMode.NORMAL
    assert plan.active_scenes == cached


def test_cached_scene_removed_from_runtime_is_discarded(scene_bindings: dict[SceneId, SceneBinding]) -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.UNKNOWN),
        cached_scenes=Scenes([SceneId.WINTER]),
        paused=False,
        manual_requested=False,
        scene_bindings=scene_bindings,
    )

    assert plan.active_scenes == Scenes()
