from core.models.scheduling import DecisionMode
from core.runtime.we_config import FactualPlaylistState, FactualPlaylistStatus


def deduce_mode(factual: FactualPlaylistState, paused: bool, manual_requested: bool) -> DecisionMode:
    if manual_requested:
        return DecisionMode.MANUAL
    if paused:
        return DecisionMode.PAUSE
    if factual.status == FactualPlaylistStatus.NO_PLAYLIST:
        return DecisionMode.RECOVERY
    return DecisionMode.NORMAL
