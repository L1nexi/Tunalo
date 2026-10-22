from __future__ import annotations

import pytest

from configurations.runtime_models import DisturbanceConfig, TimingConfig
from core.models.association import Association
from core.models.context import Context
from core.models.scene import Scenes
from core.models.scheduling import Action, Blocker, DecisionMode
from core.models.selection import Selection, SemanticItem
from core.runtime.controller import Controller
from core.runtime.deduce_mode import deduce_mode
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
            "day_work": Association(SemanticItem.DAY, SemanticItem.WORK),
            "rain": Association(SemanticItem.RAIN),
        },
        clock=clock,
    )


@pytest.mark.parametrize(
    "mode, expected",
    [
        (DecisionMode.NORMAL, Action.NOOP),
        (DecisionMode.MANUAL, Action.APPLY),
        (DecisionMode.RECOVERY, Action.APPLY),
        (DecisionMode.PAUSE, Action.PAUSE),
    ],
)
def test_controller_returns_evaluations_in_every_mode_without_advancing_success(mode: DecisionMode, expected: Action) -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, startup_delay=30, idle_threshold=20)
    controller.notify_executed(
        controller.decide_action(DecisionMode.MANUAL, Context(), Selection(probabilities={"day_work": 1.0}, salience={}, reason="best_effort"))
    )
    selection = Selection(probabilities={"rain": 1.0}, salience={}, reason="best_effort")
    clock.now = 101.0

    decision = controller.decide_action(mode, Context(idle=0, cpu=100, fullscreen=True), selection)

    assert decision.action == expected
    assert decision.timing.active_scenes == Scenes(["day_work"])
    assert not decision.timing.ready
    assert set(decision.disturbance.blocked_by) == {Blocker.IDLE, Blocker.CPU, Blocker.FULLSCREEN}

    clock.now = 131.0
    following = controller.decide_action(DecisionMode.NORMAL, Context(idle=30), selection)

    assert following.action == Action.APPLY
    assert following.timing.active_scenes == Scenes(["day_work"])
    assert following.timing.elapsed == 31.0


@pytest.mark.parametrize(
    "factual",
    [
        FactualPlaylistState(status=FactualPlaylistStatus.PLAYLIST, playlist="Other"),
        FactualPlaylistState(status=FactualPlaylistStatus.UNKNOWN),
        FactualPlaylistState(status=FactualPlaylistStatus.AMBIGUOUS),
    ],
)
def test_controller_times_probability_change_from_the_successful_distribution(factual: FactualPlaylistState) -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock)
    previous = {"day_work": 0.5, "rain": 0.5}
    controller.notify_executed(
        controller.decide_action(DecisionMode.MANUAL, Context(), Selection(probabilities=previous, salience={}, reason="best_effort"))
    )
    selection = Selection(probabilities={"day_work": 0.125, "rain": 0.875}, salience={}, reason="best_effort")
    mode = deduce_mode(
        factual=factual,
        paused=False,
        manual_requested=False,
    )

    actions = []
    for now in (130.0, 131.0):
        clock.now = now
        actions.append(controller.decide_action(mode, Context(), selection).action)

    assert actions == [Action.NOOP, Action.APPLY]


def test_controller_rechecks_current_distribution_after_a_blocked_tick() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, idle_threshold=20)
    previous = {"day_work": 0.5, "rain": 0.5}
    controller.notify_executed(
        controller.decide_action(DecisionMode.MANUAL, Context(), Selection(probabilities=previous, salience={}, reason="best_effort"))
    )
    changed = Selection(probabilities={"day_work": 0.125, "rain": 0.875}, salience={}, reason="best_effort")
    unchanged = Selection(probabilities=previous, salience={}, reason="best_effort")

    clock.now = 150.0
    blocked = controller.decide_action(DecisionMode.NORMAL, Context(idle=0), changed)
    clock.now = 151.0
    recovered = controller.decide_action(DecisionMode.NORMAL, Context(idle=30), unchanged)
    clock.now = 152.0
    ready = controller.decide_action(DecisionMode.NORMAL, Context(idle=30), changed)
    clock.now = 153.0
    retry = controller.decide_action(DecisionMode.NORMAL, Context(idle=30), changed)

    assert [blocked.action, recovered.action, ready.action, retry.action] == [Action.NOOP, Action.NOOP, Action.APPLY, Action.APPLY]


def test_controller_does_not_treat_a_tiny_new_candidate_as_an_immediate_switch() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock)
    previous = {"day_work": 1.0}
    controller.notify_executed(
        controller.decide_action(DecisionMode.MANUAL, Context(), Selection(probabilities=previous, salience={}, reason="best_effort"))
    )
    selection = Selection(probabilities={"day_work": 0.999, "rain": 0.001}, salience={}, reason="best_effort")

    actions = []
    for now in (999.0, 1000.0):
        clock.now = now
        decision = controller.decide_action(DecisionMode.NORMAL, Context(), selection)
        actions.append(decision.action)
    controller.notify_executed(decision)
    clock.now = 1001.0
    actions.append(controller.decide_action(DecisionMode.NORMAL, Context(), selection).action)

    assert actions == [Action.NOOP, Action.APPLY, Action.NOOP]


