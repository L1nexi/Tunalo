from __future__ import annotations

from configurations.runtime_models import DisturbanceConfig, TimingConfig
from core.models.context import Context
from core.models.scene import SceneId
from core.models.scheduling import Action, ActPlan, Blocker, DecisionMode
from core.models.selection import Selection, SemanticItem
from core.runtime.act_plan import plan_actuation
from core.runtime.controller import Controller
from core.runtime.we_config import FactualPlaylistState, FactualPlaylistStatus


class MutableClock:
    def __init__(self, now: float) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def _controller(
    clock: MutableClock,
    *,
    startup_delay: float = 0,
    idle_threshold: float = 0,
) -> Controller:
    return Controller(
        TimingConfig(startup_delay=startup_delay, cycle_interval=900),
        DisturbanceConfig(idle_threshold=idle_threshold, cpu_threshold=80),
        {
            SceneId.DAY_WORK: frozenset({SemanticItem.DAY, SemanticItem.WORK}),
            SceneId.RAIN: frozenset({SemanticItem.RAIN}),
        },
        clock=clock,
    )


def test_controller_times_probability_change_from_the_successful_distribution() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock)
    previous = {SceneId.DAY_WORK: 0.5, SceneId.RAIN: 0.5}
    controller.notify_executed()
    selection = Selection(probabilities={SceneId.DAY_WORK: 0.125, SceneId.RAIN: 0.875}, salience={}, reason="best_effort")
    plan = plan_actuation(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.PLAYLIST, playlist="Other"),
        cached_scenes_probabilities=previous,
        paused=False,
        manual_requested=False,
    )

    actions = []
    for now in (130.0, 131.0):
        clock.now = now
        actions.append(controller.decide_action(plan, Context(), selection).action)

    assert actions == [Action.HOLD, Action.APPLY]


def test_controller_rechecks_current_distribution_after_a_blocked_tick() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, idle_threshold=20)
    previous = {SceneId.DAY_WORK: 0.5, SceneId.RAIN: 0.5}
    controller.notify_executed()
    plan = ActPlan(mode=DecisionMode.NORMAL, cached_scenes_probabilities=previous)
    changed = Selection(probabilities={SceneId.DAY_WORK: 0.125, SceneId.RAIN: 0.875}, salience={}, reason="best_effort")
    unchanged = Selection(probabilities=previous, salience={}, reason="best_effort")

    clock.now = 150.0
    blocked = controller.decide_action(plan, Context(idle=0), changed)
    clock.now = 151.0
    recovered = controller.decide_action(plan, Context(idle=30), unchanged)
    clock.now = 152.0
    ready = controller.decide_action(plan, Context(idle=30), changed)
    clock.now = 153.0
    retry = controller.decide_action(plan, Context(idle=30), changed)

    assert [blocked.action, recovered.action, ready.action, retry.action] == [Action.HOLD, Action.HOLD, Action.APPLY, Action.APPLY]


def test_controller_does_not_treat_a_tiny_new_candidate_as_an_immediate_switch() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock)
    previous = {SceneId.DAY_WORK: 1.0}
    controller.notify_executed()
    selection = Selection(probabilities={SceneId.DAY_WORK: 0.999, SceneId.RAIN: 0.001}, salience={}, reason="best_effort")
    plan = ActPlan(mode=DecisionMode.NORMAL, cached_scenes_probabilities=previous)

    actions = []
    for now in (999.0, 1000.0):
        clock.now = now
        actions.append(controller.decide_action(plan, Context(), selection).action)
    controller.notify_executed()
    clock.now = 1001.0
    applied_plan = ActPlan(mode=DecisionMode.NORMAL, cached_scenes_probabilities=selection.probabilities)
    actions.append(controller.decide_action(applied_plan, Context(), selection).action)

    assert actions == [Action.HOLD, Action.APPLY, Action.HOLD]


def test_controller_first_switch_needs_only_startup_grace() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, startup_delay=5)
    plan = ActPlan(mode=DecisionMode.NORMAL, cached_scenes_probabilities={})
    clock.now = 104.0
    before = controller.decide_action(plan, Context(), Selection(probabilities={SceneId.DAY_WORK: 1.0}, salience={}, reason="best_effort"))
    clock.now = 105.0
    after = controller.decide_action(plan, Context(), Selection(probabilities={SceneId.RAIN: 1.0}, salience={}, reason="best_effort"))

    assert [before.action, after.action] == [Action.HOLD, Action.APPLY]


def test_controller_never_bypasses_disturbance_checks_when_a_switch_is_due() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, idle_threshold=20)
    controller.notify_executed()
    clock.now = 3700.0

    decision = controller.decide_action(
        ActPlan(mode=DecisionMode.NORMAL, cached_scenes_probabilities={SceneId.DAY_WORK: 1.0}),
        Context(idle=5, cpu=90, fullscreen=True),
        Selection(probabilities={SceneId.RAIN: 1.0}, salience={}, reason="best_effort"),
    )

    assert decision.action == Action.HOLD
    assert set(decision.disturbance.blocked_by) == {Blocker.CPU, Blocker.FULLSCREEN, Blocker.IDLE}


def test_controller_recovery_switches_without_normal_execution_gates() -> None:
    controller = _controller(MutableClock(100.0), startup_delay=30, idle_threshold=60)
    decision = controller.decide_action(
        plan_actuation(
            factual=FactualPlaylistState(status=FactualPlaylistStatus.NO_PLAYLIST),
            cached_scenes_probabilities={SceneId.DAY_WORK: 1.0},
            paused=False,
            manual_requested=False,
        ),
        Context(idle=0, cpu=100, fullscreen=True),
        Selection(probabilities={SceneId.RAIN: 1.0}, salience={}, reason="best_effort"),
    )

    assert decision.action == Action.APPLY


def test_controller_recovery_without_a_selection_does_nothing() -> None:
    controller = _controller(MutableClock(100.0))
    decision = controller.decide_action(
        ActPlan(mode=DecisionMode.RECOVERY, cached_scenes_probabilities={SceneId.DAY_WORK: 1.0}),
        Context(),
        Selection(probabilities={}, salience={}, reason="no_safe_scenes"),
    )

    assert decision.action == Action.NONE


def test_controller_configuration_replacement_preserves_success_and_startup_times() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, startup_delay=30)
    controller.notify_executed()
    clock.now = 105.0
    replacement = _controller(clock, startup_delay=100)
    replacement.import_state(controller.export_state())
    clock.now = 131.0

    decision = replacement.decide_action(
        ActPlan(
            mode=DecisionMode.NORMAL,
            cached_scenes_probabilities={SceneId.DAY_WORK: 0.5, SceneId.RAIN: 0.5},
        ),
        Context(),
        Selection(probabilities={SceneId.DAY_WORK: 0.125, SceneId.RAIN: 0.875}, salience={}, reason="best_effort"),
    )

    assert decision.action == Action.APPLY
