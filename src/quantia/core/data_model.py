"""PandasTableModel — bridges a pandas DataFrame to QTableView.

Provides an Excel-like data grid experience: column types, sorting,
formatting, and missing-value highlighting.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PandasTableModel(QAbstractTableModel):
    """
    Table model backed by a pandas DataFrame.
    Implements virtual-windowing for high-performance scrolling.
    """

    def __init__(self, df: pd.DataFrame | None = None, parent: Any = None) -> None:
        super().__init__(parent)
        self._df: pd.DataFrame = df if df is not None else pd.DataFrame()
        # Constants for virtual display
        self._page_size = 1000 

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Replace the entire DataFrame and refresh the view."""
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    # ── Required overrides ───────────────────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row, col = index.row(), index.column()
        
        # Virtual check: Ensure row is within bounds
        if row >= len(self._df) or col >= len(self._df.columns):
            return None

        # Optimization: use iat for single cell access
        value = self._df.iat[row, col]

        if role == Qt.ItemDataRole.DisplayRole:
            if pd.isna(value):
                return ""
            if isinstance(value, (float, np.float64, np.float32)):
                return f"{value:.6g}"
            return str(value)

        if role == Qt.ItemDataRole.ToolTipRole:
            if pd.isna(value):
                return "Missing value"
            return str(value)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            dtype = self._df.dtypes.iloc[col]
            if pd.api.types.is_numeric_dtype(dtype):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        if role == Qt.ItemDataRole.BackgroundRole:
            if pd.isna(value):
                # Light red tint for missing values
                from PySide6.QtGui import QColor
                return QColor(239, 83, 80, 30)  # Coral Red at 12% opacity

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            return str(section + 1)


        if role == Qt.ItemDataRole.ToolTipRole and orientation == Qt.Orientation.Horizontal:
            col_name = self._df.columns[section]
            dtype = self._df.dtypes.iloc[section]
            n_missing = int(self._df[col_name].isna().sum())
            pct_missing = n_missing / len(self._df) * 100 if len(self._df) > 0 else 0
            return f"{col_name}\nType: {dtype}\nMissing: {n_missing} ({pct_missing:.1f}%)"

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    # ── Sorting ──────────────────────────────────────────────────────────

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.beginResetModel()
        col_name = self._df.columns[column]
        ascending = order == Qt.SortOrder.AscendingOrder
        self._df = self._df.sort_values(by=col_name, ascending=ascending, na_position="last")
        self._df = self._df.reset_index(drop=True)
        self.endResetModel()

    # ── Helpers ──────────────────────────────────────────────────────────

    def column_info(self) -> list[dict[str, Any]]:
        """Return metadata for each column (for the variable list panel)."""
        info = []
        for col in self._df.columns:
            dtype = self._df[col].dtype
            n_missing = int(self._df[col].isna().sum())
            n_total = len(self._df)
            pct_missing = n_missing / n_total * 100 if n_total > 0 else 0.0

            unique_vals = self._df[col].dropna().unique()
            
            is_binary = False
            if pd.api.types.is_bool_dtype(dtype):
                is_binary = True
            elif len(unique_vals) == 2:
                val_set = set(unique_vals)
                if val_set == {0, 1} or val_set == {True, False}:
                    is_binary = True
                else:
                    try:
                        str_set = {str(v).lower().strip() for v in val_set}
                        if str_set == {"yes", "no"}:
                            is_binary = True
                    except:
                        pass
            
            if is_binary:
                var_type = "binary"
            elif pd.api.types.is_numeric_dtype(dtype):
                var_type = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                var_type = "datetime"
            else:
                var_type = "categorical"

            info.append({
                "name": col,
                "dtype": str(dtype),
                "var_type": var_type,
                "n_missing": n_missing,
                "pct_missing": pct_missing,
            })
        return info
