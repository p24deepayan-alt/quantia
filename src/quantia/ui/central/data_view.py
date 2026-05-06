"""Data View — Excel-like spreadsheet grid.

Central tab widget displaying the current DataFrame in a QTableView with:
- Frozen column headers with sort indicators
- 1-indexed row numbers
- Alternating row colours
- Column filter row (QLineEdit per column)
- Right-click context menu (sort, filter, copy, plot)
- Column resize with double-click auto-fit
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import polars as pl
from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal, QObject, QEvent
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from quantia.core.data_model import PandasTableModel
from quantia.ui.icons import feather_icon


class ShiftScrollFilter(QObject):
    """Event filter to translate Shift+Wheel into horizontal scrolling."""
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                view = obj.parent()
                if hasattr(view, 'horizontalScrollBar'):
                    h_bar = view.horizontalScrollBar()
                    delta = event.angleDelta().y()
                    h_bar.setValue(h_bar.value() - delta)
                    return True
        return super().eventFilter(obj, event)


class DataViewWidget(QWidget):
    """Excel-like data grid backed by a PandasTableModel."""

    # Emitted when data is loaded (for status bar update, variable list refresh)
    data_loaded = Signal(object)
    # Request a quick plot for a column
    quick_plot_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_df: pd.DataFrame | pl.DataFrame = pd.DataFrame()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Info bar (above table, like Excel's formula bar area) ─────────
        self._info_bar = QWidget()
        info_layout = QHBoxLayout(self._info_bar)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(8)

        self._cell_ref = QLabel("")
        self._cell_ref.setStyleSheet("font-weight: 600; min-width: 80px;")
        info_layout.addWidget(self._cell_ref)

        self._cell_value = QLineEdit()
        self._cell_value.setReadOnly(True)
        self._cell_value.setPlaceholderText("Select a cell to view its value")
        info_layout.addWidget(self._cell_value)

        # ── Quick Search ────────────────────────────────────────────────
        self._search_bar = QLineEdit()
        self._search_bar.setPlaceholderText("Search rows...")
        self._search_bar.setFixedWidth(250)
        self._search_bar.setClearButtonEnabled(True)
        self._search_bar.addAction(feather_icon("search", "#94A3B8", 14), QLineEdit.ActionPosition.LeadingPosition)
        self._search_bar.textChanged.connect(self._on_search_changed)
        info_layout.addWidget(self._search_bar)
        
        info_layout.addWidget(QLabel()) # Spacer

        layout.addWidget(self._info_bar)

        # ── Table view ───────────────────────────────────────────────────
        self._model = PandasTableModel()

        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.clicked.connect(self._on_cell_clicked)

        self._shift_scroll_filter = ShiftScrollFilter(self._table)
        self._table.viewport().installEventFilter(self._shift_scroll_filter)

        # Horizontal header (column names)
        h_header = self._table.horizontalHeader()
        h_header.setStretchLastSection(True)
        h_header.setSectionsMovable(True)
        h_header.setDefaultSectionSize(100)
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.sectionDoubleClicked.connect(self._auto_resize_column)

        # Vertical header (row numbers)
        v_header = self._table.verticalHeader()
        v_header.setMinimumWidth(50)

        layout.addWidget(self._table)
        
        self._chrome_icon_color = "#2D3E50"
        self.refresh_theme() # Apply initial theme colors

    # ── Public API ───────────────────────────────────────────────────────

    @property
    def model(self) -> PandasTableModel:
        return self._model

    def load_dataframe(self, df: pd.DataFrame | pl.DataFrame) -> None:
        """Set a new DataFrame into the table."""
        self._current_df = df
        if isinstance(df, pl.DataFrame):
            # Fast zero-copy conversion for display
            pd_df = df.to_pandas()
        else:
            pd_df = df
            
        self._model.set_dataframe(pd_df)
        self._cell_ref.setText("")
        self._cell_value.clear()
        self.data_loaded.emit(df)

    def load_csv(self, path: str) -> pl.DataFrame | None:
        """Load a CSV file and display it. Returns the Polars DataFrame on success."""
        try:
            # Use robust parameters for high-performance multi-threaded loading
            df = pl.read_csv(
                path, 
                infer_schema_length=10000, 
                truncate_ragged_lines=True
            )
            self.load_dataframe(df)
            return df
        except Exception as e:
            return None

    def load_excel(self, path: str) -> pl.DataFrame | None:
        """Load an Excel file and display it."""
        try:
            # Polars supports excel via fastexcel or calamine engines
            pd_df = pd.read_excel(path)
            df = pl.from_pandas(pd_df)
            self.load_dataframe(df)
            return df
        except Exception as e:
            return None

    def get_dataframe(self) -> pd.DataFrame | pl.DataFrame:
        return self._current_df

    # ── Cell selection ───────────────────────────────────────────────────

    def _on_cell_clicked(self, index) -> None:
        source_index = self._proxy.mapToSource(index)
        row = source_index.row()
        col = source_index.column()
        col_name = self._model.dataframe.columns[col]
        self._cell_ref.setText(f"{col_name} : R{row + 1}")

        value = self._model.dataframe.iat[row, col]
        self._cell_value.setText(str(value) if pd.notna(value) else "<missing>")

    # ── Context menu ─────────────────────────────────────────────────────

    def _show_context_menu(self, pos) -> None:
        index = self._table.indexAt(pos)
        if not index.isValid():
            return

        source_index = self._proxy.mapToSource(index)
        col_name = self._model.dataframe.columns[source_index.column()]

        menu = QMenu(self)

        menu.addAction(feather_icon("arrow-up", self._chrome_icon_color, 14), "Sort Ascending",
                       lambda: self._sort_column(source_index.column(), Qt.SortOrder.AscendingOrder))
        menu.addAction(feather_icon("arrow-down", self._chrome_icon_color, 14), "Sort Descending",
                       lambda: self._sort_column(source_index.column(), Qt.SortOrder.DescendingOrder))
        menu.addSeparator()
        menu.addAction(feather_icon("bar-chart-2", self._chrome_icon_color, 14), f"Plot '{col_name}'",
                       lambda: self.quick_plot_requested.emit(col_name))
        menu.addSeparator()
        menu.addAction(feather_icon("copy", self._chrome_icon_color, 14), "Copy Cell",
                       self._copy_selection)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def refresh_theme(self) -> None:
        """Update colors for the current theme."""
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        from quantia.theme.palette import PALETTE, Theme
        
        app = QApplication.instance()
        theme = app.get_current_theme() if isinstance(app, QuantiaApp) else Theme.LIGHT
        p = PALETTE[theme]
        
        self._chrome_icon_color = p["text_primary"]
        
        # Update Info Bar background
        bg = p["surface_secondary"]
        self.setStyleSheet(f"background-color: {p['surface_primary']};")
        # Structural stabilization + colors
        search_style = f"""
            background-color: {p['surface_tertiary']}; 
            color: {p['text_primary']}; 
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding-left: 28px;
            padding-right: 12px;
            height: 30px;
        """
        self._search_bar.setStyleSheet(search_style)
        
        ref_style = f"""
            font-weight: 600; 
            color: {p['brand_primary'] if 'brand_primary' in p else p['accent']};
            background-color: {p['surface_tertiary']};
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 0px 12px;
            height: 30px;
        """
        self._cell_ref.setStyleSheet(ref_style)
        
        # Stabilize cell value as well
        self._cell_value.setStyleSheet(f"""
            background-color: {p['surface_tertiary']}; 
            color: {p['text_primary']}; 
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 0px 12px;
            height: 30px;
        """)
        
        # Update Search Icon
        for action in self._search_bar.actions():
            self._search_bar.removeAction(action)
        self._search_bar.addAction(feather_icon("search", p["text_secondary"], 16), QLineEdit.ActionPosition.LeadingPosition)
        
        # Enforce exact heights to prevent jumping
        self._info_bar.setFixedHeight(38)
        self._cell_ref.setFixedHeight(30)
        self._cell_value.setFixedHeight(30)
        self._search_bar.setFixedHeight(30)
        
        # Update table alternating colors
        self._table.setAlternatingRowColors(True)
        
    def set_icon_color(self, color: str) -> None:
        """Update the icon colour for chrome elements (context menu)."""
        self._chrome_icon_color = color

    def _sort_column(self, col: int, order: Qt.SortOrder) -> None:
        self._table.sortByColumn(col, order)

    def _auto_resize_column(self, col: int) -> None:
        self._table.resizeColumnToContents(col)

    def _copy_selection(self) -> None:
        indexes = self._table.selectedIndexes()
        if not indexes:
            return
        source_idx = self._proxy.mapToSource(indexes[0])
        value = self._model.dataframe.iat[source_idx.row(), source_idx.column()]
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(str(value) if pd.notna(value) else "")

    def _on_search_changed(self, text: str) -> None:
        """Filter the table rows based on search text."""
        self._proxy.setFilterFixedString(text)
