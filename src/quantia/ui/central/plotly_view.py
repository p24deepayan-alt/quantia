"""Interactive Plotly popup dialog.

Renders Plotly HTML inside a QWebEngineView (or QTextBrowser fallback)
for full interactive exploration: zoom, pan, hover, and export.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import QUrl


def _webengine_available() -> bool:
    """Check if PySide6-WebEngine is installed."""
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
        return True
    except ImportError:
        return False


class InteractivePlotlyDialog(QDialog):
    """A popup dialog containing an interactive Plotly figure."""

    def __init__(self, html: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Interactive Plot (Plotly)")
        self.resize(900, 700)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if _webengine_available():
            from PySide6.QtWebEngineWidgets import QWebEngineView
            self._view = QWebEngineView()
            self._view.setHtml(html)
            layout.addWidget(self._view)
        else:
            # Graceful fallback: show a message
            lbl = QLabel(
                "PySide6-WebEngine is required for interactive Plotly plots.\n"
                "Install with: pip install PySide6-WebEngine"
            )
            lbl.setWordWrap(True)
            lbl.setStyleSheet("padding: 24px; font-size: 12pt; color: #EF4444;")
            layout.addWidget(lbl)
