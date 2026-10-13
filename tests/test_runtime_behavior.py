from __future__ import annotations

from configurations.runtime_models import SchedulingConfig
from core.models.context import Context
from core.models.scene import SceneId, Scenes
from core.models.scheduling import Action, ActPlan, Blocker, Decision, DecisionMode
from core.models.selection import Selection
from core.runtime.controller import Controller


class MutableClock:
    def __init__(self, now: float):
        self.now = now

    def __call__(self) -> float:
        return self.now


def _controller(clock: MutableClock, **overrides) -> Controller:
    values = {
        "startup_delay": 0,
        "force_after": 100,
        "cycle_cooldown": 15,
        "idle_threshold": 60,
        "cpu_threshold": 80,
        "cpu_sample_window": 1,
        "pause_on_fullscreen": True,
    }
    values.update(overrides)
    return Controller(SchedulingConfig(**values), clock=clock)


def _decide_normal(
    controller: Controller,
    context: Context,
    matched: list[SceneId],
    active: list[SceneId],
):
    return controller.decide_action(
        ActPlan(mode=DecisionMode.NORMAL, active_scenes=Scenes(active)),
        context,
        Selection(probabilities={scene_id: 1 / len(matched) for scene_id in matched}, salience={}, reason="best_effort"),
    )


def test_controller_reports_every_reason_that_blocks_an_action():
    clock = MutableClock(195.0)
    controller = _controller(clock)
    controller.notify_executed(Decision(action=Action.CYCLE, target=Scenes([SceneId.DAY_WORK])))
    clock.now = 200.0

    switch = _decide_normal(
        controller,
        Context(idle=10.0, cpu=90.0, fullscreen=True),
        [SceneId.RAIN],
        [SceneId.DAY_WORK],
    )
    cycle = _decide_normal(
        controller,
        Context(idle=10.0, cpu=90.0, fullscreen=True),
        [SceneId.DAY_WORK],
        [SceneId.DAY_WORK],
    )

    assert set(switch.evaluation.blocked_by) == {Blocker.CPU, Blocker.FULLSCREEN, Blocker.IDLE}
    assert set(cycle.evaluation.blocked_by) == {
        Blocker.COOLDOWN,
        Blocker.CPU,
        Blocker.FULLSCREEN,
        Blocker.IDLE,
    }


def test_controller_blocks_switch_and_cycle_during_startup_grace():
    clock = MutableClock(100.0)
    controller = _controller(clock, startup_delay=30)
    clock.now = 105.0
    context = Context(idle=120.0, cpu=90.0, fullscreen=True)

    switch = _decide_normal(controller, context, [SceneId.RAIN], [SceneId.DAY_WORK])
    cycle = _decide_normal(controller, context, [SceneId.DAY_WORK], [SceneId.DAY_WORK])

    assert switch.action == Action.HOLD
    assert Blocker.COOLDOWN in switch.evaluation.blocked_by
    assert cycle.action == Action.HOLD
    assert Blocker.COOLDOWN in cycle.evaluation.blocked_by


def test_controller_allows_switch_after_startup_grace():
    clock = MutableClock(100.0)
    controller = _controller(
        clock,
        startup_delay=10,
        cpu_threshold=0,
        pause_on_fullscreen=False,
    )
    clock.now = 120.0

    decision = _decide_normal(controller, Context(idle=80.0, cpu=1.0), [SceneId.RAIN], [SceneId.DAY_WORK])

    assert decision.action == Action.SWITCH


def test_controller_does_not_apply_cycle_cooldown_to_switches():
    clock = MutableClock(100.0)
    controller = _controller(
        clock,
        force_after=3600,
        cycle_cooldown=900,
        idle_threshold=10,
        cpu_threshold=0,
        pause_on_fullscreen=False,
    )
    controller.notify_executed(Decision(action=Action.SWITCH, target=Scenes([SceneId.DAY_WORK]), probabilities={SceneId.DAY_WORK: 1}))
    clock.now = 101.0

    decision = _decide_normal(controller, Context(idle=20.0, cpu=1.0), [SceneId.RAIN], [SceneId.DAY_WORK])

    assert decision.action == Action.SWITCH
    assert Blocker.COOLDOWN not in decision.evaluation.blocked_by


def test_controller_forces_a_deferred_switch_after_the_limit():
    clock = MutableClock(390.0)
    controller = _controller(clock, cpu_threshold=0, pause_on_fullscreen=False)
    controller.notify_executed(Decision(action=Action.SWITCH, target=Scenes([SceneId.DAY_WORK]), probabilities={SceneId.DAY_WORK: 1}))
    clock.now = 500.0

    decision = _decide_normal(controller, Context(idle=5.0, cpu=1.0), [SceneId.RAIN], [SceneId.DAY_WORK])

    assert decision.action == Action.SWITCH
    assert decision.evaluation.blocked_by == []


def test_controller_switches_immediately_when_candidate_sets_differ():
    clock = MutableClock(1_000.0)
    controller = _controller(
        clock,
        force_after=0,
        cycle_cooldown=0,
        idle_threshold=0,
        cpu_threshold=0,
        pause_on_fullscreen=False,
    )

    decisions = [
        _decide_normal(
            controller,
            Context(idle=999.0),
            [SceneId.SPRING, SceneId.AUTUMN],
            [SceneId.SPRING, SceneId.SUMMER],
        )
        for _ in range(2)
    ]

    assert all(decision.action == Action.SWITCH for decision in decisions)


def test_controller_recovery_switches_to_a_match_without_context_gates():
    controller = _controller(MutableClock(100.0), startup_delay=30)

    decision = controller.decide_action(
        ActPlan(mode=DecisionMode.RECOVERY, active_scenes=Scenes()),
        Context(idle=0.0, cpu=100.0, fullscreen=True),
        Selection(probabilities={SceneId.RAIN: 1}, salience={}, reason="best_effort"),
    )

    assert decision.action == Action.SWITCH
    assert decision.evaluation is None


def test_controller_recovery_without_a_match_does_nothing():
    controller = _controller(MutableClock(100.0))

    decision = controller.decide_action(
        ActPlan(mode=DecisionMode.RECOVERY, active_scenes=Scenes()),
        Context(),
        Selection(probabilities={}, salience={}, reason="no_safe_scenes"),
    )

    assert decision.action == Action.NONE
