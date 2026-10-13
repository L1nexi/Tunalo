from __future__ import annotations

from core.state.scheduler import SchedulerState


def test_manual_apply_request_is_consumed_once() -> None:
    s = SchedulerState()
    s.request_manual_apply()
    assert s.consume_manual_apply_request() is True
    assert s.consume_manual_apply_request() is False
