"""Dashboard Builder Tab."""

from __future__ import annotations

from typing import Iterable
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGridLayout, QGroupBox, QLineEdit,
    QMessageBox, QScrollArea
)

from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from quantia.ui.icons import feather_icon


class DashboardTabWidget(QWidget):
    """Tab for creating a dashboard of multiple plots."""

    code_generated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        from quantia.theme.palette import PALETTE, Theme
        app = QApplication.instance()
        self._theme = app.get_current_theme() if isinstance(app, QuantiaApp) else Theme.LIGHT
        self._icon_color = PALETTE[self._theme]["text_primary"]

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)

        # Top section: Title and Style
        top_layout = QHBoxLayout()
        lbl_title = QLabel("Dashboard Title:")
        lbl_title.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(lbl_title)
        self.txt_title = QLineEdit("My Dashboard")
        top_layout.addWidget(self.txt_title)
        
        top_layout.addSpacing(40)
        
        lbl_style = QLabel("Style Preset:")
        lbl_style.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(lbl_style)
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        top_layout.addWidget(self.cmb_style)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        layout.addSpacing(20)

        # Middle section: Plot Grid (2x2 max for simplicity)
        self.plot_configs = []
        grid = QGridLayout()
        grid.setSpacing(20)
        
        for i in range(4):
            grp = QGroupBox(f"Panel {i+1}")
            grp.setCheckable(True)
            grp.setChecked(i == 0) # Only first one checked by default
            
            glay = QGridLayout(grp)
            glay.setSpacing(10)
            
            glay.addWidget(QLabel("Plot Type:"), 0, 0)
            cmb_type = QComboBox()
            cmb_type.addItems(["Scatter", "Bar", "Line", "Histogram", "Box Plot", "Violin"])
            glay.addWidget(cmb_type, 0, 1)
            
            glay.addWidget(QLabel("X Variable:"), 1, 0)
            cmb_x = QComboBox()
            cmb_x.addItem("-- None --")
            glay.addWidget(cmb_x, 1, 1)
            
            glay.addWidget(QLabel("Y Variable:"), 2, 0)
            cmb_y = QComboBox()
            cmb_y.addItem("-- None --")
            glay.addWidget(cmb_y, 2, 1)
            
            glay.addWidget(QLabel("Color By (Hue):"), 3, 0)
            cmb_hue = QComboBox()
            cmb_hue.addItem("-- None --")
            glay.addWidget(cmb_hue, 3, 1)
            
            self.plot_configs.append({
                "group": grp,
                "type": cmb_type,
                "x": cmb_x,
                "y": cmb_y,
                "hue": cmb_hue
            })
            
            row, col = divmod(i, 2)
            grid.addWidget(grp, row, col)
            
        layout.addLayout(grid)
        layout.addSpacing(20)

        # Bottom section: Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_help = QPushButton("Help")
        self.btn_help.setIcon(feather_icon("help-circle", self._icon_color, 14))
        self.btn_help.clicked.connect(self._show_help)
        btn_layout.addWidget(self.btn_help)
        
        self.btn_run = QPushButton("Generate Dashboard")
        self.btn_run.setObjectName("primaryButton")
        self.btn_run.setIcon(feather_icon("play", "#FFFFFF", 14))
        self.btn_run.setMinimumWidth(150)
        self.btn_run.clicked.connect(self._on_run)
        btn_layout.addWidget(self.btn_run)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def update_columns(self, columns: Iterable[str]) -> None:
        """Update the comboboxes with the available dataset columns."""
        cols = [str(c) for c in columns]
        for cfg in self.plot_configs:
            for cb in (cfg["x"], cfg["y"], cfg["hue"]):
                cb.clear()
                cb.addItem("-- None --")
                cb.addItems(cols)

    def refresh_theme(self, theme) -> None:
        """Update icon colors on theme change."""
        from quantia.theme.palette import PALETTE
        self._icon_color = PALETTE[theme]["text_primary"]
        self.btn_help.setIcon(feather_icon("help-circle", self._icon_color, 14))
        # primaryButton always keeps white icon
        self.btn_run.setIcon(feather_icon("play", "#FFFFFF", 14))

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Dashboard Builder",
            "The Dashboard Builder creates an HTML report with up to 4 plots arranged in a grid.\n\n"
            "1. Enable the panels you want to include.\n"
            "2. Select the plot type and variables for each panel.\n"
            "3. Click Generate Dashboard.\n\n"
            "The generated Python script will build a static HTML dashboard displaying all selected plots in the Results view."
        )

    def _on_run(self) -> None:
        code = self.generate_code()
        if code:
            self.code_generated.emit(code)

    def generate_code(self) -> str:
        style_name = self.cmb_style.currentText()
        style_code = generate_style_code(style_name)
        title = self.txt_title.text().replace("'", "\\'")
        
        active_plots = []
        for i, cfg in enumerate(self.plot_configs):
            if cfg["group"].isChecked():
                x = cfg["x"].currentText()
                y = cfg["y"].currentText()
                hue = cfg["hue"].currentText()
                ptype = cfg["type"].currentText()
                
                x = None if x == "-- None --" else x
                y = None if y == "-- None --" else y
                hue = None if hue == "-- None --" else hue
                
                active_plots.append({
                    "id": i+1,
                    "type": ptype,
                    "x": x,
                    "y": y,
                    "hue": hue
                })
                
        if not active_plots:
            QMessageBox.warning(self, "No Plots", "Please enable at least one panel.")
            return ""

        code = [
            f"# Generate Dashboard: {title}",
            "import base64",
            "from io import BytesIO",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "",
            style_code,
            "",
            "def fig_to_base64(fig):",
            "    buf = BytesIO()",
            "    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)",
            "    buf.seek(0)",
            "    return base64.b64encode(buf.read()).decode('utf-8')",
            "",
            "html_output = []",
            f"html_output.append('<h2>{title}</h2>')",
            "html_output.append('<div style=\"display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px;\">')",
            ""
        ]
        
        for p in active_plots:
            code.append(f"try:")
            code.append(f"    fig, ax = plt.subplots(figsize=(6, 4))")
            
            x_arg = f"x='{p['x']}'" if p['x'] else ""
            y_arg = f"y='{p['y']}'" if p['y'] else ""
            hue_arg = f"hue='{p['hue']}'" if p['hue'] else ""
            
            args = ", ".join(filter(None, ["data=df", x_arg, y_arg, hue_arg, "ax=ax"]))
            
            if p['type'] == "Scatter":
                code.append(f"    sns.scatterplot({args})")
            elif p['type'] == "Bar":
                code.append(f"    sns.barplot({args})")
            elif p['type'] == "Line":
                code.append(f"    sns.lineplot({args})")
            elif p['type'] == "Histogram":
                # Histogram uses 'x' or 'y' but usually not both
                h_args = ", ".join(filter(None, ["data=df", x_arg or y_arg, hue_arg, "kde=True", "ax=ax"]))
                code.append(f"    sns.histplot({h_args})")
            elif p['type'] == "Box Plot":
                code.append(f"    sns.boxplot({args})")
            elif p['type'] == "Violin":
                code.append(f"    sns.violinplot({args})")
                
            plot_title = f"{p['type']} Panel {p['id']}"
            code.append(f"    ax.set_title('{plot_title}')")
            code.append(f"    fig.tight_layout()")
            code.append(f"    b64_img = fig_to_base64(fig)")
            code.append(f"    html_output.append(f'<div><img src=\"data:image/png;base64,{{b64_img}}\" style=\"max-width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);\" /></div>')")
            code.append(f"    plt.close(fig)")
            code.append(f"except Exception as e:")
            code.append(f"    html_output.append(f'<div style=\"padding: 20px; border: 1px solid red; color: red;\">Error in Panel {p['id']}: {{e}}</div>')")
            code.append("")
            
        code.append("html_output.append('</div>')")
        code.append("")
        code.append("if 'display_html' in globals():")
        code.append("    display_html('\\n'.join(html_output))")
        code.append("elif 'show_result' in globals():")
        code.append(f"    show_result('{title}', '\\n'.join(html_output))")
        code.append("else:")
        code.append("    print('Dashboard generated successfully.')")
        
        return "\n".join(code)
