"""Data Cleaning Dialog.

Handles dropping NA rows, dropping columns, and basic imputation.
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


class CleanDataDialog(BaseAnalysisDialog):
    """Dialog for cleaning data (missing values, dropping cols)."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Clean Data", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Target Variables:", self.list_targets, multi_select=True)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_action = QGroupBox("Action")
        l_action = QVBoxLayout(group_action)

        self.rad_drop_na = QRadioButton("Drop rows with missing values")
        self.rad_drop_na.setChecked(True)
        l_action.addWidget(self.rad_drop_na)

        self.rad_drop_col = QRadioButton("Delete selected columns entirely")
        l_action.addWidget(self.rad_drop_col)

        self.rad_impute = QRadioButton("Impute (fill) missing values")
        l_action.addWidget(self.rad_impute)
        
        layout.addWidget(group_action)

        # Imputation options
        self.group_impute = QGroupBox("Imputation Strategy")
        l_impute = QVBoxLayout(self.group_impute)
        
        self.cmb_strategy = QComboBox()
        self.cmb_strategy.addItems(["Mean", "Median", "Mode", "Custom Constant"])
        l_impute.addWidget(self.cmb_strategy)
        
        self.txt_constant = QLineEdit()
        self.txt_constant.setPlaceholderText("Enter constant value...")
        self.txt_constant.setEnabled(False)
        l_impute.addWidget(self.txt_constant)
        
        layout.addWidget(self.group_impute)
        self.group_impute.setEnabled(False)

        # Connect signals
        self.rad_impute.toggled.connect(self.group_impute.setEnabled)
        self.cmb_strategy.currentTextChanged.connect(
            lambda t: self.txt_constant.setEnabled(t == "Custom Constant")
        )

    def generate_code(self) -> str:
        targets = [self.list_targets.item(i).text() for i in range(self.list_targets.count())]
        if not targets:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Target Variable.")
            return ""

        vars_str = ", ".join(f"'{v}'" for v in targets)
        code = [
            "# Data Cleaning",
            f"target_cols = [{vars_str}]"
        ]

        if self.rad_drop_col.isChecked():
            code.append("df = df.drop(columns=target_cols)")
        elif self.rad_drop_na.isChecked():
            code.append("df = df.dropna(subset=target_cols)")
        elif self.rad_impute.isChecked():
            strategy = self.cmb_strategy.currentText()
            code.append("for col in target_cols:")
            if strategy == "Mean":
                code.append("    df[col] = df[col].fillna(df[col].mean())")
            elif strategy == "Median":
                code.append("    df[col] = df[col].fillna(df[col].median())")
            elif strategy == "Mode":
                code.append("    df[col] = df[col].fillna(df[col].mode()[0])")
            elif strategy == "Custom Constant":
                val = self.txt_constant.text()
                # Try to parse as numeric if possible
                try:
                    float(val)
                    code.append(f"    df[col] = df[col].fillna({val})")
                except ValueError:
                    code.append(f"    df[col] = df[col].fillna('{val}')")

        code.append("print(f'Operation complete. Current shape: {df.shape}')")
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Clean Data Help",
            "Drop rows with NA: Removes any row where the selected variables are missing.\n"
            "Drop columns: Completely removes the selected columns from the dataset.\n"
            "Impute: Fills missing values in the selected columns with a specific value (e.g., Mean)."
        )
