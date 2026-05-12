"""Q-Q Plot Dialog.

Generates a Quantile-Quantile plot to check if a numeric variable
follows a theoretical distribution (typically Normal).
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


class QQPlotDialog(BaseAnalysisDialog):
    """Dialog for generating a Q-Q Plot."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Q-Q Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_var = QListWidget()
        layout.addWidget(
            self._create_selector_row(
                "Numeric Variables (generates multiple plots):", self.list_var, multi_select=True
            )
        )

    def build_options(self, layout: QVBoxLayout) -> None:
        group_opts = QGroupBox("Plot Options")
        l_opts = QVBoxLayout(group_opts)

        l_opts.addWidget(QLabel("Distribution:"))
        self.cmb_dist = QComboBox()
        self.cmb_dist.addItems(["Normal (norm)", "Uniform (uniform)", "Exponential (expon)"])
        l_opts.addWidget(self.cmb_dist)
        
        l_opts.addWidget(QLabel("Plot Style Preset:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_opts.addWidget(self.cmb_style)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        vars_selected = [self.list_var.item(i).text() for i in range(self.list_var.count())]

        if not vars_selected:
            QMessageBox.warning(self, "Missing Input", "Please select at least one variable.")
            return ""

        dist_str = self.cmb_dist.currentText()
        if "norm" in dist_str:
            dist = "norm"
        elif "uniform" in dist_str:
            dist = "uniform"
        else:
            dist = "expon"

        if self._is_plotly():
            return self._generate_plotly_code(vars_selected, dist)
        return self._generate_matplotlib_code(vars_selected, dist)

    def _generate_matplotlib_code(self, vars_selected: list[str], dist: str) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_style_code(style_name)

        code = [
            f"# Q-Q Plots against {dist} distribution",
            "import polars as pl",
            "import pandas as pd",
            "import matplotlib.pyplot as plt",
            "import statsmodels.api as sm",
            "import scipy.stats as stats",
            "import io, base64",
            "",
            style_code,
            "",
        ]

        for var in vars_selected:
            code += [
                f"# Q-Q Plot: {var}",
                "if isinstance(df, pl.DataFrame):",
                f"    data = df.get_column('{var}').drop_nulls().to_pandas()",
                "else:",
                f"    data = df['{var}'].dropna()",
                "",
                "fig, ax = plt.subplots(figsize=(7, 6))",
                f"dist_func = getattr(stats, '{dist}')",
                "colors = plt.rcParams['axes.prop_cycle'].by_key()['color']",
                "c_main = colors[0] if len(colors) > 0 else '#4C72B0'",
                "c_line = colors[1] if len(colors) > 1 else '#C44E52'",
                "",
                "# Create the Q-Q plot",
                "sm.qqplot(data, dist=dist_func, line='s', ax=ax, markerfacecolor=c_main, markeredgecolor='white', alpha=0.7)",
                "",
                "# Fix the reference line color (statsmodels sets it to red by default)",
                "for line in ax.get_lines():",
                "    if line.get_linestyle() == '-':",
                "        line.set_color(c_line)",
                "        line.set_linewidth(2)",
                "",
                f"ax.set_title(f'Q-Q Plot of {var} vs {dist.capitalize()}', pad=16)",
                "ax.set_xlabel('Theoretical Quantiles', labelpad=10)",
                "ax.set_ylabel('Sample Quantiles', labelpad=10)",
                "ax.grid(True, alpha=0.3, linestyle='--')",
                "fig.tight_layout()",
                "",
                "if 'show_plot' in globals():",
                f"    show_plot('Q-Q Plot: {var}', fig)",
                "else:",
                "    plt.show()",
                "",
            ]

        return "\n".join(code)

    def _generate_plotly_code(self, vars_selected: list[str], dist: str) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_plotly_style_code(style_name)

        code = [
            f"# Q-Q Plots (Plotly) against {dist} distribution",
            "import plotly.graph_objects as go",
            "import numpy as np",
            "import scipy.stats as stats",
            "import polars as pl",
            style_code,
            "",
            f"dist_func = getattr(stats, '{dist}')",
            "",
        ]

        for var in vars_selected:
            code += [
                f"# Q-Q Plot (Plotly): {var}",
                "if isinstance(df, pl.DataFrame):",
                f"    _data = df.get_column('{var}').drop_nulls().to_pandas().values",
                "else:",
                f"    _data = df['{var}'].dropna().values",
                "",
                "(osm, osr), (slope, intercept, _) = stats.probplot(_data, dist=dist_func, plot=None)",
                "",
                "fig = go.Figure()",
                "fig.add_trace(go.Scatter(x=osm, y=osr, mode='markers', name='Sample',",
                "                        marker=dict(opacity=0.7)))",
                "fig.add_trace(go.Scatter(x=osm, y=intercept + slope * np.array(osm),",
                "                        mode='lines', name='Reference Line',",
                "                        line=dict(width=2, dash='dash')))",
                f"fig.update_layout(title='Q-Q Plot of {var} vs {dist.capitalize()}',",
                "                  xaxis_title='Theoretical Quantiles',",
                "                  yaxis_title='Sample Quantiles')",
                "",
                "if 'show_plotly' in globals():",
                f"    show_plotly('Q-Q Plot: {var}', fig.to_html(include_plotlyjs='cdn'))",
                "else:",
                "    fig.show()",
                "",
            ]

        return "\n".join(code)
