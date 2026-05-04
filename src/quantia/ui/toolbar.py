"""Toolbar for the Quantia main window.

Icon toolbar inspired by Excel's Quick Access Toolbar / ribbon bar:
New, Open, Save, Undo, Redo | Import, Export | Run Script | Generate Code | Preferences
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QToolBar, QWidget, QSizePolicy

from quantia.ui.icons import feather_icon


class QuantiaToolbar(QToolBar):
    """Main application toolbar with Feather icons."""

    # Signals emitted when toolbar buttons are clicked
    open_project = Signal()
    save_project = Signal()
    
    undo_action = Signal()
    redo_action = Signal()
    import_data = Signal()
    run_script = Signal()
    toggle_theme = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)
        self.setIconSize(self.iconSize())  # Use default

        icon_color = "#2D3E50"

        # ── File operations ──────────────────────────────────────────────
        self._add_action("folder", icon_color, "Open Project", "Open Project (Ctrl+O)", self.open_project)
        self._add_action("save", icon_color, "Save Project", "Save Project (Ctrl+S)", self.save_project)

        self.addSeparator()

        # ── Undo / Redo ──────────────────────────────────────────────────
        self._add_action("rotate-ccw", icon_color, "Undo", "Undo (Ctrl+Z)", self.undo_action)
        self._add_action("rotate-cw", icon_color, "Redo", "Redo (Ctrl+Y)", self.redo_action)

        self.addSeparator()

        # ── Data operations ──────────────────────────────────────────────
        self._add_action("download", icon_color, "Import Data", "Import Data", self.import_data)

        self.addSeparator()

        # ── Script operations ────────────────────────────────────────────
        self._add_action("play", "#26A69A", "Run Script", "Run Script (F5)", self.run_script)

        # Toolbar ends here (removed theme toggle)

    def refresh_icons(self, color: str) -> None:
        """Update all toolbar icons to a new colour."""
        for action in self.actions():
            name = action.property("icon_name")
            if not name:
                continue
            
            if name == "play":
                icon_color = "#26A69A"
            else:
                icon_color = color
                
            action.setIcon(feather_icon(name, icon_color))

    def _add_action(self, icon_name: str, color: str, text: str, tip: str, signal: Signal) -> None:
        """Helper to add a toolbar action and store its icon name."""
        act = self.addAction(feather_icon(icon_name, color), text)
        act.setToolTip(tip)
        act.setProperty("icon_name", icon_name)
        act.triggered.connect(signal.emit)
