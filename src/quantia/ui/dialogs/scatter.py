"""Scatter Plot Dialog.

Generates seaborn scatterplot code with style presets.
Supports Plotly backend for interactive visualizations.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
)

from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from quantia.ui.central.plotly_styles import PLOTLY_STYLE_NAMES, generate_plotly_style_code
from quantia.ui.dialogs.base import BaseAnalysisDialog


class ScatterPlotDialog(BaseAnalysisDialog):
    """Dialog for creating scatter plots."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Scatter Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_x = QListWidget()
        layout.addWidget(self._create_selector_row("X Variable:", self.list_x, multi_select=False))

        self.list_y = QListWidget()
        layout.addWidget(self._create_selector_row("Y Variable:", self.list_y, multi_select=False))

        self.list_hue = QListWidget()
        layout.addWidget(self._create_selector_row("Color By (optional):", self.list_hue, multi_select=False))

    def build_options(self, layout: QVBoxLayout) -> None:
        # Style
        group_style = QGroupBox("Style")
        l_style = QVBoxLayout(group_style)
        l_style.addWidget(QLabel("Preset:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_style.addWidget(self.cmb_style)
        layout.addWidget(group_style)

        # Options
        group_opts = QGroupBox("Plot Options")
        l_opts = QVBoxLayout(group_opts)

        self.chk_reg = QCheckBox("Add Regression Line")
        l_opts.addWidget(self.chk_reg)

        l_opts.addWidget(QLabel("Point Opacity:"))
        self.spn_alpha = QDoubleSpinBox()
        self.spn_alpha.setRange(0.1, 1.0)
        self.spn_alpha.setValue(0.7)
        self.spn_alpha.setSingleStep(0.1)
        l_opts.addWidget(self.spn_alpha)

        # Animation frame (Plotly-only feature)
        l_opts.addWidget(QLabel("Animation Frame (Plotly only):"))
        self.list_anim = QListWidget()
        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        x = self.list_x.item(0).text() if self.list_x.count() > 0 else None
        y = self.list_y.item(0).text() if self.list_y.count() > 0 else None
        hue = self.list_hue.item(0).text() if self.list_hue.count() > 0 else None

        if not x or not y:
            QMessageBox.warning(self, "Missing Input", "Please select both X and Y variables.")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(x, y, hue)
        return self._generate_matplotlib_code(x, y, hue)

    def _generate_matplotlib_code(self, x: str, y: str, hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        alpha = self.spn_alpha.value()
        reg = self.chk_reg.isChecked()

        style_code = generate_style_code(style_name)
        hue_arg = f", hue='{hue}'" if hue else ""

        code = [
            f"# Scatter Plot: {x} vs {y}",
            style_code,
            "",
            "fig, ax = plt.subplots(figsize=(8, 6))",
        ]

        if reg:
            code.append(f"sns.regplot(data=df, x='{x}', y='{y}', scatter_kws={{'alpha': {alpha}}}, ax=ax)")
        else:
            code.append(f"sns.scatterplot(data=df, x='{x}', y='{y}'{hue_arg}, alpha={alpha}, ax=ax)")

        code += [
            f"ax.set_title('{y} vs {x}')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('Scatter: {x} vs {y}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, x: str, y: str, hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        alpha = self.spn_alpha.value()
        reg = self.chk_reg.isChecked()

        style_code = generate_plotly_style_code(style_name)

        color_arg = f", color='{hue}'" if hue else ""
        trendline_arg = ", trendline='ols'" if reg else ""

        code = [
            f"# Scatter Plot (Plotly): {x} vs {y}",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.to_pandas()",
            "else:",
            f"    _plot_df = df",
            "",
            f"fig = px.scatter(_plot_df, x='{x}', y='{y}'{color_arg}{trendline_arg},",
            f"                 opacity={alpha}, title='{y} vs {x}')",
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('Scatter: {x} vs {y}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
