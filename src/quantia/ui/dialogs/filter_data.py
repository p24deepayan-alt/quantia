"""Filter Data Dialog.

Handles subsetting rows based on a condition (e.g., column == value).
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
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class FilterDataDialog(BaseAnalysisDialog):
    """Dialog for filtering/subsetting rows in the dataset."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Filter Data (Subset Rows)", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Filter based on Variable:", self.list_targets, multi_select=False)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_cond = QGroupBox("Condition")
        l_cond = QVBoxLayout(group_cond)

        l_cond.addWidget(QLabel("Operator:"))
        self.cmb_operator = QComboBox()
        self.cmb_operator.addItems([
            "== (Equals)",
            "!= (Not Equals)",
            "> (Greater Than)",
            "< (Less Than)",
            ">= (Greater or Equal)",
            "<= (Less or Equal)",
            "Contains (for Text)"
        ])
        l_cond.addWidget(self.cmb_operator)

        l_cond.addWidget(QLabel("Value:"))
        self.txt_value = QLineEdit()
        self.txt_value.setPlaceholderText("e.g. 50 or 'Male'")
        l_cond.addWidget(self.txt_value)

        layout.addWidget(group_cond)

    def generate_code(self) -> str:
        if self.list_targets.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select a variable to filter on.")
            return ""

        target_var = self.list_targets.item(0).text()
        operator_str = self.cmb_operator.currentText().split()[0]
        value = self.txt_value.text()

        if not value:
            QMessageBox.warning(self, "Missing Input", "Please provide a value for the condition.")
            return ""

        code = [
            f"# Filter Data: Keep rows where {target_var} {operator_str} {value}",
            "import polars as pl",
            "import pandas as pd",
            f"target = '{target_var}'",
        ]

        # Determine if value should be treated as string or numeric in the code
        try:
            float(value)
            val_repr = value
        except ValueError:
            val_repr = repr(value)

        code.append("if isinstance(df, pl.DataFrame):")
        if operator_str == "Contains":
            code.append(f"    df = df.filter(pl.col(target).cast(pl.Utf8).str.contains({val_repr}, ignore_case=True))")
        elif operator_str == "==":
            code.append(f"    df = df.filter(pl.col(target) == {val_repr})")
        elif operator_str == "!=":
            code.append(f"    df = df.filter(pl.col(target) != {val_repr})")
        elif operator_str == ">":
            code.append(f"    df = df.filter(pl.col(target) > {val_repr})")
        elif operator_str == "<":
            code.append(f"    df = df.filter(pl.col(target) < {val_repr})")
        elif operator_str == ">=":
            code.append(f"    df = df.filter(pl.col(target) >= {val_repr})")
        elif operator_str == "<=":
            code.append(f"    df = df.filter(pl.col(target) <= {val_repr})")
            
        code.append("else:")
        if operator_str == "Contains":
            code.append(f"    df = df[df[target].astype(str).str.contains({val_repr}, na=False, case=False)]")
        else:
            code.append(f"    df = df[df[target] {operator_str} {val_repr}]")

        code.append("print(f'Filtering applied. New shape: {df.shape}')")
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Filter Data Help",
            "Removes rows from the dataset that do not meet the specified condition.\n\n"
            "Warning: This action overwrites your current view. You can reload the dataset "
            "or use the script editor to undo."
        )
