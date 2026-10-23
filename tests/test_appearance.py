from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ui.appearance import AppearanceStore, Theme


def test_first_launch_uses_system_appearance_without_writing(tmp_path: Path) -> None:
    path = tmp_path / "appearance.json"
    assert AppearanceStore(path).load().theme == "auto"
    assert not path.exists()


@pytest.mark.parametrize("theme", ["dark", "light", "auto"])
def test_each_appearance_survives_a_new_store_instance(tmp_path: Path, theme: Theme) -> None:
    path = tmp_path / "preferences" / "appearance.json"
    AppearanceStore(path).save_theme(theme)
    assert AppearanceStore(path).load().theme == theme


def test_invalid_theme_does_not_replace_saved_appearance(tmp_path: Path) -> None:
    path = tmp_path / "appearance.json"
    store = AppearanceStore(path)
    store.save_theme("dark")
    with pytest.raises(ValidationError):
        store.save_theme("unknown")  # type: ignore[arg-type]
    assert AppearanceStore(path).load().theme == "dark"


@pytest.mark.parametrize("payload", ['{"theme":"invalid"}', "not json"])
def test_invalid_saved_appearance_is_reported_without_rewriting(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "appearance.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValidationError):
        AppearanceStore(path).load()
    assert path.read_text(encoding="utf-8") == payload


def test_failed_replacement_preserves_previous_appearance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "appearance.json"
    store = AppearanceStore(path)
    store.save_theme("dark")

    def denied_replace(source: str, destination: Path) -> None:
        raise PermissionError("File is locked")

    monkeypatch.setattr("os.replace", denied_replace)
    with pytest.raises(PermissionError):
        store.save_theme("light")
    assert AppearanceStore(path).load().theme == "dark"
