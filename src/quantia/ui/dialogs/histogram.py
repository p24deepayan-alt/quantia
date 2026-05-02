"""Histogram Dialog.

Generates seaborn histplot code with style presets.
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
    QVBoxLayout,
)

from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from quantia.ui.dialogs.base import BaseAnalysisDialog


class HistogramDialog(BaseAnalysisDialog):
    """Dialog for creating histograms."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Histogram", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_variable = QListWidget()
        row = self._create_selector_row("Variable:", self.list_variable, multi_select=False)
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

        l_opts.addWidget(QLabel("Number of Bins:"))
        self.spn_bins = QSpinBox()
        self.spn_bins.setRange(5, 200)
        self.spn_bins.setValue(30)
        l_opts.addWidget(self.spn_bins)

        self.chk_kde = QCheckBox("Overlay KDE Curve")
        self.chk_kde.setChecked(True)
        l_opts.addWidget(self.chk_kde)

        self.chk_rug = QCheckBox("Show Rug Plot")
        l_opts.addWidget(self.chk_rug)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        var = self.list_variable.item(0).text() if self.list_variable.count() > 0 else None
        if not var:
            QMessageBox.warning(self, "Missing Input", "Please select a variable.")
            return ""

        style_name = self.cmb_style.currentText()
        bins = self.spn_bins.value()
        kde = self.chk_kde.isChecked()
        rug = self.chk_rug.isChecked()

        style_code = generate_style_code(style_name)

        code = [
            f"# Histogram: {var}",
            style_code,
            "",
            "fig, ax = plt.subplots(figsize=(8, 5))",
            f"sns.histplot(data=df, x='{var}', bins={bins}, kde={kde}, ax=ax)",
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
        ]

        return "\n".join(code)
