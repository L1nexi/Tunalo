from __future__ import annotations

import pytest

from core.models.scene import SceneId, Scenes
from core.models.scheduling import DecisionMode
from core.runtime.act_plan import plan_actuation
from core.runtime.we_config import FactualPlaylistState, FactualPlaylistStatus


def test_manual_requested_takes_priority_over_paused() -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.UNKNOWN),
        cached_scenes_probabilities={SceneId.DAY_WORK: 1.0},
        paused=True,
        manual_requested=True,
    )
    assert plan.mode == DecisionMode.MANUAL


def test_paused_takes_priority_over_recovery() -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.NO_PLAYLIST),
        cached_scenes_probabilities={SceneId.DAY_WORK: 1.0},
        paused=True,
        manual_requested=False,
    )
    assert plan.mode == DecisionMode.PAUSE


def test_no_factual_playlist_triggers_recovery_when_not_paused() -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.NO_PLAYLIST),
        cached_scenes_probabilities={SceneId.DAY_WORK: 1.0},
        paused=False,
        manual_requested=False,
    )
    assert plan.mode == DecisionMode.RECOVERY


def test_unmanaged_factual_playlist_preserves_normal_scheduling() -> None:
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.PLAYLIST, playlist="Other"),
        cached_scenes_probabilities={SceneId.DAY_WORK: 1.0},
        paused=False,
        manual_requested=False,
    )
    assert plan.mode == DecisionMode.NORMAL


def test_factual_playlist_targeted_by_cached_scene_preserves_cached_pool() -> None:
    cached = {SceneId.DAY_WORK: 0.75, SceneId.NIGHT_WORK: 0.25}

    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.PLAYLIST, playlist="A"),
        cached_scenes_probabilities=cached,
        paused=False,
        manual_requested=False,
    )

    assert plan.mode == DecisionMode.NORMAL
    assert plan.active_scenes == Scenes(list(cached))


@pytest.mark.parametrize("status", [FactualPlaylistStatus.UNKNOWN, FactualPlaylistStatus.AMBIGUOUS])
def test_unknown_factual_state_preserves_cached_scenes(status: FactualPlaylistStatus) -> None:
    cached = {SceneId.DAY_WORK: 0.75, SceneId.NIGHT_WORK: 0.25}

    plan = plan_actuation(
        factual=FactualPlaylistState(status=status),
        cached_scenes_probabilities=cached,
        paused=False,
        manual_requested=False,
    )

    assert plan.mode == DecisionMode.NORMAL
    assert plan.active_scenes == Scenes(list(cached))
