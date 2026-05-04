"""Plot View widget.

Provides a tabbed interface for viewing matplotlib figures embedded
via FigureCanvasQTAgg. Each plot opens in a new closable tab.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from quantia.ui.icons import feather_icon


class PlotViewWidget(QWidget):
    """Container for matplotlib plots. Each figure opens in a new tab."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("plotView")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        h_layout = QHBoxLayout(toolbar)
        h_layout.setContentsMargins(8, 4, 8, 4)

        self._btn_save = QPushButton("Save Plot")
        self._btn_save.setIcon(feather_icon("download", "#2D3E50", 14))
        self._btn_save.clicked.connect(self._save_current)

        self._btn_clear = QPushButton("Clear All Plots")
        self._btn_clear.setIcon(feather_icon("trash-2", "#D32F2F", 14))
        self._btn_clear.clicked.connect(self.clear_all)

        h_layout.addStretch()
        h_layout.addWidget(self._btn_save)
        h_layout.addWidget(self._btn_clear)
        
        self._chrome_icon_color = "#2D3E50"
        layout.addWidget(toolbar)

        # Tabs container
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        layout.addWidget(self._tabs)

    def add_plot(self, title: str, fig: Figure) -> None:
        """Embed a matplotlib Figure in a new tab."""
        canvas = FigureCanvasQTAgg(fig)
        canvas.draw()
        idx = self._tabs.addTab(canvas, feather_icon("image", self._chrome_icon_color, 14), title)
        self._tabs.setCurrentIndex(idx)

    def set_icon_color(self, color: str) -> None:
        """Update the icon colour for toolbar and existing tabs."""
        self._chrome_icon_color = color
        self._btn_save.setIcon(feather_icon("download", color, 14))
        # btn_clear uses red
        
        # Update existing tabs
        for i in range(self._tabs.count()):
            self._tabs.setTabIcon(i, feather_icon("image", color, 14))

    def _save_current(self) -> None:
        """Save the currently visible plot to a file."""
        widget = self._tabs.currentWidget()
        if not isinstance(widget, FigureCanvasQTAgg):
            return

from quantia.utils.paths import get_plots_dir

# ... later in the file ...

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            str(get_plots_dir()),
            "PNG Image (*.png);;SVG Vector (*.svg);;PDF Document (*.pdf);;All Files (*)",
        )
        if path:
            widget.figure.savefig(path, dpi=150, bbox_inches="tight")

    def _close_tab(self, index: int) -> None:
        self._tabs.removeTab(index)

    def clear_all(self) -> None:
        self._tabs.clear()
