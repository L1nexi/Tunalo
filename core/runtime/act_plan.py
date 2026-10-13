from __future__ import annotations

from collections.abc import Mapping

from core.models.scene import SceneBinding, SceneId, Scenes
from core.models.scheduling import ActPlan, DecisionMode
from core.runtime.we_config import FactualPlaylistState
from core.runtime.we_config import FactualPlaylistStatus as Status


def plan_actuation(
    factual: FactualPlaylistState,
    cached_scenes: Scenes,
    paused: bool,
    manual_requested: bool,
    scene_bindings: Mapping[SceneId, SceneBinding],
) -> ActPlan:
    mode = DecisionMode.NORMAL
    active_scenes = Scenes([scene_id for scene_id in cached_scenes.ids() if scene_id in scene_bindings])

    if manual_requested:
        mode = DecisionMode.MANUAL
    elif paused:
        mode = DecisionMode.PAUSE
    elif factual.status == Status.NO_PLAYLIST:
        mode = DecisionMode.RECOVERY
        active_scenes = Scenes()
    elif factual.status == Status.PLAYLIST:
        playlist_scenes = Scenes([scene_id for scene_id, binding in scene_bindings.items() if binding.playlist == factual.playlist])
        if not playlist_scenes:
            mode = DecisionMode.RECOVERY
            active_scenes = Scenes()
        elif not any(scene_id in playlist_scenes for scene_id in active_scenes.ids()):
            active_scenes = playlist_scenes

    return ActPlan(mode=mode, active_scenes=active_scenes)
