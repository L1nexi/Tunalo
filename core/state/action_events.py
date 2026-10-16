from __future__ import annotations

from core.models.event import EventLogger, EventType
from core.models.scheduling import Action
from core.models.trace import TickTrace


class ActionEventWriter:
    def __init__(self, event_logger: EventLogger):
        self._events = event_logger

    def on_tick(self, trace: TickTrace) -> None:
        result = trace.action
        selection = trace.selection
        decision = trace.decision

        if decision.action == Action.APPLY and result.executed:
            self._events.write(
                EventType.SCENES_APPLIED,
                {
                    "scenes_from": [scene_id.value for scene_id in trace.active_scenes.ids()],
                    "scenes_to": [scene_id.value for scene_id in trace.target.ids()],
                    "target_playlist": result.target_playlist,
                    "salience": {item: round(value, 4) for item, value in selection.salience.items()},
                    "probabilities": {scene_id.value: round(value, 4) for scene_id, value in selection.probabilities.items()},
                    "selected_scene": result.selected_scene,
                },
            )
        elif decision.action == Action.APPLY and not result.executed:
            self._events.write(
                EventType.ACTUATION_FAILED,
                {
                    "action": decision.action.value,
                    "matched_scenes": [scene_id.value for scene_id in decision.target.ids()],
                    "active_scenes": [scene_id.value for scene_id in trace.active_scenes.ids()],
                },
            )
