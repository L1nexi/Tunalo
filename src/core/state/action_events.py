from __future__ import annotations

import logging

from core.models.event import EventLogger, EventType
from core.models.scheduling import Action
from core.models.trace import TickTrace

logger = logging.getLogger("Tunalo.Actions")


class ActionEventWriter:
    def __init__(self, event_logger: EventLogger) -> None:
        self._events = event_logger

    def on_tick(self, trace: TickTrace) -> None:
        schedule = trace.schedule
        decision = schedule.decision
        if decision.action != Action.APPLY:
            return

        result = schedule.action
        selection = schedule.selection
        logger.log(
            logging.INFO if result.executed else logging.WARNING,
            "Scene execution: tick_id=%d, mode=%s, executed=%s, selected_scene=%r, target_playlist=%r, probabilities=%s",
            trace.tick_id,
            schedule.mode.value,
            result.executed,
            result.selected_scene,
            result.target_playlist,
            selection.probabilities,
        )
        data: dict[str, object] = {
            "tick_id": trace.tick_id,
            "mode": schedule.mode.value,
            "target_playlist": result.target_playlist,
            "selected_scene": result.selected_scene,
        }
        if result.executed:
            event_type = EventType.SCENES_APPLIED
            data.update(
                {
                    "scenes_from": decision.timing.active_scenes.ids(),
                    "scenes_to": schedule.target.ids(),
                    "salience": {item: round(value, 4) for item, value in selection.salience.items()},
                    "probabilities": {scene_id: round(value, 4) for scene_id, value in selection.probabilities.items()},
                }
            )
        else:
            event_type = EventType.ACTUATION_FAILED
            data.update(
                {
                    "action": decision.action.value,
                    "matched_scenes": decision.target.ids(),
                    "active_scenes": decision.timing.active_scenes.ids(),
                }
            )
        self._events.write(event_type, data, ts=trace.ts)
