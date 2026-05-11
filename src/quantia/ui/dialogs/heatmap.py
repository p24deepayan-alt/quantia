"""Correlation Heatmap Dialog.

Generates a seaborn heatmap for a correlation matrix.
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


class HeatmapDialog(BaseAnalysisDialog):
    """Dialog for creating correlation heatmaps."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Correlation Heatmap", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_vars = QListWidget()
        layout.addWidget(self._create_selector_row("Variables (select 2 or more numeric):", self.list_vars, multi_select=True))

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
        group_opts = QGroupBox("Correlation Options")
        l_opts = QVBoxLayout(group_opts)

        l_opts.addWidget(QLabel("Method:"))
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(["Pearson", "Spearman", "Kendall"])
        l_opts.addWidget(self.cmb_method)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        vars_selected = [self.list_vars.item(i).text() for i in range(self.list_vars.count())]

        if len(vars_selected) < 2:
            QMessageBox.warning(self, "Missing Input", "Please select at least 2 numeric variables.")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(vars_selected)
        return self._generate_matplotlib_code(vars_selected)

    def _generate_matplotlib_code(self, vars_selected: list[str]) -> str:
        style_name = self.cmb_style.currentText()
        method = self.cmb_method.currentText().lower()

        style_code = generate_style_code(style_name)
        title = f"Correlation Heatmap ({method.capitalize()})"

        code = [
            f"# {title}",
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            style_code,
            "",
            f"cols = {vars_selected}",
            "if isinstance(df, pl.DataFrame):",
            "    # Extract and calculate correlation using Pandas (seaborn/stats standard)",
            "    sub = df.select(cols).drop_nulls().to_pandas()",
            "else:",
            "    sub = df[cols].dropna()",
            "",
            f"corr = sub.corr(method='{method}')",
            "",
            "fig, ax = plt.subplots(figsize=(8, 6))",
            "colors = plt.rcParams['axes.prop_cycle'].by_key()['color']",
            "c_main = colors[0] if len(colors) > 0 else '#4C72B0'",
            "cmap = sns.diverging_palette(220, 20, as_cmap=True)  # Default fallback",
            "try:",
            "    # Attempt to create a diverging colormap from the primary style color to white to dark gray",
            "    cmap = sns.blend_palette(['#4A4A4A', '#FFFFFF', c_main], as_cmap=True)",
            "except Exception:",
            "    pass",
            "",
            "sns.heatmap(corr, annot=True, fmt='.2f', cmap=cmap, vmin=-1, vmax=1, center=0,",
            "            square=True, linewidths=.5, cbar_kws={'shrink': .8}, ax=ax)",
            f"ax.set_title('{title}', pad=20)",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('{title}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, vars_selected: list[str]) -> str:
        style_name = self.cmb_style.currentText()
        method = self.cmb_method.currentText().lower()
        style_code = generate_plotly_style_code(style_name)
        title = f"Correlation Heatmap ({method.capitalize()})"

        code = [
            f"# {title} (Plotly)",
            "import plotly.express as px",
            "import plotly.graph_objects as go",
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            style_code,
            "",
            f"cols = {vars_selected}",
            "if isinstance(df, pl.DataFrame):",
            "    sub = df.select(cols).drop_nulls().to_pandas()",
            "else:",
            "    sub = df[cols].dropna()",
            "",
            f"corr = sub.corr(method='{method}')",
            "",
            "fig = go.Figure(data=go.Heatmap(",
            "    z=corr.values,",
            "    x=corr.columns.tolist(),",
            "    y=corr.index.tolist(),",
            "    text=np.round(corr.values, 2),",
            "    texttemplate='%{text:.2f}',",
            "    colorscale='RdBu_r',",
            "    zmin=-1, zmax=1,",
            "    colorbar=dict(title='Correlation')",
            "))",
            f"fig.update_layout(title='{title}', width=700, height=600)",
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('{title}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
