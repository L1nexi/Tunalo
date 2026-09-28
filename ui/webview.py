from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
import webbrowser
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import psutil

from ui.i18n import t
from ui.icon_assets import icon_path

if TYPE_CHECKING:
    import webview

logger = logging.getLogger("Tunalo.WebView")

# frontend/src/components/setup/SetupWorkspace.vue 监听同名事件，把关闭决定交回页面。
_NATIVE_CLOSE_EVENT = "tunalo:native-close-request"

WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1


def _resolve_icon_path() -> str:
    return str(icon_path("AppIcon.ico"))


def _set_window_icon() -> None:
    import webview

    icon_path = _resolve_icon_path()
    if not os.path.isfile(icon_path):
        logger.warning("Icon not found: %s", icon_path)
        return

    try:
        title = webview.windows[0].title
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if not hwnd:
            logger.warning("FindWindowW returned NULL for title: %r", title)
            return

        hicon = ctypes.windll.user32.LoadImageW(
            0,
            icon_path,
            1,
            0,
            0,
            0x00000010 | 0x00000040,
        )
        if hicon:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
    except Exception:
        logger.exception("Failed to set window icon")


class _WindowAPI:
    def __init__(self) -> None:
        self._page_ready = False
        self._close_allowed = False

    def page_ready(self) -> None:
        """Mark the page as loaded so native close requests are guarded by the page."""
        self._page_ready = True

    def choose_wallpaper_engine(self) -> str | None:
        """Open a native file picker and return the selected executable path."""
        import webview

        if not webview.windows:
            return None
        selected = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=("Wallpaper Engine executable (*.exe)",),
        )
        return selected[0] if selected else None

    def open_external(self, url: str) -> None:
        """Open one safe HTTP(S) URL in the user's default browser.

        Raises:
            ValueError: If ``url`` is not an absolute HTTP(S) URL.
        """

        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("external URL must be an absolute HTTP(S) URL")
        webbrowser.open_new_tab(url)

    def close(self) -> None:
        """Destroy the window after the user confirmed a guarded close request."""
        self._close_allowed = True
        import webview

        if webview.windows:
            webview.windows[0].destroy()


class AppWindow:
    def __init__(self, api_port: int, locale: str, *, path: str = "/", title_key: str = "setup_title"):
        self._url = f"http://127.0.0.1:{api_port}{path}?locale={locale}"
        self._title = t(title_key)

    def create_and_block(self) -> None:
        import webview

        api = _WindowAPI()
        window = webview.create_window(
            title=self._title,
            url=self._url,
            width=1200,
            height=780,
            resizable=True,
            text_select=True,
            js_api=api,
        )
        window.events.closing += lambda: _forward_native_close(window, api)

        webview.start(gui="edgechromium", func=_set_window_icon)


def _forward_native_close(window: webview.Window, api: _WindowAPI) -> bool:
    """Decide whether a native close request (× button, Alt+F4) may proceed.

    The request is vetoed and forwarded to the page, which asks about unsaved
    changes and destroys the window itself via ``close()`` when confirmed.
    ``close()`` marks ``_close_allowed`` first, because pywebview implements
    destroy as ``Form.Close()``, which raises this very event again. Fails
    open when the page has not reported ``page_ready``, so a broken page can
    never leave an unclosable window. The forward must not run on the UI
    thread: it is raised inside the native close processing, and a synchronous
    ``evaluate_js`` there would deadlock the message loop.

    Returns:
        ``True`` to allow closing, ``False`` to veto it.
    """
    if api._close_allowed or not api._page_ready:
        return True
    threading.Thread(target=_notify_page_of_close, args=(window, api), daemon=True).start()
    return False


def _notify_page_of_close(window: webview.Window, api: _WindowAPI) -> None:
    """Deliver the native close request to the page; destroy when undeliverable."""
    try:
        window.evaluate_js(f"window.dispatchEvent(new CustomEvent('{_NATIVE_CLOSE_EVENT}'))")
    except Exception:
        logger.exception("Failed to forward the native close request to the page")
        api._close_allowed = True
        try:
            window.destroy()
        except Exception:
            logger.exception("Failed to close the window after the forward failure")


def focus_process_window(process_id: int) -> bool:
    """Restore and focus a visible window owned by a process or its children."""

    if sys.platform != "win32":
        return False

    process_ids = {process_id}
    try:
        process_ids.update(child.pid for child in psutil.Process(process_id).children(recursive=True))
    except psutil.Error:
        pass

    user32 = ctypes.windll.user32
    target: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @callback_type
    def enum_window(hwnd: int, _lparam: int) -> bool:
        owner_process_id = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_process_id))
        if owner_process_id.value in process_ids and user32.IsWindowVisible(hwnd):
            target.append(hwnd)
            return False
        return True

    user32.EnumWindows(enum_window, 0)
    if not target:
        return False

    user32.ShowWindow(target[0], 9)  # SW_RESTORE
    return bool(user32.SetForegroundWindow(target[0]))
