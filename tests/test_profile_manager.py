from __future__ import annotations

import getpass
import json
from pathlib import Path

import pytest

from configurations.profile import Profile
from configurations.profile_store import ProfileStore
from core.runtime.profile_manager import (
    ProfileAlreadyExists,
    ProfileApplyUnavailable,
    ProfileManager,
    ProfileNotFoundError,
)


def _wallpaper_engine_path(tmp_path: Path, *playlists: tuple[str, int]) -> str:
    executable = tmp_path / "wallpaper64.exe"
    executable.write_text("fake", encoding="utf-8")
    config = {
        getpass.getuser(): {
            "general": {"playlists": [{"name": name, "items": [f"item-{index}" for index in range(count)]} for name, count in playlists]}
        }
    }
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    return str(executable)


def _profile(wallpaper_engine_path: str, *, playlist: str = "WORK") -> Profile:
    return Profile.model_validate(
        {
            "wallpaper_engine_path": wallpaper_engine_path,
            "weather": {
                "api_key": "test-key",
                "location": {
                    "name": "上海",
                    "latitude": 31.2304,
                    "longitude": 121.4737,
                },
            },
            "scenes": {"day_work": {"name": "日间工作", "associations": {"time": ["day"], "activity": ["work"]}, "playlist": playlist}},
        }
    )


def test_profile_manager_initializes_from_persisted_profile(tmp_path: Path):
    executable = _wallpaper_engine_path(tmp_path, ("WORK", 7))
    profile = _profile(executable)
    ProfileStore(str(tmp_path)).commit(profile)
    manager = ProfileManager(str(tmp_path))
    manager.load_initial_profile()

    config = manager.compile_initial_config()

    assert config.scenes["day_work"].item_count == 7
    assert manager.get_profile() == profile


def test_load_initial_profile_without_persisted_profile_raises(tmp_path: Path):
    manager = ProfileManager(str(tmp_path))

    with pytest.raises(ProfileNotFoundError):
        manager.load_initial_profile()


def test_create_initial_profile_validates_persists_and_publishes(tmp_path: Path):
    executable = _wallpaper_engine_path(tmp_path, ("WORK", 7))
    draft = _profile(executable)
    manager = ProfileManager(str(tmp_path))

    committed = manager.create_initial_profile(draft)

    assert committed == draft
    assert manager.get_profile() == draft
    assert manager.compile_initial_config().scenes["day_work"].item_count == 7

    reloaded = ProfileManager(str(tmp_path))
    reloaded.load_initial_profile()
    assert reloaded.get_profile() == draft
    assert reloaded.compile_initial_config().scenes["day_work"].item_count == 7


def test_create_initial_profile_rejects_existing_persisted_profile(tmp_path: Path):
    executable = _wallpaper_engine_path(tmp_path, ("WORK", 1), ("NEW", 2))
    current = _profile(executable)
    replacement = _profile(executable, playlist="NEW")
    ProfileStore(str(tmp_path)).commit(current)
    manager = ProfileManager(str(tmp_path))

    with pytest.raises(ProfileAlreadyExists):
        manager.create_initial_profile(replacement)


def test_profile_application_is_unavailable_before_startup(tmp_path: Path):
    executable = _wallpaper_engine_path(tmp_path, ("WORK", 1))
    manager = ProfileManager(str(tmp_path))

    with pytest.raises(ProfileApplyUnavailable):
        manager.apply_profile(_profile(executable), timeout=1)
