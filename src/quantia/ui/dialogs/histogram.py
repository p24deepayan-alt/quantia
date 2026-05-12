"""Histogram Dialog.

Generates seaborn histplot code with style presets.
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
    QSpinBox,
    QHBoxLayout,
    QVBoxLayout,
)

from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from quantia.ui.central.plotly_styles import PLOTLY_STYLE_NAMES, generate_plotly_style_code
from quantia.ui.dialogs.base import BaseAnalysisDialog


class HistogramDialog(BaseAnalysisDialog):
    """Dialog for creating histograms."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Histogram", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_variable = QListWidget()
        row = self._create_selector_row("Variables (generates multiple plots):", self.list_variable, multi_select=True)
        layout.addWidget(row)

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

        bin_layout = QHBoxLayout()
        bin_layout.addWidget(QLabel("Number of Bins:"))
        self.spn_bins = QSpinBox()
        self.spn_bins.setRange(5, 200)
        self.spn_bins.setValue(30)
        bin_layout.addWidget(self.spn_bins)
        
        self.chk_auto_bins = QCheckBox("Auto")
        self.chk_auto_bins.setChecked(True)
        self.chk_auto_bins.toggled.connect(lambda checked: self.spn_bins.setEnabled(not checked))
        self.spn_bins.setEnabled(False)
        bin_layout.addWidget(self.chk_auto_bins)
        
        l_opts.addLayout(bin_layout)

        self.chk_kde = QCheckBox("Overlay KDE Curve")
        self.chk_kde.setChecked(True)
        l_opts.addWidget(self.chk_kde)

        self.chk_rug = QCheckBox("Show Rug Plot")
        l_opts.addWidget(self.chk_rug)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        vars_selected = [self.list_variable.item(i).text() for i in range(self.list_variable.count())]
        if not vars_selected:
            QMessageBox.warning(self, "Missing Input", "Please select at least one variable.")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(vars_selected)
        return self._generate_matplotlib_code(vars_selected)

    def _generate_matplotlib_code(self, vars_selected: list[str]) -> str:
        style_name = self.cmb_style.currentText()
        kde = self.chk_kde.isChecked()
        rug = self.chk_rug.isChecked()

        style_code = generate_style_code(style_name)
        
        bins_arg = "bins='auto'" if self.chk_auto_bins.isChecked() else f"bins={self.spn_bins.value()}"

        code = [
            f"# Histograms",
            style_code,
            "",
        ]

        for var in vars_selected:
            code += [
                f"# Histogram: {var}",
                "fig, ax = plt.subplots(figsize=(8, 5))",
                f"sns.histplot(data=df, x='{var}', {bins_arg}, kde={kde}, ax=ax)",
            ]

            if rug:
                code.append(f"sns.rugplot(data=df, x='{var}', ax=ax, alpha=0.3)")

            code += [
                f"ax.set_title('Distribution of {var}')",
                f"ax.set_xlabel('{var}')",
                "ax.set_ylabel('Count')",
                "fig.tight_layout()",
                "",
                "if 'show_plot' in globals():",
                f"    show_plot('Histogram: {var}', fig)",
                "else:",
                "    plt.show()",
                "",
            ]

        return "\n".join(code)

    def _generate_plotly_code(self, vars_selected: list[str]) -> str:
        style_name = self.cmb_style.currentText()
        kde = self.chk_kde.isChecked()
        rug = self.chk_rug.isChecked()

        style_code = generate_plotly_style_code(style_name)

        marginal = "'rug'" if rug else ("'violin'" if kde else "None")
        
        bins_arg = "" if self.chk_auto_bins.isChecked() else f"nbins={self.spn_bins.value()}, "

        code = [
            f"# Histograms (Plotly)",
            "import plotly.express as px",
            "import plotly.graph_objects as go",
            style_code,
            "",
            "import polars as pl",
            "is_pl = isinstance(df, pl.DataFrame)",
            "",
        ]

        for var in vars_selected:
            code += [
                f"# Histogram (Plotly): {var}",
                f"if is_pl:",
                f"    _plot_df = df.select('{var}').drop_nulls().to_pandas()",
                "else:",
                f"    _plot_df = df[['{var}']].dropna()",
                "",
                f"fig = px.histogram(_plot_df, x='{var}', {bins_arg}marginal={marginal},",
                f"                   title='Distribution of {var}')",
            ]

            if kde and not rug:
                code.append("fig.update_traces(opacity=0.75)")
                code.append(f"# Add KDE overlay")
                code.append(f"import numpy as np")
                code.append(f"from scipy.stats import gaussian_kde")
                code.append(f"_data = _plot_df['{var}'].values")
                code.append(f"_kde = gaussian_kde(_data)")
                code.append(f"_x_range = np.linspace(_data.min(), _data.max(), 200)")
                if self.chk_auto_bins.isChecked():
                    code.append(f"_, _bins = np.histogram(_data, bins='auto')")
                    code.append(f"_bin_width = _bins[1] - _bins[0]")
                    code.append(f"_kde_vals = _kde(_x_range) * len(_data) * _bin_width")
                else:
                    code.append(f"_kde_vals = _kde(_x_range) * len(_data) * (_data.max() - _data.min()) / {self.spn_bins.value()}")
                code.append(f"fig.add_trace(go.Scatter(x=_x_range, y=_kde_vals, mode='lines', name='KDE',")
                code.append(f"                        line=dict(width=2)))")

            code += [
                f"fig.update_layout(xaxis_title='{var}', yaxis_title='Count')",
                "",
                "if 'show_plotly' in globals():",
                f"    show_plotly('Histogram: {var}', fig.to_html(include_plotlyjs='cdn'))",
                "else:",
                "    fig.show()",
                "",
            ]

        return "\n".join(code)
