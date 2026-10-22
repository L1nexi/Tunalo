from __future__ import annotations

import logging
import random
from collections.abc import Mapping

from core.models.scene import SceneBinding, Scenes
from core.models.scheduling import Action, ActionResult, Decision
from core.runtime.executor import WEExecutor

logger = logging.getLogger("Tunalo.Actuator")


class Actuator:
    def __init__(self, executor: WEExecutor, scene_bindings: Mapping[str, SceneBinding]) -> None:
        self.executor = executor
        self.scene_bindings = scene_bindings

    def act(self, decision: Decision) -> ActionResult:
        if decision.action == Action.APPLY:
            target_scenes = decision.target
        else:
            target_scenes = Scenes()

        if not target_scenes:
            return ActionResult()

        scene_ids = target_scenes.ids()
        selected_scene = random.choices(scene_ids, weights=[decision.probabilities[scene_id] for scene_id in scene_ids], k=1)[0]
        target_playlist = self.scene_bindings[selected_scene].playlist
        logger.info("Applying scene '%s' via playlist '%s'", selected_scene, target_playlist)
        executed = bool(self.executor.open_playlist(target_playlist))

        return ActionResult(
            target_playlist=target_playlist,
            selected_scene=selected_scene,
            executed=executed,
        )
