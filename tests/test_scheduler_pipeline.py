from __future__ import annotations

from pathlib import Path

import pytest

from core.models.context import Context
from core.models.scene import SceneId, Scenes
from core.models.scheduling import Action, ActionResult, ActPlan, Decision, DecisionMode, ScheduleResult
from core.models.selection import Selection
from core.state.persisted import PersistedState
from core.state.scheduler import SchedulerState


@pytest.fixture
def state_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "state.json"
    save = PersistedState.save

    def save_to_test_file(state: PersistedState) -> None:
        save(state, str(path))

    # 仅重定向文件路径，继续使用真实的持久化保存和加载实现。
    monkeypatch.setattr(PersistedState, "save", save_to_test_file)
    return path


@pytest.fixture
def switch_result() -> ScheduleResult:
    return ScheduleResult(
        context=Context(),
        selection=Selection(probabilities={SceneId.RAIN: 1.0}, salience={}, reason="best_effort"),
        plan=ActPlan(mode=DecisionMode.NORMAL, active_scenes=Scenes([SceneId.DAY_WORK])),
        decision=Decision(action=Action.SWITCH, target=Scenes([SceneId.RAIN]), probabilities={SceneId.RAIN: 1.0}),
        action=ActionResult(target_playlist="RAIN", selected_scene=SceneId.RAIN, executed=True),
    )


def test_manual_apply_request_is_consumed_once() -> None:
    s = SchedulerState()
    s.request_manual_apply()
    assert s.consume_manual_apply_request() is True
    assert s.consume_manual_apply_request() is False


def test_executed_switch_commits_new_scenes_and_persists_state(state_file: Path, switch_result: ScheduleResult) -> None:
    state = SchedulerState(cached_scenes=Scenes([SceneId.DAY_WORK]))
    trace = state.attach_metadata(switch_result)

    state.commit(trace)

    assert state.cached_scenes == Scenes([SceneId.RAIN])
    assert PersistedState.load(str(state_file)).cached_scenes == [SceneId.RAIN]
    assert state.last_tick_trace is trace
    assert trace.target == Scenes([SceneId.RAIN])


@pytest.mark.parametrize(
    ("action", "execution_result", "target_scene", "active_scene"),
    [
        (Action.SWITCH, ActionResult("RAIN", SceneId.RAIN, False), SceneId.RAIN, SceneId.DAY_WORK),
        (Action.CYCLE, ActionResult("WORK", SceneId.DAY_WORK, True), SceneId.DAY_WORK, SceneId.DAY_WORK),
        (Action.HOLD, ActionResult(), SceneId.RAIN, SceneId.DAY_WORK),
        (Action.PAUSE, ActionResult(), SceneId.RAIN, SceneId.DAY_WORK),
        (Action.NONE, ActionResult(), None, None),
    ],
)
def test_unsuccessful_switch_and_other_actions_preserve_cached_state(
    state_file: Path,
    switch_result: ScheduleResult,
    action: Action,
    execution_result: ActionResult,
    target_scene: SceneId | None,
    active_scene: SceneId | None,
) -> None:
    state = SchedulerState(cached_scenes=Scenes([SceneId.DAY_WORK]))
    state.save()
    persisted_before = state_file.read_bytes()
    probabilities = {target_scene: 1.0} if target_scene else {}
    switch_result.selection = Selection(probabilities=probabilities, salience={}, reason="best_effort" if target_scene else "no_safe_scenes")
    switch_result.decision.action = action
    switch_result.decision.target = Scenes([target_scene] if target_scene else [])
    switch_result.decision.probabilities = probabilities
    switch_result.action = execution_result
    switch_result.plan = ActPlan(
        mode=DecisionMode.PAUSE if action == Action.PAUSE else DecisionMode.NORMAL,
        active_scenes=Scenes([active_scene] if active_scene else []),
    )
    trace = state.attach_metadata(switch_result)

    state.commit(trace)

    assert state.cached_scenes == Scenes([SceneId.DAY_WORK])
    assert PersistedState.load(str(state_file)).cached_scenes == [SceneId.DAY_WORK]
    assert state_file.read_bytes() == persisted_before
    assert state.last_tick_trace is trace
    assert trace.target == Scenes([active_scene] if active_scene else [])


def test_switch_to_cached_scenes_leaves_persisted_file_unchanged(state_file: Path, switch_result: ScheduleResult) -> None:
    state = SchedulerState(cached_scenes=Scenes([SceneId.RAIN]))
    state.save()
    # 保留合法 JSON 的额外换行，确保一次多余保存不会被相同内容掩盖。
    persisted_before = state_file.read_bytes() + b"\n"
    state_file.write_bytes(persisted_before)
    trace = state.attach_metadata(switch_result)

    state.commit(trace)

    assert state.cached_scenes == Scenes([SceneId.RAIN])
    assert state_file.read_bytes() == persisted_before
    assert state.last_tick_trace is trace
