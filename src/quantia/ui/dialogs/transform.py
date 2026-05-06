"""Transform Data Dialog.

Handles mathematical transformations like Log, Square Root, Standardize, Normalize.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QListWidget,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class TransformDataDialog(BaseAnalysisDialog):
    """Dialog for mathematically transforming numeric variables."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Transform Data", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Variables to Transform (numeric):", self.list_targets, multi_select=True)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Transformation Type
        group_type = QGroupBox("Transformation Type")
        l_type = QVBoxLayout(group_type)
        
        self.cmb_transform = QComboBox()
        self.cmb_transform.addItems([
            "Log (base e)", 
            "Log (base 10)", 
            "Square Root", 
            "Standardize (Z-score)", 
            "Min-Max Normalize"
        ])
        l_type.addWidget(self.cmb_transform)
        layout.addWidget(group_type)

        # Output Destination
        group_dest = QGroupBox("Output Destination")
        l_dest = QVBoxLayout(group_dest)
        
        self.rad_new_col = QRadioButton("Create new columns (e.g., 'Log_VarName')")
        self.rad_new_col.setChecked(True)
        l_dest.addWidget(self.rad_new_col)
        
        self.rad_overwrite = QRadioButton("Overwrite existing columns")
        l_dest.addWidget(self.rad_overwrite)
        
        layout.addWidget(group_dest)

    def generate_code(self) -> str:
        targets = [self.list_targets.item(i).text() for i in range(self.list_targets.count())]
        if not targets:
            QMessageBox.warning(self, "Missing Input", "Please select at least one variable to transform.")
            return ""

        transform_type = self.cmb_transform.currentText()
        new_cols = self.rad_new_col.isChecked()
        prefix = transform_type.split(' ')[0].replace('-', '')

        vars_str = ", ".join(f"'{v}'" for v in targets)
        code = [
            f"# Data Transformation: {transform_type}",
            "import numpy as np",
            "import polars as pl",
            "import pandas as pd",
        ]

        if transform_type == "Standardize (Z-score)":
            code.insert(1, "from scipy.stats import zscore")

        code.extend([
            "",
            f"target_cols = [{vars_str}]",
            "if isinstance(df, pl.DataFrame):",
            "    # Multi-threaded transformations via Polars expressions",
            "    exprs = []",
            "    for i, col in enumerate(target_cols):",
            "        if 'progress' in globals(): progress(int((i+1)/len(target_cols)*100))",
            f"        new_col = f'{prefix}_' + col if {new_cols} else col"
        ])

        if transform_type == "Log (base e)":
            code.append("        exprs.append(pl.col(col).log().alias(new_col))")
        elif transform_type == "Log (base 10)":
            code.append("        exprs.append(pl.col(col).log(10).alias(new_col))")
        elif transform_type == "Square Root":
            code.append("        exprs.append(pl.col(col).sqrt().alias(new_col))")
        elif transform_type == "Standardize (Z-score)":
            code.append("        exprs.append(((pl.col(col) - pl.col(col).mean()) / pl.col(col).std()).alias(new_col))")
        elif transform_type == "Min-Max Normalize":
            code.append("        exprs.append(((pl.col(col) - pl.col(col).min()) / (pl.col(col).max() - pl.col(col).min())).alias(new_col))")

        code.extend([
            "    df = df.with_columns(exprs)",
            "else:",
            "    for i, col in enumerate(target_cols):",
            "        if 'progress' in globals(): progress(int((i+1)/len(target_cols)*100))",
            f"        new_col = f'{prefix}_' + col if {new_cols} else col"
        ])

        # Apply transformation (Pandas fallback)
        if transform_type == "Log (base e)":
            code.append("        df[new_col] = np.log(df[col])")
        elif transform_type == "Log (base 10)":
            code.append("        df[new_col] = np.log10(df[col])")
        elif transform_type == "Square Root":
            code.append("        df[new_col] = np.sqrt(df[col])")
        elif transform_type == "Standardize (Z-score)":
            code.append("        df[new_col] = zscore(df[col], nan_policy='omit')")
        elif transform_type == "Min-Max Normalize":
            code.append("        min_val, max_val = df[col].min(), df[col].max()")
            code.append("        df[new_col] = (df[col] - min_val) / (max_val - min_val)")

        code.append(f"print('Transformed {len(targets)} columns.')")
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Transform Data Help",
            "Applies a mathematical transformation to the selected numeric variables.\n\n"
            "By default, this creates new columns to preserve your original data."
        )
