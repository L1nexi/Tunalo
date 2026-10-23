from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

Theme = Literal["auto", "light", "dark"]


class AppearancePreferences(BaseModel):
    theme: Theme = "auto"


class AppearanceStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> AppearancePreferences:
        """Read appearance preferences, using system appearance on first launch.

        Raises:
            OSError: If an existing file cannot be read.
            pydantic.ValidationError: If the file contains invalid preferences.
        """
        try:
            payload = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return AppearancePreferences()
        return AppearancePreferences.model_validate_json(payload)

    def save_theme(self, theme: Theme) -> None:
        """Validate and atomically save the chosen appearance.

        Raises:
            pydantic.ValidationError: If the theme is not auto, light or dark.
            OSError: If the preferences cannot be written or replaced.
        """
        preferences = AppearancePreferences(theme=theme)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(dir=self.path.parent, prefix=".appearance-", suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(preferences.model_dump_json(indent=2) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
        finally:
            Path(temporary_path).unlink(missing_ok=True)
