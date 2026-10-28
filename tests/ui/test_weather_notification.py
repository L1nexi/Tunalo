from __future__ import annotations

from pathlib import Path

import pystray
import pytest

from app.event_logger import JsonlEventLogger
from core.runtime.profile_manager import ProfileManager
from core.runtime.scheduler import Scheduler
from ui import i18n
from ui.tray import TrayIcon


@pytest.mark.parametrize(
    ("language", "message"),
    [
        ("zh", "自上次成功获取天气信息已经过了 2 小时。可能是网络或者代理问题？"),
        ("en", "It has been 2 hours since weather information was last retrieved successfully. Could it be a network or proxy issue?"),
    ],
)
def test_weather_notification_uses_the_current_language_and_is_silent_while_stopping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, language: str, message: str
) -> None:
    notifications: list[tuple[str, str | None]] = []

    def notify(icon: pystray.Icon, text: str, title: str | None = None) -> None:
        notifications.append((text, title))

    monkeypatch.setattr(pystray.Icon, "notify", notify)
    scheduler = Scheduler(ProfileManager(str(tmp_path)), JsonlEventLogger(str(tmp_path)))
    tray = TrayIcon(scheduler)
    previous_language = i18n.current_lang
    try:
        i18n.set_language(language)
        tray.notify_weather_unavailable(10799.0)
        scheduler.stop_event.set()
        tray.notify_weather_unavailable(14400.0)
    finally:
        i18n.set_language(previous_language)

    assert notifications == [(message, "Tunalo")]
