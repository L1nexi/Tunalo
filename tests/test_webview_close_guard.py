from __future__ import annotations

import time

from ui.webview import _NATIVE_CLOSE_EVENT, _forward_native_close, _notify_page_of_close, _WindowAPI


class _StubWindow:
    def __init__(self, *, fail_evaluation: bool = False) -> None:
        self.scripts: list[str] = []
        self.fail_evaluation = fail_evaluation
        self.destroyed = 0

    def evaluate_js(self, script: str) -> None:
        if self.fail_evaluation:
            raise RuntimeError("bridge unavailable")
        self.scripts.append(script)

    def destroy(self) -> None:
        self.destroyed += 1


def _ready_api() -> _WindowAPI:
    api = _WindowAPI()
    api.page_ready()
    return api


def _wait_for_scripts(window: _StubWindow, count: int, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while len(window.scripts) < count and time.monotonic() < deadline:
        time.sleep(0.01)


def test_native_close_before_page_ready_allows_closing() -> None:
    window = _StubWindow()

    assert _forward_native_close(window, _WindowAPI()) is True
    time.sleep(0.05)
    assert window.scripts == []


def test_programmatic_destroy_is_not_vetoed() -> None:
    window = _StubWindow()
    api = _ready_api()
    api._close_allowed = True

    assert _forward_native_close(window, api) is True
    time.sleep(0.05)
    assert window.scripts == []


def test_native_close_when_page_ready_vetoes_and_notifies_page() -> None:
    window = _StubWindow()

    assert _forward_native_close(window, _ready_api()) is False
    _wait_for_scripts(window, 1)
    assert len(window.scripts) == 1
    assert _NATIVE_CLOSE_EVENT in window.scripts[0]


def test_notify_failure_destroys_window_instead_of_leaving_it_unclosable() -> None:
    window = _StubWindow(fail_evaluation=True)
    api = _ready_api()

    _notify_page_of_close(window, api)

    assert window.scripts == []
    assert window.destroyed == 1
    assert api._close_allowed is True
