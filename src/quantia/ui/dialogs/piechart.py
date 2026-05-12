"""Pie / Donut Chart Dialog.

Generates pandas plotting code for matplotlib.
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


class PieChartDialog(BaseAnalysisDialog):
    """Dialog for creating Pie and Donut charts."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Pie / Donut Chart", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_cat = QListWidget()
        row_cat = self._create_selector_row("Category (Labels):", self.list_cat, multi_select=False)
        layout.addWidget(row_cat)

        self.list_val = QListWidget()
        row_val = self._create_selector_row("Values (Optional):", self.list_val, multi_select=False)
        layout.addWidget(row_val)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_opts = QGroupBox("Plot Options")
        l_opts = QVBoxLayout(group_opts)

        l_opts.addWidget(QLabel("Plot Type:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Pie Chart", "Donut Chart"])
        l_opts.addWidget(self.cmb_type)
        
        l_opts.addWidget(QLabel("Preset Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_opts.addWidget(self.cmb_style)
        
        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        cat_var = self.list_cat.item(0).text() if self.list_cat.count() > 0 else None
        
        if not cat_var:
            QMessageBox.warning(self, "Missing Input", "Please select a category for the labels.")
            return ""

        val_var = self.list_val.item(0).text() if self.list_val.count() > 0 else None

        if self._is_plotly():
            return self._generate_plotly_code(cat_var, val_var)
        return self._generate_matplotlib_code(cat_var, val_var)

    def _generate_matplotlib_code(self, cat_var: str, val_var: str | None) -> str:
        style_name = self.cmb_style.currentText()
        plot_type = self.cmb_type.currentText()
        style_code = generate_style_code(style_name)

        code = [
            f"# {plot_type}: {cat_var}",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.to_pandas()",
            "else:",
            f"    _plot_df = df.copy()",
            "",
        ]

        if val_var:
            code.append(f"counts = _plot_df.groupby('{cat_var}')['{val_var}'].sum()")
        else:
            code.append(f"counts = _plot_df['{cat_var}'].value_counts()")

        code.append("fig, ax = plt.subplots(figsize=(8, 8))")
        
        if plot_type == "Donut Chart":
            code.append("wedges, texts, autotexts = ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4))")
        else:
            code.append("wedges, texts, autotexts = ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90)")

        code += [
            f"ax.set_title('{plot_type}: {cat_var}')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('{plot_type}: {cat_var}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, cat_var: str, val_var: str | None) -> str:
        style_name = self.cmb_style.currentText()
        plot_type = self.cmb_type.currentText()
        style_code = generate_plotly_style_code(style_name)

        code = [
            f"# {plot_type} (Plotly): {cat_var}",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.to_pandas()",
            "else:",
            f"    _plot_df = df.copy()",
            "",
        ]

        val_arg = f", values='{val_var}'" if val_var else ""
        hole_arg = ", hole=0.4" if plot_type == "Donut Chart" else ""

        if not val_var:
            # Need to compute counts for px.pie if no values provided, or we can just let px.pie do it if we give it the whole dataframe?
            # Wait, px.pie requires values. Actually, if you omit values, it defaults to counting the rows. Let's just pass the df.
            pass

        code += [
            f"fig = px.pie(_plot_df, names='{cat_var}'{val_arg}{hole_arg},",
            f"             title='{plot_type}: {cat_var}')",
            "fig.update_traces(textposition='inside', textinfo='percent+label')",
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('{plot_type}: {cat_var}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
