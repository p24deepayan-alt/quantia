"""Strip / Swarm Plot Dialog.

Generates seaborn stripplot or swarmplot code.
Supports Plotly backend (using px.strip) for interactive visualizations.
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


class StripPlotDialog(BaseAnalysisDialog):
    """Dialog for creating strip and swarm plots."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Strip / Swarm Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_y = QListWidget()
        row_y = self._create_selector_row("Numeric Variable (Y):", self.list_y, multi_select=False)
        layout.addWidget(row_y)

        self.list_x = QListWidget()
        row_x = self._create_selector_row("Category (X):", self.list_x, multi_select=False)
        layout.addWidget(row_x)

        self.list_hue = QListWidget()
        row_hue = self._create_selector_row("Color (Hue) - Optional:", self.list_hue, multi_select=False)
        layout.addWidget(row_hue)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_opts = QGroupBox("Plot Options")
        l_opts = QVBoxLayout(group_opts)

        l_opts.addWidget(QLabel("Plot Type:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Strip Plot", "Swarm Plot"])
        l_opts.addWidget(self.cmb_type)
        
        l_opts.addWidget(QLabel("Preset Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_opts.addWidget(self.cmb_style)
        
        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        y_var = self.list_y.item(0).text() if self.list_y.count() > 0 else None
        x_var = self.list_x.item(0).text() if self.list_x.count() > 0 else None
        
        if not y_var or not x_var:
            QMessageBox.warning(self, "Missing Input", "Please select both a numeric variable (Y) and a category (X).")
            return ""

        hue = self.list_hue.item(0).text() if self.list_hue.count() > 0 else None

        if self._is_plotly():
            return self._generate_plotly_code(y_var, x_var, hue)
        return self._generate_matplotlib_code(y_var, x_var, hue)

    def _generate_matplotlib_code(self, y_var: str, x_var: str, hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        plot_type = self.cmb_type.currentText()
        style_code = generate_style_code(style_name)

        code = [
            f"# {plot_type}",
            style_code,
            "",
            "fig, ax = plt.subplots(figsize=(8, 5))"
        ]

        hue_arg = f", hue='{hue}', dodge=True" if hue else ""
        sns_func = "sns.swarmplot" if plot_type == "Swarm Plot" else "sns.stripplot"
        
        code.append(f"{sns_func}(data=df, x='{x_var}', y='{y_var}'{hue_arg}, ax=ax, alpha=0.7)")

        code += [
            f"ax.set_title('{plot_type}: {y_var} by {x_var}')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('{plot_type}: {y_var}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, y_var: str, x_var: str, hue: str | None) -> str:
        style_name = self.cmb_style.currentText()
        plot_type = self.cmb_type.currentText()
        style_code = generate_plotly_style_code(style_name)

        code = [
            f"# {plot_type} (Plotly)",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.select(['{y_var}', '{x_var}'" + (f", '{hue}'" if hue else "") + "]).drop_nulls().to_pandas()",
            "else:",
            f"    _plot_df = df[['{y_var}', '{x_var}'" + (f", '{hue}'" if hue else "") + "]].dropna()",
            "",
        ]

        color_arg = f", color='{hue}'" if hue else ""
        stripmode = ", stripmode='group'" if hue else ""
        
        code += [
            f"fig = px.strip(_plot_df, x='{x_var}', y='{y_var}'{color_arg}{stripmode},",
            f"               title='{plot_type}: {y_var} by {x_var}')",
        ]

        code += [
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('{plot_type}: {y_var}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
