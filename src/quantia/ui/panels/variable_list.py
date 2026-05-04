"""Variable List panel — VBA Project Explorer style.

Dockable left panel showing all variables in the current dataset with
type icons, missing-data badges, and right-click context menus.
Supports drag-and-drop into analysis dialogs.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag, QColor
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quantia.ui.icons import feather_icon


# Variable type → icon mapping (Feather icon names)
_TYPE_ICONS = {
    "numeric": ("hash", "#2C3E8F"),       # Deep Indigo
    "categorical": ("tag", "#009688"),     # Teal
    "datetime": ("calendar", "#FFC107"),   # Amber
    "binary": ("toggle-right", "#E91E63"), # Pink/Rose
}

# Missing % → badge colour
def _missing_color(pct: float) -> QColor:
    if pct == 0:
        return QColor("#26A69A")  # Seafoam Green — no missing
    if pct < 5:
        return QColor("#FFC107")  # Amber — low missing
    return QColor("#EF5350")      # Coral Red — high missing


class VariableListPanel(QDockWidget):
    """Dockable panel listing dataset variables with type info."""

    # Emitted when user double-clicks a variable
    variable_selected = Signal(str)
    # Emitted when user requests a quick histogram
    quick_plot_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Variables", parent)
        self.setObjectName("VariableListDock")
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(200)
        
        self._chrome_icon_color = "#000000"

        # Container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search / filter bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter variables…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._filter_variables)
        layout.addWidget(self._search)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Variable", "Type", "Missing"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.setDragEnabled(True)
        self._tree.setColumnWidth(0, 120)
        self._tree.setColumnWidth(1, 70)
        self._tree.setColumnWidth(2, 60)
        layout.addWidget(self._tree)

        # Summary label
        self._summary = QLabel("No data loaded")
        self._summary.setStyleSheet("padding: 4px 8px; font-size: 11px; color: #6B7280;")
        layout.addWidget(self._summary)

        self.setWidget(container)

    def set_variables(self, columns_info: list[dict[str, Any]]) -> None:
        """Populate the tree from column_info() output of PandasTableModel."""
        self._tree.clear()

        for info in columns_info:
            name = info["name"]
            var_type = info["var_type"]
            pct_missing = info["pct_missing"]

            item = QTreeWidgetItem()
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, info)

            # Type icon
            icon_name, icon_color = _TYPE_ICONS.get(var_type, ("help-circle", "#6B7280"))
            item.setIcon(0, feather_icon(icon_name, icon_color, 14))

            # Type label
            item.setText(1, var_type[:3].upper())

            # Missing percentage
            if pct_missing > 0:
                item.setText(2, f"{pct_missing:.1f}%")
            else:
                item.setText(2, "—")

            # Colour the missing column
            color = _missing_color(pct_missing)
            item.setForeground(2, color)

            self._tree.addTopLevelItem(item)

        self._summary.setText(f"{len(columns_info)} variables")

    def refresh_theme(self, theme: Any) -> None:
        """Update colors and stabilize layout for the current theme."""
        from quantia.theme.palette import PALETTE
        p = PALETTE[theme]
        
        self._chrome_icon_color = p["text_primary"]
        
        # Stabilize search bar
        self._search.setStyleSheet(f"""
            background-color: {p['surface_primary']};
            color: {p['text_primary']};
            border: 1px solid {p['border']};
            border-bottom: none;
            padding: 4px 10px;
        """)
        self._search.setFixedHeight(34)
        
        # Update summary label
        self._summary.setStyleSheet(f"padding: 4px 8px; font-size: 11px; color: {p['text_secondary']}; border-top: 1px solid {p['border']};")
        self._summary.setFixedHeight(24)
        
        # Stabilize tree headers
        self._tree.header().setFixedHeight(30)

    def refresh_icons(self, color: str) -> None:
        """Deprecated: Use refresh_theme instead."""
        self._chrome_icon_color = color

    def clear_variables(self) -> None:
        self._tree.clear()
        self._summary.setText("No data loaded")

    # ── Filtering ────────────────────────────────────────────────────────

    def _filter_variables(self, text: str) -> None:
        text_lower = text.lower()
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item is not None:
                item.setHidden(text_lower not in item.text(0).lower())

    # ── Context menu ─────────────────────────────────────────────────────

    def _show_context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if item is None:
            return

        var_name = item.text(0)
        menu = QMenu(self)
        menu.addAction(feather_icon("bar-chart-2", self._chrome_icon_color, 14), "Quick Histogram",
                       lambda: self.quick_plot_requested.emit(var_name))
        menu.addAction(feather_icon("info", self._chrome_icon_color, 14), "Describe",
                       lambda: self.variable_selected.emit(var_name))
        menu.addSeparator()
        menu.addAction("Copy Variable Name",
                       lambda: self._copy_name(var_name))
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _on_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        self.variable_selected.emit(item.text(0))

    @staticmethod
    def _copy_name(name: str) -> None:
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(name)
