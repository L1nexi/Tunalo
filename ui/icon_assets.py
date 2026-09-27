"""Static application icons shared by the tray and desktop window."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def icon_path(filename: str) -> Path:
    """Return the icon asset in a source checkout or a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).resolve().parents[1] / "packaging" / filename


def load_tray_icon(paused: bool) -> Image.Image:
    """Load a detached 64-pixel image for the current tray state."""
    filename = "PausedIcon.ico" if paused else "AppIcon.ico"
    with Image.open(icon_path(filename)) as icon:
        icon.size = (64, 64)
        return icon.convert("RGBA")
