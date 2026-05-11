"""Plotly style templates matching the matplotlib journal presets.

Each template maps to its matplotlib counterpart in plot_styles.py and can be
applied via ``fig.update_layout(template=template)`` in generated code.
The ``generate_plotly_style_code`` function returns a self-contained Python
snippet that creates the template at runtime.
"""

from __future__ import annotations

from typing import Any

# Each entry mirrors the corresponding PLOT_STYLES dict in plot_styles.py.
# Keys: colorway, font_family, title_size, bg_color, gridcolor, showgrid
PLOTLY_STYLES: dict[str, dict[str, Any]] = {
    "Nature": {
        "colorway": ["#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4", "#91D1C2", "#DC9FB4"],
        "font_family": "Arial",
        "title_size": 16,
        "label_size": 13,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#E5E5E5",
        "showgrid": False,
    },
    "Science": {
        "colorway": ["#3B4992", "#EE0000", "#008B45", "#631879", "#008280", "#BB5500", "#A2B0D0", "#7B7B7B"],
        "font_family": "Arial",
        "title_size": 15,
        "label_size": 12,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#E5E5E5",
        "showgrid": False,
    },
    "The Lancet": {
        "colorway": ["#00468B", "#ED0000", "#42B540", "#0099B4", "#925E9F", "#FDAF91", "#AD002A", "#ADB6B6"],
        "font_family": "Times New Roman",
        "title_size": 16,
        "label_size": 13,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#D0D0D0",
        "showgrid": True,
    },
    "NEJM": {
        "colorway": ["#BC3C29", "#0072B5", "#E18727", "#20854E", "#7876B1", "#6F99AD", "#FFDC91", "#EE4C97"],
        "font_family": "Arial",
        "title_size": 15,
        "label_size": 12,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#E5E5E5",
        "showgrid": False,
    },
    "JAMA": {
        "colorway": ["#374E55", "#DF8F44", "#00A1D5", "#B24745", "#79AF97", "#6A6599", "#80796B"],
        "font_family": "Arial",
        "title_size": 15,
        "label_size": 12,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#D0D0D0",
        "showgrid": True,
    },
    "APA 7th": {
        "colorway": ["#2D2D2D", "#6B6B6B", "#A0A0A0", "#C8C8C8", "#4A4A4A", "#8C8C8C", "#B5B5B5"],
        "font_family": "Times New Roman",
        "title_size": 14,
        "label_size": 12,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#E5E5E5",
        "showgrid": False,
    },
    "The Economist": {
        "colorway": ["#01A2D9", "#014D64", "#6794A7", "#7AD2F6", "#76C0C1", "#BCD631", "#D5952D", "#DB444B"],
        "font_family": "Arial",
        "title_size": 16,
        "label_size": 12,
        "bg_color": "#D5E4EB",
        "paper_bg": "#D5E4EB",
        "gridcolor": "#FFFFFF",
        "showgrid": True,
    },
    "IEEE": {
        "colorway": ["#000000", "#0055A4", "#CC0000", "#228B22", "#8B4513", "#555555", "#8B0000", "#006400"],
        "font_family": "Serif",
        "title_size": 13,
        "label_size": 11,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#E5E5E5",
        "showgrid": False,
    },
    "Minimal": {
        "colorway": ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3", "#8C8C8C"],
        "font_family": "Arial",
        "title_size": 15,
        "label_size": 12,
        "bg_color": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "gridcolor": "#F0F0F0",
        "showgrid": False,
    },
    "Classic": {
        "colorway": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"],
        "font_family": "Arial",
        "title_size": 16,
        "label_size": 13,
        "bg_color": "#EAEAF2",
        "paper_bg": "#EAEAF2",
        "gridcolor": "#FFFFFF",
        "showgrid": True,
    },
}

PLOTLY_STYLE_NAMES: list[str] = list(PLOTLY_STYLES.keys())


def generate_plotly_style_code(style_name: str) -> str:
    """Return Python code that creates and applies a Plotly template.

    The returned snippet is self-contained so the user can paste it
    into any script and reproduce the exact figure styling.
    """
    s = PLOTLY_STYLES.get(style_name)
    if s is None:
        return "# Unknown Plotly style\n"

    lines = [
        f"# Plotly Style: {style_name}",
        "import plotly.graph_objects as go",
        "import plotly.io as pio",
        "",
        f"_template = go.layout.Template()",
        f"_template.layout.colorway = {s['colorway']}",
        f"_template.layout.font = dict(family='{s['font_family']}', size={s['label_size']})",
        f"_template.layout.title = dict(font=dict(size={s['title_size']}))",
        f"_template.layout.plot_bgcolor = '{s['bg_color']}'",
        f"_template.layout.paper_bgcolor = '{s['paper_bg']}'",
        f"_template.layout.xaxis = dict(showgrid={s['showgrid']}, gridcolor='{s['gridcolor']}')",
        f"_template.layout.yaxis = dict(showgrid={s['showgrid']}, gridcolor='{s['gridcolor']}')",
        f"pio.templates['quantia_{style_name.lower().replace(' ', '_')}'] = _template",
        f"pio.templates.default = 'quantia_{style_name.lower().replace(' ', '_')}'",
    ]
    return "\n".join(lines)
