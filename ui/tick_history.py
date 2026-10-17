from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from core.models.context import WeatherData
from core.models.scene import SceneId, Scenes
from core.models.scheduling import Action, Blocker, DisturbanceEvaluation, TimingEvaluation
from core.models.selection import ActivityEvaluation, PolicyEvaluation, SeasonEvaluation, TimeEvaluation, WeatherEvaluation
from core.models.trace import TickTrace
from core.state.tick_history import TickHistoryWindow


def _round_float(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _playlist_or_none(playlist: str | None) -> str | None:
    """Scheduler internals use empty string for "no playlist"; API uses null."""
    if not playlist:
        return None
    return playlist


def _sorted_tag_items(items: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(items.items(), key=lambda item: (-item[1], item[0]))


class ApiDto(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class SemanticSalienceDto(ApiDto):
    item: str
    value: float


class WindowSnapshotDto(ApiDto):
    process: str
    title: str


class IdleSnapshotDto(ApiDto):
    seconds: float


class CpuSnapshotDto(ApiDto):
    average_percent: float


class WeatherSnapshotDto(ApiDto):
    available: bool
    id: int | None
    main: str | None
    sunrise: int | None
    sunset: int | None


class ClockSnapshotDto(ApiDto):
    local_ts: int
    hour: int
    day_of_year: int


class ActivityDetailsDto(ApiDto):
    match_source: str
    matched_rule: str | None
    matched_tag: str | None
    window_title: str
    process: str


class TimeDetailsDto(ApiDto):
    hour: float
    virtual_hour: float | None
    day_start_hour: float | None
    night_start_hour: float | None
    peaks: dict[str, float]


class SeasonDetailsDto(ApiDto):
    day_of_year: int
    peaks: dict[str, int]


class WeatherDetailsDto(ApiDto):
    weather_id: int | None
    weather_main: str | None
    available: bool
    mapped: bool


class BaseEvaluationDto(ApiDto):
    policy_id: str
    salience: list[SemanticSalienceDto]


class ActivityEvaluationDto(BaseEvaluationDto):
    details: ActivityDetailsDto


class TimeEvaluationDto(BaseEvaluationDto):
    details: TimeDetailsDto


class SeasonEvaluationDto(BaseEvaluationDto):
    details: SeasonDetailsDto


class WeatherEvaluationDto(BaseEvaluationDto):
    details: WeatherDetailsDto


EvaluationDto = ActivityEvaluationDto | TimeEvaluationDto | SeasonEvaluationDto | WeatherEvaluationDto


class DisturbanceEvaluationDto(ApiDto):
    allowed: bool
    blocked_by: list[Blocker]
    idle_seconds: float
    idle_threshold: float
    cpu_percent: float
    cpu_threshold: float | None
    fullscreen: bool


class TimingEvaluationDto(ApiDto):
    ready: bool
    distance: float | None
    reference_distance: float
    interval: float | None
    elapsed: float
    startup_remaining: float
    remaining: float | None


class ControllerDto(ApiDto):
    timing: TimingEvaluationDto
    disturbance: DisturbanceEvaluationDto


class PlaylistRefDto(ApiDto):
    name: str


class SceneRefDto(ApiDto):
    id: SceneId


class ActionDecisionDto(ApiDto):
    action: Action
    executed: bool
    active_scenes: list[SceneRefDto]
    target_scenes: list[SceneRefDto]
    candidate_scenes: list[SceneRefDto]
    target_playlist: PlaylistRefDto | None
    selected_scene: SceneRefDto | None


class SceneProbabilityDto(ApiDto):
    scene: SceneRefDto
    probability: float


class SelectionExplanationDto(ApiDto):
    reason: str
    selected_tier: int | None
    sources: list[str]
    excluded_scenes: dict[SceneId, list[str]]


class SenseSnapshotDto(ApiDto):
    window: WindowSnapshotDto
    idle: IdleSnapshotDto
    cpu: CpuSnapshotDto
    fullscreen: bool
    weather: WeatherSnapshotDto
    clock: ClockSnapshotDto


class ThinkSnapshotDto(ApiDto):
    salience: list[SemanticSalienceDto]
    selection: SelectionExplanationDto
    policies: list[EvaluationDto]
    controller: ControllerDto
    decision: ActionDecisionDto


class ActSnapshotDto(ApiDto):
    scene_probabilities: list[SceneProbabilityDto]


class TickSummaryDto(ApiDto):
    tick_id: int
    ts: float
    selection_reason: str
    active_scenes: list[SceneRefDto]
    candidate_scenes: list[SceneRefDto]
    action: Action
    paused: bool
    executed: bool
    has_event: bool


class TickSnapshotDto(ApiDto):
    summary: TickSummaryDto
    sense: SenseSnapshotDto
    think: ThinkSnapshotDto
    act: ActSnapshotDto


class TickWindowResponseDto(ApiDto):
    live_tick_id: int | None
    ticks: list[TickSnapshotDto]


def _scene_ref(scene_id: SceneId) -> SceneRefDto:
    return SceneRefDto(id=scene_id)


def _scene_refs(scenes: Scenes) -> list[SceneRefDto]:
    return [_scene_ref(scene_id) for scene_id in scenes.ids()]


def _playlist_ref(playlist: str | None) -> PlaylistRefDto | None:
    normalized_playlist = _playlist_or_none(playlist)
    if normalized_playlist is None:
        return None
    return PlaylistRefDto(name=normalized_playlist)


def _salience_values(values: dict[str, float]) -> list[SemanticSalienceDto]:
    return [SemanticSalienceDto(item=item, value=_round_float(value)) for item, value in _sorted_tag_items(values)]


def _weather_snapshot(weather: WeatherData | None) -> WeatherSnapshotDto:
    if weather is None:
        return WeatherSnapshotDto(
            available=False,
            id=None,
            main=None,
            sunrise=None,
            sunset=None,
        )
    return WeatherSnapshotDto(
        available=True,
        id=weather.id or None,
        main=weather.main or None,
        sunrise=weather.sunrise or None,
        sunset=weather.sunset or None,
    )


def _clock_snapshot(local_time: time.struct_time) -> ClockSnapshotDto:
    return ClockSnapshotDto(
        local_ts=int(time.mktime(local_time)),
        hour=local_time.tm_hour,
        day_of_year=local_time.tm_yday,
    )


def _policy_base_dto(policy: PolicyEvaluation) -> BaseEvaluationDto:
    return BaseEvaluationDto(
        policy_id=policy.policy_id,
        salience=_salience_values(policy.salience),
    )


def _policy_snapshot(policy: PolicyEvaluation) -> EvaluationDto:
    base_dto = _policy_base_dto(policy)
    base_kwargs = base_dto.model_dump()
    if isinstance(policy, ActivityEvaluation):
        return ActivityEvaluationDto(
            **base_kwargs,
            details=ActivityDetailsDto(
                match_source=policy.details.match_source,
                matched_rule=policy.details.matched_rule,
                matched_tag=policy.details.matched_tag,
                window_title=policy.details.window_title,
                process=policy.details.process,
            ),
        )
    if isinstance(policy, TimeEvaluation):
        return TimeEvaluationDto(
            **base_kwargs,
            details=TimeDetailsDto(
                hour=_round_float(policy.details.hour),
                virtual_hour=_round_float(policy.details.virtual_hour),
                day_start_hour=_round_float(policy.details.day_start_hour),
                night_start_hour=_round_float(policy.details.night_start_hour),
                peaks={key: _round_float(value) for key, value in sorted(policy.details.peaks.items())},
            ),
        )
    if isinstance(policy, SeasonEvaluation):
        return SeasonEvaluationDto(
            **base_kwargs,
            details=SeasonDetailsDto(
                day_of_year=policy.details.day_of_year,
                peaks=dict(sorted(policy.details.peaks.items())),
            ),
        )
    if isinstance(policy, WeatherEvaluation):
        return WeatherEvaluationDto(
            **base_kwargs,
            details=WeatherDetailsDto(
                weather_id=policy.details.weather_id,
                weather_main=policy.details.weather_main,
                available=policy.details.available,
                mapped=policy.details.mapped,
            ),
        )
    raise TypeError(f"Unsupported policy evaluation type: {type(policy)!r}")


def _disturbance_evaluation(
    evaluation: DisturbanceEvaluation,
) -> DisturbanceEvaluationDto:
    return DisturbanceEvaluationDto(
        allowed=evaluation.allowed,
        blocked_by=list(evaluation.blocked_by),
        idle_seconds=_round_float(evaluation.idle_seconds),
        idle_threshold=_round_float(evaluation.idle_threshold),
        cpu_percent=_round_float(evaluation.cpu_percent),
        cpu_threshold=_round_float(evaluation.cpu_threshold),
        fullscreen=evaluation.fullscreen,
    )


def _timing_evaluation(evaluation: TimingEvaluation) -> TimingEvaluationDto:
    return TimingEvaluationDto(
        ready=evaluation.ready,
        distance=_round_float(evaluation.distance),
        reference_distance=_round_float(evaluation.reference_distance),
        interval=_round_float(evaluation.interval),
        elapsed=_round_float(evaluation.elapsed),
        startup_remaining=_round_float(evaluation.startup_remaining),
        remaining=_round_float(evaluation.remaining),
    )


def map_tick_snapshot(trace: TickTrace) -> TickSnapshotDto:
    candidate_scene_refs = _scene_refs(trace.selection.scenes)
    action_candidate_scene_refs = _scene_refs(trace.decision.target)
    target_refs = _scene_refs(trace.target)
    active_scene_refs = _scene_refs(trace.decision.timing.active_scenes)
    target_playlist_ref = _playlist_ref(trace.action.target_playlist)
    has_event = trace.decision.action == Action.APPLY

    return TickSnapshotDto(
        summary=TickSummaryDto(
            tick_id=trace.tick_id,
            ts=trace.ts,
            selection_reason=trace.selection.reason,
            active_scenes=target_refs,
            candidate_scenes=candidate_scene_refs,
            action=trace.decision.action,
            paused=trace.paused,
            executed=trace.action.executed,
            has_event=has_event,
        ),
        sense=SenseSnapshotDto(
            window=WindowSnapshotDto(
                process=trace.context.window.process or "",
                title=trace.context.window.title or "",
            ),
            idle=IdleSnapshotDto(seconds=_round_float(trace.context.idle)),
            cpu=CpuSnapshotDto(average_percent=_round_float(trace.context.cpu)),
            fullscreen=trace.context.fullscreen,
            weather=_weather_snapshot(trace.context.weather),
            clock=_clock_snapshot(trace.context.time),
        ),
        think=ThinkSnapshotDto(
            salience=_salience_values(trace.selection.salience),
            selection=SelectionExplanationDto(
                reason=trace.selection.reason,
                selected_tier=trace.selection.selected_tier,
                sources=trace.selection.sources,
                excluded_scenes={scene_id: sorted(items) for scene_id, items in trace.selection.excluded_scenes.items()},
            ),
            policies=[_policy_snapshot(policy) for policy in trace.selection.policy_evaluations],
            controller=ControllerDto(
                timing=_timing_evaluation(trace.decision.timing),
                disturbance=_disturbance_evaluation(trace.decision.disturbance),
            ),
            decision=ActionDecisionDto(
                action=trace.decision.action,
                executed=trace.action.executed,
                active_scenes=active_scene_refs,
                target_scenes=target_refs,
                candidate_scenes=action_candidate_scene_refs,
                target_playlist=target_playlist_ref,
                selected_scene=_scene_ref(trace.action.selected_scene) if trace.action.selected_scene is not None else None,
            ),
        ),
        act=ActSnapshotDto(
            scene_probabilities=[
                SceneProbabilityDto(
                    scene=_scene_ref(scene_id),
                    probability=_round_float(probability),
                )
                for scene_id, probability in sorted(trace.selection.probabilities.items(), key=lambda item: (-item[1], item[0]))
            ],
        ),
    )


def build_tick_snapshot(trace: TickTrace) -> dict[str, Any]:
    snapshot = map_tick_snapshot(trace)
    return snapshot.model_dump(mode="json", by_alias=True)


def build_tick_window_response(window: TickHistoryWindow) -> dict[str, Any]:
    response = TickWindowResponseDto(
        live_tick_id=window.live_tick_id,
        ticks=[map_tick_snapshot(trace) for trace in window.traces],
    )
    return response.model_dump(mode="json", by_alias=True)
