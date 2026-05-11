"""Bar Chart Dialog.

Generates seaborn barplot / countplot code with style presets.
Supports Plotly backend for interactive visualizations.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
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


class BarChartDialog(BaseAnalysisDialog):
    """Dialog for creating bar charts."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Bar Chart", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_category = QListWidget()
        layout.addWidget(self._create_selector_row("Category Variable:", self.list_category, multi_select=False))

        self.list_value = QListWidget()
        layout.addWidget(self._create_selector_row("Value Variable (optional):", self.list_value, multi_select=False))

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

        l_opts.addWidget(QLabel("Aggregation (when Value is set):"))
        self.cmb_agg = QComboBox()
        self.cmb_agg.addItems(["mean", "sum", "median", "count"])
        l_opts.addWidget(self.cmb_agg)

        l_opts.addWidget(QLabel("Orientation:"))
        self.cmb_orient = QComboBox()
        self.cmb_orient.addItems(["Vertical", "Horizontal"])
        l_opts.addWidget(self.cmb_orient)

        self.chk_errorbars = QCheckBox("Show Error Bars (CI 95%)")
        self.chk_errorbars.setChecked(True)
        l_opts.addWidget(self.chk_errorbars)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        cat = self.list_category.item(0).text() if self.list_category.count() > 0 else None
        val = self.list_value.item(0).text() if self.list_value.count() > 0 else None

        if not cat:
            QMessageBox.warning(self, "Missing Input", "Please select a category variable.")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(cat, val)
        return self._generate_matplotlib_code(cat, val)

    def _generate_matplotlib_code(self, cat: str, val: str | None) -> str:
        style_name = self.cmb_style.currentText()
        agg = self.cmb_agg.currentText()
        orient = self.cmb_orient.currentText()
        errorbars = self.chk_errorbars.isChecked()

        style_code = generate_style_code(style_name)
        ci_arg = "('ci', 95)" if errorbars else "None"

        code = [
            f"# Bar Chart: {cat}" + (f" vs {val}" if val else ""),
            style_code,
            "",
            "fig, ax = plt.subplots(figsize=(8, 5))",
        ]

        if val:
            if orient == "Vertical":
                code.append(f"sns.barplot(data=df, x='{cat}', y='{val}', estimator='{agg}', errorbar={ci_arg}, ax=ax)")
            else:
                code.append(f"sns.barplot(data=df, x='{val}', y='{cat}', estimator='{agg}', errorbar={ci_arg}, orient='h', ax=ax)")
            title = f"{agg.title()} of {val} by {cat}"
        else:
            if orient == "Vertical":
                code.append(f"sns.countplot(data=df, x='{cat}', ax=ax)")
            else:
                code.append(f"sns.countplot(data=df, y='{cat}', ax=ax)")
            title = f"Count of {cat}"

        code += [
            f"ax.set_title('{title}')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('Bar Chart: {title}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)

    def _generate_plotly_code(self, cat: str, val: str | None) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_plotly_style_code(style_name)
        agg = self.cmb_agg.currentText()
        orient = self.cmb_orient.currentText()

        code = [
            f"# Bar Chart (Plotly): {cat}" + (f" vs {val}" if val else ""),
            "import plotly.express as px",
            "import pandas as pd",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            "    _plot_df = df.to_pandas()",
            "else:",
            "    _plot_df = df.copy()",
            "",
        ]

        if val:
            title = f"{agg.title()} of {val} by {cat}"
            if orient == "Vertical":
                code.append(f"fig = px.bar(_plot_df.groupby('{cat}', as_index=False)['{val}'].{agg}(),")
                code.append(f"            x='{cat}', y='{val}', title='{title}')")
            else:
                code.append(f"fig = px.bar(_plot_df.groupby('{cat}', as_index=False)['{val}'].{agg}(),")
                code.append(f"            x='{val}', y='{cat}', orientation='h', title='{title}')")
        else:
            title = f"Count of {cat}"
            code.append(f"_counts = _plot_df['{cat}'].value_counts().reset_index()")
            code.append(f"_counts.columns = ['{cat}', 'count']")
            if orient == "Vertical":
                code.append(f"fig = px.bar(_counts, x='{cat}', y='count', title='{title}')")
            else:
                code.append(f"fig = px.bar(_counts, x='count', y='{cat}', orientation='h', title='{title}')")

        code += [
            "",
            "if 'show_plotly' in globals():",
            f"    show_plotly('Bar Chart: {title}', fig.to_html(include_plotlyjs='cdn'))",
            "else:",
            "    fig.show()",
        ]

        return "\n".join(code)
