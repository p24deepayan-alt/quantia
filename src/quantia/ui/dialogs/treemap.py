"""Treemap / Sunburst Chart Dialog.

Generates Plotly interactive hierarchical charts.
Falls back to nested grouping for Matplotlib (bar chart).
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


class TreemapDialog(BaseAnalysisDialog):
    """Dialog for creating Treemap and Sunburst charts."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Treemap / Sunburst Chart", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_path = QListWidget()
        row_path = self._create_selector_row("Hierarchy Path (Categories):", self.list_path, multi_select=True)
        layout.addWidget(row_path)

        self.list_val = QListWidget()
        row_val = self._create_selector_row("Values (Optional numeric):", self.list_val, multi_select=False)
        layout.addWidget(row_val)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_opts = QGroupBox("Plot Options")
        l_opts = QVBoxLayout(group_opts)

        l_opts.addWidget(QLabel("Plot Type:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Treemap", "Sunburst"])
        l_opts.addWidget(self.cmb_type)
        
        l_opts.addWidget(QLabel("Preset Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_opts.addWidget(self.cmb_style)
        
        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        path_vars = [self.list_path.item(i).text() for i in range(self.list_path.count())]
        
        if not path_vars:
            QMessageBox.warning(self, "Missing Input", "Please select at least one category for the hierarchy.")
            return ""

        val_var = self.list_val.item(0).text() if self.list_val.count() > 0 else None

        if self._is_plotly():
            return self._generate_plotly_code(path_vars, val_var)
        return self._generate_matplotlib_code(path_vars, val_var)

    def _generate_matplotlib_code(self, path_vars: list[str], val_var: str | None) -> str:
        style_name = self.cmb_style.currentText()
        plot_type = self.cmb_type.currentText()
        style_code = generate_style_code(style_name)

        code = [
            f"# {plot_type}: Matplotlib Fallback",
            "# Note: True Treemaps/Sunbursts are best viewed with Plotly.",
            "# Generating a horizontal stacked bar chart instead.",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            f"    _plot_df = df.to_pandas()",
            "else:",
            f"    _plot_df = df.copy()",
            "",
        ]

        path_str = "[" + ", ".join(f"'{p}'" for p in path_vars) + "]"
        
        if val_var:
            code.append(f"grouped = _plot_df.groupby({path_str})['{val_var}'].sum().unstack().fillna(0)")
        else:
            if len(path_vars) > 1:
                group_cols = "[" + ", ".join(f"'{p}'" for p in path_vars[:-1]) + "]"
                code.append(f"grouped = _plot_df.groupby({path_str}).size().unstack().fillna(0)")
            else:
                code.append(f"grouped = _plot_df['{path_vars[0]}'].value_counts().to_frame('Count')")

        code += [
            "fig, ax = plt.subplots(figsize=(10, 6))",
            "grouped.plot(kind='barh', stacked=True, ax=ax)",
            f"ax.set_title('Hierarchical Breakdown')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('Hierarchy', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, path_vars: list[str], val_var: str | None) -> str:
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
            f"    _plot_df = df.to_pandas()",
            "else:",
            f"    _plot_df = df.copy()",
            "",
        ]

        path_str = "[" + ", ".join(f"'{p}'" for p in path_vars) + "]"
        val_arg = f", values='{val_var}'" if val_var else ""

        px_func = "px.treemap" if plot_type == "Treemap" else "px.sunburst"

        # Handle NAs in paths as plotly will crash if there are NAs
        code.append(f"_plot_df = _plot_df.dropna(subset={path_str})")
        code.append(f"fig = {px_func}(_plot_df, path={path_str}{val_arg},")
        code.append(f"                title='{plot_type} Breakdown')")
        code.append("fig.update_traces(root_color='lightgrey')")

        code += [
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('{plot_type}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
