"""Console panel — VBA Immediate Window style.

Dockable bottom panel showing script output with coloured messages:
- Normal output: default text colour
- Errors: coral red
- Warnings: amber
- Assumption check results: seafoam green
- Commands: teal accent
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor, QFont
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from quantia.ui.icons import feather_icon


class _MessageType:
    NORMAL = "normal"
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"
    COMMAND = "command"
    INFO = "info"


# Colour mapping (works in both themes — dark theme overrides via QSS if needed)
_COLORS = {
    _MessageType.NORMAL: None,          # Use default text colour
    _MessageType.ERROR: "#EF5350",      # Coral Red
    _MessageType.WARNING: "#FFC107",    # Amber
    _MessageType.SUCCESS: "#26A69A",    # Seafoam Green
    _MessageType.COMMAND: "#009688",    # Teal Accent
    _MessageType.INFO: "#5B6BC0",       # Lighter Indigo
}


class ConsolePanel(QDockWidget):
    """Dockable output console inspired by VBA's Immediate Window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Console", parent)
        self.setObjectName("ConsoleDock")
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Button bar ───────────────────────────────────────────────────
        btn_bar = QWidget()
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(4, 2, 4, 2)
        btn_layout.setSpacing(4)

        clear_btn = QPushButton()
        clear_btn.setIcon(feather_icon("trash-2", "#6B7280", 14))
        clear_btn.setToolTip("Clear Console")
        clear_btn.setFixedSize(24, 24)
        clear_btn.setFlat(True)
        clear_btn.clicked.connect(self.clear)
        btn_layout.addWidget(clear_btn)

        copy_btn = QPushButton()
        copy_btn.setIcon(feather_icon("copy", "#6B7280", 14))
        copy_btn.setToolTip("Copy All")
        copy_btn.setFixedSize(24, 24)
        copy_btn.setFlat(True)
        copy_btn.clicked.connect(self._copy_all)
        btn_layout.addWidget(copy_btn)

        btn_layout.addStretch()
        layout.addWidget(btn_bar)

        # ── Text area ────────────────────────────────────────────────────
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Fira Code", 12))
        self._output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._output)
        self.setWidget(container)

    def refresh_theme(self, theme: Any) -> None:
        """Update colors and icons for the current theme."""
        from quantia.theme.palette import Theme, PALETTE
        p = PALETTE[theme]
        
        # Update text editor
        self._output.setStyleSheet(f"background-color: {p['surface_primary']}; color: {p['text_primary']}; border: none;")
        
        # Update button bar icons
        ic = p["text_secondary"]
        # I'll need to find the buttons. Actually, I can just re-set them if I had references.
        # But for now, let's just use the children.
        for btn in self.findChildren(QPushButton):
            if "Clear" in (btn.toolTip() or ""):
                btn.setIcon(feather_icon("trash-2", ic, 14))
            elif "Copy" in (btn.toolTip() or ""):
                btn.setIcon(feather_icon("copy", ic, 14))

        # Welcome message
        self.write_info("Quantia Console — Ready")

    # ── Public API ───────────────────────────────────────────────────────

    def write(self, text: str) -> None:
        """Write normal output."""
        self._append(text, _MessageType.NORMAL)

    def write_error(self, text: str) -> None:
        """Write error message in coral red."""
        self._append(f"ERROR: {text}", _MessageType.ERROR)

    def write_warning(self, text: str) -> None:
        """Write warning message in amber."""
        self._append(f"WARNING: {text}", _MessageType.WARNING)

    def write_success(self, text: str) -> None:
        """Write success / assumption-check result in seafoam green."""
        self._append(f"✓ {text}", _MessageType.SUCCESS)

    def write_command(self, text: str) -> None:
        """Write executed command echo in teal."""
        self._append(f">>> {text}", _MessageType.COMMAND)

    def write_info(self, text: str) -> None:
        """Write informational message."""
        self._append(text, _MessageType.INFO)

    def clear(self) -> None:
        """Clear all console output."""
        self._output.clear()

    # ── Internal ─────────────────────────────────────────────────────────

    def _append(self, text: str, msg_type: str) -> None:
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        color = _COLORS.get(msg_type)
        if color:
            fmt.setForeground(QColor(color))

        cursor.insertText(text + "\n", fmt)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def _copy_all(self) -> None:
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._output.toPlainText())
