"""Line Chart Dialog.

Generates seaborn lineplot code with style presets.
Supports Plotly backend for interactive visualizations.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
)

from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from quantia.ui.central.plotly_styles import generate_plotly_style_code
from quantia.ui.dialogs.base import BaseAnalysisDialog


class LineChartDialog(BaseAnalysisDialog):
    """Dialog for creating line charts."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Line Chart", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_x = QListWidget()
        layout.addWidget(self._create_selector_row("X-Axis (e.g. Date/Time):", self.list_x, multi_select=False))

        self.list_y = QListWidget()
        layout.addWidget(self._create_selector_row("Y-Axis (numeric):", self.list_y, multi_select=False))

        self.list_hue = QListWidget()
        layout.addWidget(self._create_selector_row("Group By (Hue) (optional):", self.list_hue, multi_select=False))

    def build_options(self, layout: QVBoxLayout) -> None:
        # Style
        group_style = QGroupBox("Style")
        l_style = QVBoxLayout(group_style)
        l_style.addWidget(QLabel("Preset:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_style.addWidget(self.cmb_style)
        layout.addWidget(group_style)

    def generate_code(self) -> str:
        var_x = self.list_x.item(0).text() if self.list_x.count() > 0 else None
        var_y = self.list_y.item(0).text() if self.list_y.count() > 0 else None
        hue = self.list_hue.item(0).text() if self.list_hue.count() > 0 else None

        if not var_x or not var_y:
            QMessageBox.warning(self, "Missing Input", "Please select both X and Y variables.")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(var_x, var_y, hue)
        return self._generate_matplotlib_code(var_x, var_y, hue)

    def _generate_matplotlib_code(self, var_x: str, var_y: str, hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_style_code(style_name)

        title = f"Line Chart: {var_y} over {var_x}"
        if hue:
            title += f" by {hue}"

        args = [f"data=df", f"x='{var_x}'", f"y='{var_y}'"]
        if hue:
            args.append(f"hue='{hue}'")

        code = [
            f"# {title}",
            style_code,
            "",
            "fig, ax = plt.subplots(figsize=(9, 5))",
            f"sns.lineplot({', '.join(args)}, marker='o', ax=ax)",
            f"ax.set_title('{title}')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('{title}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, var_x: str, var_y: str, hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_plotly_style_code(style_name)

        title = f"Line Chart: {var_y} over {var_x}"
        if hue:
            title += f" by {hue}"

        color_arg = f", color='{hue}'" if hue else ""

        code = [
            f"# {title} (Plotly)",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            "    _plot_df = df.to_pandas()",
            "else:",
            "    _plot_df = df",
            "",
            f"fig = px.line(_plot_df, x='{var_x}', y='{var_y}'{color_arg}, markers=True,",
            f"              title='{title}')",
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('{title}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
