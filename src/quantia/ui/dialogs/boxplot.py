"""Box Plot Dialog.

Generates seaborn boxplot code with style presets.
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


class BoxPlotDialog(BaseAnalysisDialog):
    """Dialog for creating box plots."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Box Plot", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_variable = QListWidget()
        layout.addWidget(self._create_selector_row("Variables (numeric, generates multiple plots):", self.list_variable, multi_select=True))

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
        vars_selected = [self.list_variable.item(i).text() for i in range(self.list_variable.count())]
        group = self.list_group.item(0).text() if self.list_group.count() > 0 else None

        if not vars_selected:
            QMessageBox.warning(self, "Missing Input", "Please select at least one numeric variable.")
            return ""

        if self._is_plotly():
            return self._generate_plotly_code(vars_selected, group)
        return self._generate_matplotlib_code(vars_selected, group)

    def _generate_matplotlib_code(self, vars_selected: list[str], group: str | None) -> str:
        style_name = self.cmb_style.currentText()
        orient = "h" if self.cmb_orient.currentText() == "Horizontal" else "v"
        notch = self.chk_notch.isChecked()
        swarm = self.chk_swarm.isChecked()

        style_code = generate_style_code(style_name)

        code = [
            f"# Box Plots",
            style_code,
            "",
        ]

        for var in vars_selected:
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

            code += [
                f"# Box Plot: {title}",
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
                "",
            ]

        return "\n".join(code)

    def _generate_plotly_code(self, vars_selected: list[str], group: str | None) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_plotly_style_code(style_name)
        notch = self.chk_notch.isChecked()
        points = "'all'" if self.chk_swarm.isChecked() else "False"

        color_arg = f", color='{group}'" if group else ""

        code = [
            f"# Box Plots (Plotly)",
            "import plotly.express as px",
            style_code,
            "",
            "import polars as pl",
            "if isinstance(df, pl.DataFrame):",
            "    _plot_df = df.to_pandas()",
            "else:",
            "    _plot_df = df.copy()",
            "",
        ]

        for var in vars_selected:
            title = f"{var} by {group}" if group else f"Distribution of {var}"

            code += [
                f"# Box Plot (Plotly): {title}",
                f"fig = px.box(_plot_df, y='{var}'{color_arg}, notched={notch}, points={points},",
                f"             title='{title}')",
                "",
                "if 'show_plotly' in globals():",
                f"    show_plotly('Box Plot: {title}', fig.to_html(include_plotlyjs='cdn'))",
                "else:",
                "    fig.show()",
                "",
            ]

        return "\n".join(code)
