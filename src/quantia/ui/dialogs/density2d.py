"""2D Density / Hexbin Plot Dialog.

Generates seaborn kdeplot or matplotlib hexbin code.
Supports Plotly backend (px.density_contour/heatmap) for interactive visualizations.
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


class Density2DPlotDialog(BaseAnalysisDialog):
    """Dialog for creating 2D Density and Hexbin plots."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("2D Density / Hexbin Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_x = QListWidget()
        row_x = self._create_selector_row("Numeric Variable (X):", self.list_x, multi_select=False)
        layout.addWidget(row_x)

        self.list_y = QListWidget()
        row_y = self._create_selector_row("Numeric Variable (Y):", self.list_y, multi_select=False)
        layout.addWidget(row_y)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_opts = QGroupBox("Plot Options")
        l_opts = QVBoxLayout(group_opts)

        l_opts.addWidget(QLabel("Plot Type:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["2D KDE Contour", "Hexbin"])
        l_opts.addWidget(self.cmb_type)
        
        l_opts.addWidget(QLabel("Preset Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_opts.addWidget(self.cmb_style)
        
        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        x_var = self.list_x.item(0).text() if self.list_x.count() > 0 else None
        y_var = self.list_y.item(0).text() if self.list_y.count() > 0 else None
        
        if not x_var or not y_var:
            QMessageBox.warning(self, "Missing Input", "Please select both X and Y numeric variables.")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(x_var, y_var)
        return self._generate_matplotlib_code(x_var, y_var)

    def _generate_matplotlib_code(self, x_var: str, y_var: str) -> str:
        style_name = self.cmb_style.currentText()
        plot_type = self.cmb_type.currentText()
        style_code = generate_style_code(style_name)

        code = [
            f"# {plot_type}: {x_var} vs {y_var}",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.select(['{x_var}', '{y_var}']).drop_nulls().to_pandas()",
            "else:",
            f"    _plot_df = df[['{x_var}', '{y_var}']].dropna()",
            "",
            "fig, ax = plt.subplots(figsize=(8, 6))"
        ]

        if plot_type == "2D KDE Contour":
            code.append(f"sns.kdeplot(data=_plot_df, x='{x_var}', y='{y_var}', fill=True, cmap='viridis', ax=ax, thresh=0.05)")
        else:
            code.append(f"hb = ax.hexbin(_plot_df['{x_var}'], _plot_df['{y_var}'], gridsize=30, cmap='Blues', mincnt=1)")
            code.append("cb = fig.colorbar(hb, ax=ax)")
            code.append("cb.set_label('Count')")

        code += [
            f"ax.set_title('{plot_type}: {x_var} vs {y_var}')",
            f"ax.set_xlabel('{x_var}')",
            f"ax.set_ylabel('{y_var}')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('{plot_type}: {x_var}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, x_var: str, y_var: str) -> str:
        style_name = self.cmb_style.currentText()
        plot_type = self.cmb_type.currentText()
        style_code = generate_plotly_style_code(style_name)

        code = [
            f"# {plot_type} (Plotly): {x_var} vs {y_var}",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.select(['{x_var}', '{y_var}']).drop_nulls().to_pandas()",
            "else:",
            f"    _plot_df = df[['{x_var}', '{y_var}']].dropna()",
            "",
        ]

        if plot_type == "2D KDE Contour":
            code.append(f"fig = px.density_contour(_plot_df, x='{x_var}', y='{y_var}',")
            code.append(f"                         title='{plot_type}: {x_var} vs {y_var}')")
            code.append("fig.update_traces(contours_coloring='fill', contours_showlabels=True)")
        else:
            code.append(f"fig = px.density_heatmap(_plot_df, x='{x_var}', y='{y_var}', nbinsx=30, nbinsy=30,")
            code.append(f"                         title='{plot_type}: {x_var} vs {y_var}')")

        code += [
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('{plot_type}: {x_var}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
