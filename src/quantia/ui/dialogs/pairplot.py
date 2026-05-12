"""Pair Plot Dialog.

Generates seaborn pairplot code with style presets.
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


class PairPlotDialog(BaseAnalysisDialog):
    """Dialog for creating pair plots / scatterplot matrices."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Pair Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_vars = QListWidget()
        row_vars = self._create_selector_row("Variables (min 2):", self.list_vars, multi_select=True)
        layout.addWidget(row_vars)

        self.list_hue = QListWidget()
        row_hue = self._create_selector_row("Color (Hue) - Optional:", self.list_hue, multi_select=False)
        layout.addWidget(row_hue)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_style = QGroupBox("Style")
        l_style = QVBoxLayout(group_style)
        l_style.addWidget(QLabel("Preset:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_style.addWidget(self.cmb_style)
        layout.addWidget(group_style)

    def generate_code(self) -> str:
        vars_selected = [self.list_vars.item(i).text() for i in range(self.list_vars.count())]
        if len(vars_selected) < 2:
            QMessageBox.warning(self, "Missing Input", "Please select at least 2 variables.")
            return ""

        hue = self.list_hue.item(0).text() if self.list_hue.count() > 0 else None

        if self._is_plotly():
            return self._generate_plotly_code(vars_selected, hue)
        return self._generate_matplotlib_code(vars_selected, hue)

    def _generate_matplotlib_code(self, vars_selected: list[str], hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_style_code(style_name)

        vars_str = "[" + ", ".join(f"'{v}'" for v in vars_selected) + "]"
        
        code = [
            f"# Pair Plot",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.to_pandas()",
            "else:",
            f"    _plot_df = df.copy()",
            "",
            f"vars_to_plot = {vars_str}",
        ]

        if hue:
            code.append(f"fig = sns.pairplot(_plot_df, vars=vars_to_plot, hue='{hue}')")
        else:
            code.append("fig = sns.pairplot(_plot_df, vars=vars_to_plot)")

        code += [
            "fig.figure.suptitle('Pair Plot', y=1.02)",
            "",
            "if 'show_plot' in globals():",
            "    show_plot('Pair Plot', fig.figure)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, vars_selected: list[str], hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_plotly_style_code(style_name)

        vars_str = "[" + ", ".join(f"'{v}'" for v in vars_selected) + "]"

        code = [
            f"# Pair Plot (Plotly)",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.to_pandas()",
            "else:",
            f"    _plot_df = df.copy()",
            "",
            f"vars_to_plot = {vars_str}",
        ]

        color_arg = f", color='{hue}'" if hue else ""
        
        code += [
            f"fig = px.scatter_matrix(_plot_df, dimensions=vars_to_plot{color_arg},",
            f"                        title='Pair Plot')",
            "fig.update_traces(diagonal_visible=False)",
            "",
            "if 'show_plotly' in globals():",
            "    show_plotly('Pair Plot', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
