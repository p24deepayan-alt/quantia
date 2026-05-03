"""Utilities for managing application resources."""

import sys
import os
from pathlib import Path


def resource_path(relative_path: str | Path) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # We are in development mode
        # The base is the project root (4 levels up from this file)
        base_path = Path(__file__).parent.parent.parent.parent

    return base_path / relative_path
