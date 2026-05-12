"""Ridge Plot (Joyplot) Dialog.

Generates seaborn FacetGrid KDE code.
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


class RidgePlotDialog(BaseAnalysisDialog):
    """Dialog for creating Ridge Plots."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Ridge Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_x = QListWidget()
        row_x = self._create_selector_row("Numeric Variable (X):", self.list_x, multi_select=False)
        layout.addWidget(row_x)

        self.list_y = QListWidget()
        row_y = self._create_selector_row("Category (Y):", self.list_y, multi_select=False)
        layout.addWidget(row_y)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_style = QGroupBox("Style")
        l_style = QVBoxLayout(group_style)
        l_style.addWidget(QLabel("Preset:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_style.addWidget(self.cmb_style)
        layout.addWidget(group_style)

    def generate_code(self) -> str:
        x_var = self.list_x.item(0).text() if self.list_x.count() > 0 else None
        y_var = self.list_y.item(0).text() if self.list_y.count() > 0 else None
        
        if not x_var or not y_var:
            QMessageBox.warning(self, "Missing Input", "Please select both a numeric variable (X) and a category (Y).")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(x_var, y_var)
        return self._generate_matplotlib_code(x_var, y_var)

    def _generate_matplotlib_code(self, x_var: str, y_var: str) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_style_code(style_name)

        code = [
            f"# Ridge Plot: {x_var} by {y_var}",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.select(['{x_var}', '{y_var}']).drop_nulls().to_pandas()",
            "else:",
            f"    _plot_df = df[['{x_var}', '{y_var}']].dropna()",
            "",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            f"sns.set_theme(style='white', rc={{'axes.facecolor': (0, 0, 0, 0)}})",
            "",
            f"g = sns.FacetGrid(_plot_df, row='{y_var}', hue='{y_var}', aspect=8, height=1.0)",
            f"g.map(sns.kdeplot, '{x_var}', bw_adjust=.5, clip_on=False, fill=True, alpha=1, linewidth=1.5)",
            f"g.map(sns.kdeplot, '{x_var}', clip_on=False, color='w', lw=2, bw_adjust=.5)",
            "g.refline(y=0, linewidth=2, linestyle='-', color=None, clip_on=False)",
            "",
            "def label(x, color, label):",
            "    ax = plt.gca()",
            "    ax.text(0, .2, label, fontweight='bold', color=color,",
            "            ha='left', va='center', transform=ax.transAxes)",
            f"g.map(label, '{x_var}')",
            "",
            "g.figure.subplots_adjust(hspace=-.25)",
            "g.set_titles('')",
            "g.set(yticks=[], ylabel='')",
            "g.despine(bottom=True, left=True)",
            f"g.figure.suptitle('Ridge Plot: {x_var} by {y_var}', y=1.02)",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('Ridge Plot: {x_var}', g.figure)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, x_var: str, y_var: str) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_plotly_style_code(style_name)

        code = [
            f"# Ridge Plot (Plotly): {x_var} by {y_var}",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.select(['{x_var}', '{y_var}']).drop_nulls().to_pandas()",
            "else:",
            f"    _plot_df = df[['{x_var}', '{y_var}']].dropna()",
            "",
            f"fig = px.violin(_plot_df, x='{x_var}', y='{y_var}', color='{y_var}',",
            f"                orientation='h', side='positive',",
            f"                title='Ridge Plot: {x_var} by {y_var}')",
            "fig.update_traces(width=3, points=False)",
            "fig.update_layout(violingap=0, violinmode='overlay', showlegend=False)",
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('Ridge Plot: {x_var}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
