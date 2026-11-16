from __future__ import annotations

import subprocess
import winreg
from pathlib import Path

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "Tunalo"


def build_autostart_command(executable: Path, config_dir: Path, *, script: Path | None = None) -> str:
    """Build an absolute Windows launch command for a release or source checkout."""
    executable = executable.absolute()
    command = [str(executable)]
    if script is not None:
        command = [str(executable.with_name("pythonw.exe")), str(script.absolute())]
    command.extend(("--config", str(config_dir.absolute())))
    return subprocess.list2cmdline(command)


class AutostartRegistration:
    """Manage Tunalo's launch command in the current user's Run registry key."""

    def __init__(self, command: str, *, registry_path: str = _RUN_KEY) -> None:
        self._command = command
        self._registry_path = registry_path

    def is_enabled(self) -> bool:
        """Return whether the registered command matches this application and config.

        Raises:
            OSError: If Windows refuses access to the registry.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._registry_path, access=winreg.KEY_QUERY_VALUE) as key:
                command, value_type = winreg.QueryValueEx(key, _VALUE_NAME)
        except FileNotFoundError:
            return False
        return value_type == winreg.REG_SZ and command == self._command

    def set_enabled(self, enabled: bool) -> None:
        """Register this launch command or remove Tunalo's startup entry.

        Disabling an absent entry succeeds without creating a registry key.

        Raises:
            ValueError: If enabled is not a boolean, or an enabled command is empty,
                contains a null character, or exceeds Windows' 260-character limit.
            OSError: If Windows refuses the registry change.
        """
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be a boolean")
        if enabled:
            if not self._command or "\0" in self._command:
                raise ValueError("Autostart command must be non-empty and contain no null characters")
            if len(self._command.encode("utf-16-le")) // 2 > 260:
                raise ValueError("Windows autostart commands cannot exceed 260 characters")
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self._registry_path, access=winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, self._command)
            return

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._registry_path, access=winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, _VALUE_NAME)
        except FileNotFoundError:
            pass
