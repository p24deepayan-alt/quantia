"""Quantia Application — QApplication subclass with theme management."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication

from quantia.theme.palette import Theme, get_stylesheet


class QuantiaApp(QApplication):
    """Customised QApplication with font loading and Fusion base style."""

    def __init__(self, argv: list[str] | None = None) -> None:
        super().__init__(argv or sys.argv)
        self._current_theme = Theme.LIGHT
        
        # ── Global Error Handling ────────────────────────────────────────
        sys.excepthook = self._global_error_handler

    def _global_error_handler(self, exctype, value, traceback_obj) -> None:
        """Catch-all for any unhandled exceptions in the GUI thread."""
        import traceback
        from PySide6.QtWidgets import QMessageBox
        
        err_msg = "".join(traceback.format_exception(exctype, value, traceback_obj))
        print(f"CRITICAL ERROR:\n{err_msg}")
        
        # Display a user-friendly crash dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Quantia — Unexpected Error")
        msg.setText("An unexpected error occurred.")
        msg.setInformativeText("The application encountered a problem and may need to restart.")
        msg.setDetailedText(err_msg)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

        # ── Base style ───────────────────────────────────────────────────
        self.setStyle("Fusion")

        # ── Application metadata ─────────────────────────────────────────
        self.setApplicationName("Quantia")
        self.setApplicationVersion("0.1.1")
        self.setOrganizationName("Quantia")

        # ── Load fonts ───────────────────────────────────────────────────
        self._load_system_fonts()

        # ── Set default font ─────────────────────────────────────────────
        font = QFont("Inter", 10)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        self.setFont(font)

    def _load_system_fonts(self) -> None:
        """Try to load Inter and Fira Code if available on the system."""
        # Qt will fall back through the font family list in the QSS
        # (Inter → Segoe UI Variable → Segoe UI → sans-serif)
        # No need to bundle fonts for Phase 1 — system fonts suffice.
        pass

    def apply_theme(self, theme: Theme) -> None:
        """Apply a QSS theme and update global state."""
        self._current_theme = theme
        qss = get_stylesheet(theme)
        if qss:
            self.setStyleSheet(qss)
        
    def toggle_theme(self) -> Theme:
        """Switch between Light and Dark themes and return the new theme."""
        new_theme = Theme.DARK if self._current_theme == Theme.LIGHT else Theme.LIGHT
        self.apply_theme(new_theme)
        return new_theme

    def get_current_theme(self) -> Theme:
        """Return the currently active theme."""
        return self._current_theme
