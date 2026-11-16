from __future__ import annotations

import json
import subprocess
import sys
import winreg
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

from app.autostart import AutostartRegistration, build_autostart_command


@pytest.fixture
def registry_path() -> Iterator[str]:
    path = rf"Software\Tunalo.Tests.{uuid4().hex}"
    try:
        yield path
    finally:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except FileNotFoundError:
            pass


@pytest.fixture
def registration(registry_path: str) -> AutostartRegistration:
    command = build_autostart_command(Path("C:/Tunalo/Tunalo.exe"), Path("C:/Tunalo/config"))
    return AutostartRegistration(command, registry_path=registry_path)


def test_absent_startup_entry_is_disabled(registration: AutostartRegistration) -> None:
    assert not registration.is_enabled()


def test_enabled_startup_survives_a_new_registration_instance(registry_path: str, registration: AutostartRegistration) -> None:
    registration.set_enabled(True)

    command = build_autostart_command(Path("C:/Tunalo/Tunalo.exe"), Path("C:/Tunalo/config"))
    assert AutostartRegistration(command, registry_path=registry_path).is_enabled()


def test_repeated_enable_and_disable_succeed(registration: AutostartRegistration) -> None:
    registration.set_enabled(True)
    registration.set_enabled(True)
    assert registration.is_enabled()

    registration.set_enabled(False)
    registration.set_enabled(False)
    assert not registration.is_enabled()


def test_disabling_an_absent_entry_succeeds(registration: AutostartRegistration) -> None:
    registration.set_enabled(False)
    assert not registration.is_enabled()


def test_an_old_launch_command_is_replaced_only_when_enabled(registry_path: str, registration: AutostartRegistration) -> None:
    registration.set_enabled(True)
    updated_command = build_autostart_command(Path("C:/New Tunalo/Tunalo.exe"), Path("C:/New Tunalo/config"))
    updated = AutostartRegistration(updated_command, registry_path=registry_path)

    assert not updated.is_enabled()
    assert registration.is_enabled()

    updated.set_enabled(True)
    assert updated.is_enabled()


@pytest.mark.parametrize("enabled", ["false", 1])
def test_non_boolean_input_preserves_enabled_startup(registration: AutostartRegistration, enabled: object) -> None:
    registration.set_enabled(True)
    with pytest.raises(ValueError, match="boolean"):
        registration.set_enabled(enabled)  # type: ignore[arg-type]
    assert registration.is_enabled()


@pytest.mark.parametrize("command", ["", "Tunalo.exe\0--window", "x" * 261, "\U0001f600" * 131])
def test_invalid_commands_preserve_previous_registration(registry_path: str, registration: AutostartRegistration, command: str) -> None:
    registration.set_enabled(True)
    invalid = AutostartRegistration(command, registry_path=registry_path)

    with pytest.raises(ValueError):
        invalid.set_enabled(True)

    assert registration.is_enabled()


def test_release_command_quotes_executable_and_config_paths() -> None:
    command = build_autostart_command(Path("C:/Program Files/Tunalo/Tunalo.exe"), Path("C:/Users/Test User/Tunalo config"))

    assert command == '"C:\\Program Files\\Tunalo\\Tunalo.exe" --config "C:\\Users\\Test User\\Tunalo config"'


def test_source_command_uses_a_windowless_interpreter() -> None:
    command = build_autostart_command(
        Path("C:/Python Runtime/python.exe"),
        Path("C:/Tunalo config"),
        script=Path("C:/Source Checkout/main.py"),
    )

    assert command == '"C:\\Python Runtime\\pythonw.exe" "C:\\Source Checkout\\main.py" --config "C:\\Tunalo config"'


def test_source_command_launches_with_the_selected_config_from_another_directory(tmp_path: Path) -> None:
    source_dir = tmp_path / "source checkout"
    config_dir = tmp_path / "config with spaces"
    working_dir = tmp_path / "unrelated directory"
    for directory in (source_dir, config_dir, working_dir):
        directory.mkdir()

    script = source_dir / "main.py"
    script.write_text(
        "import argparse, json, sys\n"
        "from pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--config', required=True)\n"
        "config = parser.parse_args().config\n"
        "payload = {'config': config, 'executable': Path(sys.executable).name}\n"
        "(Path(config) / 'started.json').write_text(json.dumps(payload), encoding='utf-8')\n",
        encoding="utf-8",
    )
    command = build_autostart_command(Path(sys.executable), config_dir, script=script)

    subprocess.run(command, cwd=working_dir, check=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)

    assert json.loads((config_dir / "started.json").read_text(encoding="utf-8")) == {
        "config": str(config_dir),
        "executable": "pythonw.exe",
    }
