"""String Format Dialog.

Handles changing case (Upper, Lower, Title) and trimming whitespace.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class StringFormatDialog(BaseAnalysisDialog):
    """Dialog for formatting string columns (Case, Trim)."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Change Case & Trim", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Columns to Format (String):", self.list_targets, multi_select=True)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Operation
        group_op = QGroupBox("Operation")
        l_op = QVBoxLayout(group_op)
        
        self.cmb_operation = QComboBox()
        self.cmb_operation.addItems([
            "UPPERCASE", 
            "lowercase", 
            "Title Case", 
            "Capitalize First Letter",
            "Trim Whitespace (Leading & Trailing)"
        ])
        l_op.addWidget(self.cmb_operation)
        layout.addWidget(group_op)

        # Output Destination
        group_dest = QGroupBox("Output Destination")
        l_dest = QVBoxLayout(group_dest)
        
        self.rad_overwrite = QRadioButton("Overwrite existing columns")
        self.rad_overwrite.setChecked(True)
        l_dest.addWidget(self.rad_overwrite)

        self.rad_new_col = QRadioButton("Create new columns (e.g., 'Formatted_VarName')")
        l_dest.addWidget(self.rad_new_col)
        
        layout.addWidget(group_dest)

    def generate_code(self) -> str:
        targets = [self.list_targets.item(i).text() for i in range(self.list_targets.count())]
        if not targets:
            QMessageBox.warning(self, "Missing Input", "Please select at least one column to format.")
            return ""

        operation = self.cmb_operation.currentText()
        new_cols = self.rad_new_col.isChecked()

        vars_str = ", ".join(f"'{v}'" for v in targets)
        code = [
            f"# String Format: {operation}",
            f"target_cols = [{vars_str}]",
            "for col in target_cols:"
        ]

        # Determine target column name
        if new_cols:
            code.append("    new_col = f'Formatted_' + col")
        else:
            code.append("    new_col = col")

        # Apply transformation
        if operation == "UPPERCASE":
            code.append("    df[new_col] = df[col].astype(str).str.upper()")
        elif operation == "lowercase":
            code.append("    df[new_col] = df[col].astype(str).str.lower()")
        elif operation == "Title Case":
            code.append("    df[new_col] = df[col].astype(str).str.title()")
        elif operation == "Capitalize First Letter":
            code.append("    df[new_col] = df[col].astype(str).str.capitalize()")
        elif operation == "Trim Whitespace (Leading & Trailing)":
            code.append("    df[new_col] = df[col].astype(str).str.strip()")
            
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Change Case & Trim",
            "Applies string formatting to one or more columns.\n\n"
            "This forces the column to string type, applies the operation, and either overwrites or creates a new column."
        )
