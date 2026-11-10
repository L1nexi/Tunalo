from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

# ``Local\`` 把作用域限制在当前登录会话：每个桌面只有一个托盘，多个 Windows 会话互不影响。
SINGLE_INSTANCE_MUTEX_NAME = "Local\\Tunalo.SingleInstance"

_ERROR_ALREADY_EXISTS = 183


def _create_mutex_handle(name: str) -> tuple[int | None, int]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    handle = kernel32.CreateMutexW(None, False, name)
    return handle, ctypes.get_last_error()


def _close_mutex_handle(handle: int) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle(handle)


class SingleInstance:
    """持有一个内核互斥体，保证每个登录会话只有一个托盘实例。

    持有者进程退出时 Windows 自动释放互斥体，崩溃的实例不会挡住下一次启动。
    """

    def __init__(self, name: str = SINGLE_INSTANCE_MUTEX_NAME) -> None:
        self._name = name
        self._handle: int | None = None

    @property
    def held(self) -> bool:
        return self._handle is not None

    def acquire(self) -> bool:
        """尝试取得互斥体。

        Returns:
            已有实例持有时返回 False，本进程取得时返回 True。

        Raises:
            OSError: Windows 无法创建互斥体句柄时抛出。
        """
        if sys.platform != "win32":
            return True

        handle, error = _create_mutex_handle(self._name)
        if not handle:
            raise OSError(error, "CreateMutexW failed")
        if error == _ERROR_ALREADY_EXISTS:
            _close_mutex_handle(handle)
            return False
        self._handle = handle
        return True
