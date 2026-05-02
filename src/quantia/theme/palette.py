"""Colour palette and theme definitions for Quantia.

Follows the branding document colour system, mapped to a Windows-native
semantic token structure. Themes are applied via Qt stylesheets (.qss).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

_THEME_DIR = Path(__file__).parent


class Theme(Enum):
    """Available application themes."""

    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"


# ── Brand colours ────────────────────────────────────────────────────────────

DEEP_INDIGO = "#2C3E8F"
TEAL_ACCENT = "#009688"
SEAFOAM_GREEN = "#26A69A"
AMBER = "#FFC107"
CORAL_RED = "#EF5350"
SLATE_DARK = "#2D3E50"
CLOUD = "#F5F7FA"
OFF_WHITE = "#FAFBFD"
NEAR_BLACK = "#1E1E2E"


# ── Semantic tokens per theme ────────────────────────────────────────────────

PALETTE = {
    Theme.LIGHT: {
        "surface_primary": OFF_WHITE,
        "surface_secondary": "#F0F2F5",
        "surface_tertiary": "#E8EBF0",
        "border": "#D1D5DB",
        "text_primary": SLATE_DARK,
        "text_secondary": "#6B7280",
        "accent": DEEP_INDIGO,
        "accent_hover": "#3A4FA3",
        "accent_light": "#E8EBF5",
        "success": SEAFOAM_GREEN,
        "warning": AMBER,
        "error": CORAL_RED,
        "teal": TEAL_ACCENT,
        "table_alt_row": "#F6F8FA",
        "table_header_bg": "#E8EBF0",
        "selection": "#D0D7F2",
    },
    Theme.DARK: {
        "surface_primary": NEAR_BLACK,
        "surface_secondary": "#252538",
        "surface_tertiary": "#2D2D44",
        "border": "#3A3A50",
        "text_primary": "#E8EBF0",
        "text_secondary": "#9CA3AF",
        "accent": "#5B6BC0",
        "accent_hover": "#7986CB",
        "accent_light": "#2A2A45",
        "success": "#4DB6AC",
        "warning": "#FFD54F",
        "error": CORAL_RED,
        "teal": SEAFOAM_GREEN,
        "table_alt_row": "#252538",
        "table_header_bg": "#2D2D44",
        "selection": "#3A3A60",
    },
}


def get_stylesheet(theme: Theme) -> str:
    """Load the QSS stylesheet for the given theme."""
    qss_file = _THEME_DIR / f"{theme.value}.qss"
    if not qss_file.exists():
        return ""
    return qss_file.read_text(encoding="utf-8")
