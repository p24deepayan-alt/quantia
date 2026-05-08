"""Interactive Plot popup dialog with matplotlib NavigationToolbar2QT."""

from __future__ import annotations

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtGui import QIcon

class InteractivePlotDialog(QDialog):
    """A popup dialog containing an interactive matplotlib figure."""

    def __init__(self, fig: Figure, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Interactive Plot")
        self.resize(800, 600)
        self.setModal(False) # Non-modal so user can look at multiple plots

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create canvas and toolbar
        self.canvas = FigureCanvasQTAgg(fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
