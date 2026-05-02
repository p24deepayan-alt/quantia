"""Box Plot Dialog.

Generates seaborn boxplot code with style presets.
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
from quantia.ui.dialogs.base import BaseAnalysisDialog


class BoxPlotDialog(BaseAnalysisDialog):
    """Dialog for creating box plots."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Box Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_variable = QListWidget()
        layout.addWidget(self._create_selector_row("Variable (numeric):", self.list_variable, multi_select=False))

        self.list_group = QListWidget()
        layout.addWidget(self._create_selector_row("Group By (optional):", self.list_group, multi_select=False))

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

        l_opts.addWidget(QLabel("Orientation:"))
        self.cmb_orient = QComboBox()
        self.cmb_orient.addItems(["Vertical", "Horizontal"])
        l_opts.addWidget(self.cmb_orient)

        self.chk_notch = QCheckBox("Notched (show CI for median)")
        l_opts.addWidget(self.chk_notch)

        self.chk_swarm = QCheckBox("Overlay Data Points (Swarm)")
        l_opts.addWidget(self.chk_swarm)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        var = self.list_variable.item(0).text() if self.list_variable.count() > 0 else None
        group = self.list_group.item(0).text() if self.list_group.count() > 0 else None

        if not var:
            QMessageBox.warning(self, "Missing Input", "Please select a numeric variable.")
            return ""

        style_name = self.cmb_style.currentText()
        orient = "h" if self.cmb_orient.currentText() == "Horizontal" else "v"
        notch = self.chk_notch.isChecked()
        swarm = self.chk_swarm.isChecked()

        style_code = generate_style_code(style_name)

        if group:
            if orient == "v":
                x_arg, y_arg = f"x='{group}'", f"y='{var}'"
            else:
                x_arg, y_arg = f"x='{var}'", f"y='{group}'"
            title = f"{var} by {group}"
        else:
            if orient == "v":
                x_arg, y_arg = "", f"y='{var}'"
            else:
                x_arg, y_arg = f"x='{var}'", ""
            title = f"Distribution of {var}"

        args = ", ".join(a for a in [f"data=df", x_arg, y_arg] if a)

        code = [
            f"# Box Plot: {title}",
            style_code,
            "",
            "fig, ax = plt.subplots(figsize=(8, 5))",
            f"sns.boxplot({args}, notch={notch}, ax=ax)",
        ]

        if swarm:
            code.append(f"sns.swarmplot({args}, color='0.25', size=3, ax=ax)")

        code += [
            f"ax.set_title('{title}')",
            "fig.tight_layout()",
            "",
            "if 'show_plot' in globals():",
            f"    show_plot('Box Plot: {title}', fig)",
            "else:",
            "    plt.show()",
        ]

        return "\n".join(code)
