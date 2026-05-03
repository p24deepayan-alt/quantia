"""Concatenate Columns Dialog.

Joins two or more columns together with a specific separator.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class ConcatColsDialog(BaseAnalysisDialog):
    """Dialog for concatenating columns."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Concatenate Columns", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Columns to Combine (Top to Bottom):", self.list_targets, multi_select=True)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Separator
        group_sep = QGroupBox("Separator")
        l_sep = QVBoxLayout(group_sep)
        self.txt_sep = QLineEdit()
        self.txt_sep.setPlaceholderText("e.g. , or - or leave blank")
        l_sep.addWidget(self.txt_sep)
        layout.addWidget(group_sep)

        # Output
        group_out = QGroupBox("Output")
        l_out = QVBoxLayout(group_out)
        l_out.addWidget(QLabel("New Column Name:"))
        self.txt_new_col = QLineEdit()
        self.txt_new_col.setText("Concatenated")
        l_out.addWidget(self.txt_new_col)
        layout.addWidget(group_out)

    def generate_code(self) -> str:
        targets = [self.list_targets.item(i).text() for i in range(self.list_targets.count())]
        
        if len(targets) < 2:
            QMessageBox.warning(self, "Missing Input", "Please select at least TWO columns to concatenate.")
            return ""

        sep_str = self.txt_sep.text()
        
        new_col = self.txt_new_col.text().strip()
        if not new_col:
            QMessageBox.warning(self, "Missing Input", "Please provide a new column name.")
            return ""

        code = [
            f"# Concatenate Columns",
        ]
        
        # Escape quotes
        s_esc = sep_str.replace("'", "\\'")
        
        # Build the pandas string concatenation code
        parts = [f"df['{c}'].astype(str)" for c in targets]
        joiner = f" + '{s_esc}' + "
        
        concat_expr = joiner.join(parts)
        
        code.append(f"df['{new_col}'] = {concat_expr}")
            
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Concatenate Columns",
            "Combines multiple columns into a single new text column.\n\n"
            "The columns are joined in the exact order they appear in the list. Non-string columns are automatically converted to text."
        )
