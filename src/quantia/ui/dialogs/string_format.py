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
            "import polars as pl",
            "import pandas as pd",
            f"target_cols = [{vars_str}]",
            "",
            "if isinstance(df, pl.DataFrame):",
            "    # Multi-threaded formatting via Polars",
            "    exprs = []",
            "    for col in target_cols:",
            f"        new_col = 'Formatted_' + col if {new_cols} else col"
        ]

        if operation == "UPPERCASE":
            code.append("        exprs.append(pl.col(col).cast(pl.Utf8).str.to_uppercase().replace('', None).alias(new_col))")
        elif operation == "lowercase":
            code.append("        exprs.append(pl.col(col).cast(pl.Utf8).str.to_lowercase().replace('', None).alias(new_col))")
        elif operation == "Title Case":
            code.append("        exprs.append(pl.col(col).cast(pl.Utf8).str.to_titlecase().replace('', None).alias(new_col))")
        elif operation == "Capitalize First Letter":
            code.append("        exprs.append((pl.col(col).cast(pl.Utf8).str.slice(0, 1).str.to_uppercase() + pl.col(col).cast(pl.Utf8).str.slice(1).str.to_lowercase()).replace('', None).alias(new_col))")
        elif operation == "Trim Whitespace (Leading & Trailing)":
            code.append("        exprs.append(pl.col(col).cast(pl.Utf8).str.strip_chars().replace('', None).alias(new_col))")

        code.extend([
            "    df = df.with_columns(exprs)",
            "else:",
            "    for col in target_cols:",
            f"        new_col = 'Formatted_' + col if {new_cols} else col"
        ])

        # Apply transformation (Pandas fallback)
        if operation == "UPPERCASE":
            code.append("        res = df[col].astype(str).str.upper()")
            code.append("        df[new_col] = res.mask(res == '')")
        elif operation == "lowercase":
            code.append("        res = df[col].astype(str).str.lower()")
            code.append("        df[new_col] = res.mask(res == '')")
        elif operation == "Title Case":
            code.append("        res = df[col].astype(str).str.title()")
            code.append("        df[new_col] = res.mask(res == '')")
        elif operation == "Capitalize First Letter":
            code.append("        res = df[col].astype(str).str.capitalize()")
            code.append("        df[new_col] = res.mask(res == '')")
        elif operation == "Trim Whitespace (Leading & Trailing)":
            code.append("        res = df[col].astype(str).str.strip()")
            code.append("        df[new_col] = res.mask(res == '')")
            
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Change Case & Trim",
            "Applies string formatting to one or more columns.\n\n"
            "This forces the column to string type, applies the operation, and either overwrites or creates a new column."
        )
