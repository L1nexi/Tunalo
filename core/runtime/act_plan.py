from __future__ import annotations

from collections.abc import Mapping

from core.models.scene import SceneId
from core.models.scheduling import ActPlan, DecisionMode
from core.runtime.we_config import FactualPlaylistState
from core.runtime.we_config import FactualPlaylistStatus as Status


def plan_actuation(
    factual: FactualPlaylistState,
    cached_scenes_probabilities: Mapping[SceneId, float],
    paused: bool,
    manual_requested: bool,
) -> ActPlan:
    mode = DecisionMode.NORMAL

    if manual_requested:
        mode = DecisionMode.MANUAL
    elif paused:
        mode = DecisionMode.PAUSE
    elif factual.status == Status.NO_PLAYLIST:
        mode = DecisionMode.RECOVERY

    return ActPlan(mode=mode, cached_scenes_probabilities=dict(cached_scenes_probabilities))