def test_controller_first_switch_needs_only_startup_grace() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, startup_delay=5)
    clock.now = 104.0
    before = controller.decide_action(DecisionMode.NORMAL, Context(), Selection(probabilities={"day_work": 1.0}, salience={}, reason="best_effort"))
    clock.now = 105.0
    after = controller.decide_action(DecisionMode.NORMAL, Context(), Selection(probabilities={"rain": 1.0}, salience={}, reason="best_effort"))

    assert [before.action, after.action] == [Action.NOOP, Action.APPLY]


def test_controller_never_bypasses_disturbance_checks_when_a_switch_is_due() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, idle_threshold=20)
    controller.notify_executed(
        controller.decide_action(DecisionMode.MANUAL, Context(), Selection(probabilities={"day_work": 1.0}, salience={}, reason="best_effort"))
    )
    clock.now = 3700.0

    decision = controller.decide_action(
        DecisionMode.NORMAL,
        Context(idle=5, cpu=90, fullscreen=True),
        Selection(probabilities={"rain": 1.0}, salience={}, reason="best_effort"),
    )

    assert decision.action == Action.NOOP
    assert set(decision.disturbance.blocked_by) == {Blocker.CPU, Blocker.FULLSCREEN, Blocker.IDLE}


def test_controller_recovery_switches_without_normal_execution_gates() -> None:
    controller = _controller(MutableClock(100.0), startup_delay=30, idle_threshold=60)
    controller.notify_executed(
        controller.decide_action(DecisionMode.MANUAL, Context(), Selection(probabilities={"day_work": 1.0}, salience={}, reason="best_effort"))
    )
    decision = controller.decide_action(
        deduce_mode(
            factual=FactualPlaylistState(status=FactualPlaylistStatus.NO_PLAYLIST),
            paused=False,
            manual_requested=False,
        ),
        Context(idle=0, cpu=100, fullscreen=True),
        Selection(probabilities={"rain": 1.0}, salience={}, reason="best_effort"),
    )

    assert decision.action == Action.APPLY


@pytest.mark.parametrize("manual_requested, expected", [(True, Action.APPLY), (False, Action.PAUSE)])
def test_controller_prioritizes_manual_application_then_pause_over_recovery(manual_requested: bool, expected: Action) -> None:
    controller = _controller(MutableClock(100.0), startup_delay=30, idle_threshold=60)
    mode = deduce_mode(
        factual=FactualPlaylistState(status=FactualPlaylistStatus.NO_PLAYLIST),
        paused=True,
        manual_requested=manual_requested,
    )

    decision = controller.decide_action(
        mode,
        Context(idle=0, cpu=100, fullscreen=True),
        Selection(probabilities={"rain": 1.0}, salience={}, reason="best_effort"),
    )

    assert decision.action == expected


def test_controller_recovery_without_a_selection_does_nothing() -> None:
    controller = _controller(MutableClock(100.0))
    controller.notify_executed(
        controller.decide_action(DecisionMode.MANUAL, Context(), Selection(probabilities={"day_work": 1.0}, salience={}, reason="best_effort"))
    )
    decision = controller.decide_action(
        DecisionMode.RECOVERY,
        Context(),
        Selection(probabilities={}, salience={}, reason="no_safe_scenes"),
    )

    assert decision.action.value == "noop"


def test_controller_configuration_replacement_preserves_successful_distribution_and_times() -> None:
    clock = MutableClock(100.0)
    controller = _controller(clock, startup_delay=30)
    controller.notify_executed(
        controller.decide_action(
            DecisionMode.MANUAL, Context(), Selection(probabilities={"day_work": 0.5, "rain": 0.5}, salience={}, reason="best_effort")
        )
    )
    clock.now = 105.0
    replacement = _controller(clock, startup_delay=100)
    replacement.import_state(controller.export_state())
    selection = Selection(probabilities={"day_work": 0.125, "rain": 0.875}, salience={}, reason="best_effort")

    actions = []
    for now in (130.0, 131.0):
        clock.now = now
        actions.append(replacement.decide_action(DecisionMode.NORMAL, Context(), selection).action)

    assert actions == [Action.NOOP, Action.APPLY]


@pytest.mark.parametrize(
    "scene_associations",
    [
        {
            "day_work": Association(SemanticItem.DAY, SemanticItem.WORK),
            "rain": Association(SemanticItem.RAIN),
        },
        {
            "day_work": Association(SemanticItem.DAY, SemanticItem.SUNSET, SemanticItem.WORK, SemanticItem.LEISURE),
            "rain": Association(SemanticItem.RAIN, SemanticItem.SNOW),
        },
    ],
)
def test_controller_keeps_the_same_switch_time_when_only_same_variable_alternatives_are_added(
    scene_associations: dict[str, Association],
) -> None:
    clock = MutableClock(100.0)
    controller = Controller(
        TimingConfig(startup_delay=0, cycle_interval=900),
        DisturbanceConfig(idle_threshold=0, cpu_threshold=80),
        scene_associations,
        clock=clock,
    )
    controller.notify_executed(
        controller.decide_action(
            DecisionMode.MANUAL, Context(), Selection(probabilities={"day_work": 0.5, "rain": 0.5}, salience={}, reason="best_effort")
        )
    )
    changed = Selection(probabilities={"day_work": 0.125, "rain": 0.875}, salience={}, reason="best_effort")

    actions = []
    for now in (130.0, 131.0):
        clock.now = now
        actions.append(controller.decide_action(DecisionMode.NORMAL, Context(), changed).action)

    assert actions == [Action.NOOP, Action.APPLY]
