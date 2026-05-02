"""Plot style presets inspired by scientific journals.

Each preset is a dict that can be applied via seaborn/matplotlib to produce
publication-quality figures. Users select a style from a dropdown in each
plot dialog; the generated code is fully self-contained and editable.
"""

from __future__ import annotations

from typing import Any

# Type alias for a style definition
StyleDef = dict[str, Any]

PLOT_STYLES: dict[str, StyleDef] = {
    "Nature": {
        "palette": ["#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4", "#91D1C2", "#DC9FB4"],
        "context": "notebook",
        "font_family": "Arial",
        "title_size": 14,
        "label_size": 12,
        "grid_style": "ticks",
        "bg_color": "#FFFFFF",
        "edge_color": "#333333",
        "spine_visible": True,
        "grid_alpha": 0.0,
    },
    "Science": {
        "palette": ["#3B4992", "#EE0000", "#008B45", "#631879", "#008280", "#BB5500", "#A2B0D0", "#7B7B7B"],
        "context": "notebook",
        "font_family": "TeX Gyre Heros",
        "title_size": 13,
        "label_size": 11,
        "grid_style": "white",
        "bg_color": "#FFFFFF",
        "edge_color": "#222222",
        "spine_visible": True,
        "grid_alpha": 0.0,
    },
    "The Lancet": {
        "palette": ["#00468B", "#ED0000", "#42B540", "#0099B4", "#925E9F", "#FDAF91", "#AD002A", "#ADB6B6"],
        "context": "notebook",
        "font_family": "Times New Roman",
        "title_size": 14,
        "label_size": 12,
        "grid_style": "whitegrid",
        "bg_color": "#FFFFFF",
        "edge_color": "#4A4A4A",
        "spine_visible": True,
        "grid_alpha": 0.3,
    },
    "NEJM": {
        "palette": ["#BC3C29", "#0072B5", "#E18727", "#20854E", "#7876B1", "#6F99AD", "#FFDC91", "#EE4C97"],
        "context": "notebook",
        "font_family": "Arial",
        "title_size": 13,
        "label_size": 11,
        "grid_style": "ticks",
        "bg_color": "#FFFFFF",
        "edge_color": "#2D2D2D",
        "spine_visible": True,
        "grid_alpha": 0.0,
    },
    "JAMA": {
        "palette": ["#374E55", "#DF8F44", "#00A1D5", "#B24745", "#79AF97", "#6A6599", "#80796B"],
        "context": "notebook",
        "font_family": "Arial",
        "title_size": 13,
        "label_size": 11,
        "grid_style": "whitegrid",
        "bg_color": "#FFFFFF",
        "edge_color": "#374E55",
        "spine_visible": True,
        "grid_alpha": 0.25,
    },
    "APA 7th": {
        "palette": ["#2D2D2D", "#6B6B6B", "#A0A0A0", "#C8C8C8", "#4A4A4A", "#8C8C8C", "#B5B5B5"],
        "context": "paper",
        "font_family": "Times New Roman",
        "title_size": 12,
        "label_size": 11,
        "grid_style": "ticks",
        "bg_color": "#FFFFFF",
        "edge_color": "#000000",
        "spine_visible": True,
        "grid_alpha": 0.0,
    },
    "The Economist": {
        "palette": ["#01A2D9", "#014D64", "#6794A7", "#7AD2F6", "#76C0C1", "#BCD631", "#D5952D", "#DB444B"],
        "context": "notebook",
        "font_family": "Arial",
        "title_size": 14,
        "label_size": 11,
        "grid_style": "whitegrid",
        "bg_color": "#D5E4EB",
        "edge_color": "#014D64",
        "spine_visible": False,
        "grid_alpha": 0.6,
    },
    "IEEE": {
        "palette": ["#000000", "#0055A4", "#CC0000", "#228B22", "#8B4513", "#555555", "#8B0000", "#006400"],
        "context": "paper",
        "font_family": "Serif",
        "title_size": 11,
        "label_size": 10,
        "grid_style": "ticks",
        "bg_color": "#FFFFFF",
        "edge_color": "#000000",
        "spine_visible": True,
        "grid_alpha": 0.0,
    },
    "Minimal": {
        "palette": ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3", "#8C8C8C"],
        "context": "notebook",
        "font_family": "TeX Gyre Heros",
        "title_size": 13,
        "label_size": 11,
        "grid_style": "white",
        "bg_color": "#FFFFFF",
        "edge_color": "#CCCCCC",
        "spine_visible": False,
        "grid_alpha": 0.0,
    },
    "Classic": {
        "palette": "deep",
        "context": "notebook",
        "font_family": "DejaVu Sans",
        "title_size": 14,
        "label_size": 12,
        "grid_style": "whitegrid",
        "bg_color": "#EAEAF2",
        "edge_color": "#333333",
        "spine_visible": True,
        "grid_alpha": 0.5,
    },
}

STYLE_NAMES: list[str] = list(PLOT_STYLES.keys())


def generate_style_code(style_name: str) -> str:
    """Return Python code that applies the given style preset.

    The returned snippet is self-contained so the user can paste it
    into any script and reproduce the exact figure styling.
    """
    s = PLOT_STYLES.get(style_name)
    if s is None:
        return "# Unknown style\n"

    palette = s["palette"]
    if isinstance(palette, list):
        palette_arg = repr(palette)
    else:
        palette_arg = f"'{palette}'"

    lines = [
        f"# Style: {style_name}",
        "import matplotlib.pyplot as plt",
        "import seaborn as sns",
        "",
        f"sns.set_theme(style='{s['grid_style']}', context='{s['context']}',",
        f"              font='{s['font_family']}',",
        f"              palette={palette_arg})",
        f"plt.rcParams['figure.facecolor'] = '{s['bg_color']}'",
        f"plt.rcParams['axes.facecolor'] = '{s['bg_color']}'",
        f"plt.rcParams['axes.edgecolor'] = '{s['edge_color']}'",
        f"plt.rcParams['axes.titlesize'] = {s['title_size']}",
        f"plt.rcParams['axes.labelsize'] = {s['label_size']}",
        f"plt.rcParams['axes.grid'] = {s['grid_alpha'] > 0}",
        f"plt.rcParams['grid.alpha'] = {s['grid_alpha']}",
    ]
    return "\n".join(lines)
