"""If / Else (Conditional) Dialog.

Creates a new column based on a logical condition using np.where.
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


class IfElseDialog(BaseAnalysisDialog):
    """Dialog for conditional logic (If/Else)."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("If / Else (Conditional)", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Target Column to Evaluate:", self.list_targets, multi_select=False)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Condition
        group_cond = QGroupBox("Condition")
        l_cond = QVBoxLayout(group_cond)
        
        self.cmb_operator = QComboBox()
        self.cmb_operator.addItems([
            "Equals (==)",
            "Not Equals (!=)",
            "Greater Than (>)",
            "Less Than (<)",
            "Greater or Equal (>=)",
            "Less or Equal (<=)",
            "Contains (string)",
            "Is Missing (NA)"
        ])
        l_cond.addWidget(self.cmb_operator)
        
        self.txt_value = QLineEdit()
        self.txt_value.setPlaceholderText("Value to compare against (e.g. 100 or 'Yes')")
        l_cond.addWidget(self.txt_value)
        layout.addWidget(group_cond)

        # True / False
        group_tf = QGroupBox("Results")
        l_tf = QVBoxLayout(group_tf)
        
        l_tf.addWidget(QLabel("Value if True:"))
        self.txt_true = QLineEdit()
        self.txt_true.setPlaceholderText("e.g. 'High' or 1")
        l_tf.addWidget(self.txt_true)
        
        l_tf.addWidget(QLabel("Value if False:"))
        self.txt_false = QLineEdit()
        self.txt_false.setPlaceholderText("e.g. 'Low' or 0")
        l_tf.addWidget(self.txt_false)
        layout.addWidget(group_tf)

        # Output
        group_out = QGroupBox("Output")
        l_out = QVBoxLayout(group_out)
        l_out.addWidget(QLabel("New Column Name:"))
        self.txt_new_col = QLineEdit()
        self.txt_new_col.setText("Conditional_Result")
        l_out.addWidget(self.txt_new_col)
        layout.addWidget(group_out)

    def generate_code(self) -> str:
        if self.list_targets.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select a target column to evaluate.")
            return ""

        target = self.list_targets.item(0).text()
        op_text = self.cmb_operator.currentText()
        comp_val = self.txt_value.text().strip()
        val_true = self.txt_true.text().strip()
        val_false = self.txt_false.text().strip()
        new_col = self.txt_new_col.text().strip()

        if not new_col:
            QMessageBox.warning(self, "Missing Input", "Please provide a new column name.")
            return ""
            
        if not val_true or not val_false:
            QMessageBox.warning(self, "Missing Input", "Please provide both True and False values.")
            return ""
            
        if op_text not in ["Is Missing (NA)"] and not comp_val:
            QMessageBox.warning(self, "Missing Input", "Please provide a value to compare against.")
            return ""

        # Smartly format true/false values (quote them if they aren't numbers)
        def format_val(v: str) -> str:
            try:
                float(v)
                return v
            except ValueError:
                v_esc = v.replace("'", "\\'")
                return f"'{v_esc}'"
                
        def format_comp(v: str) -> str:
            # Check if target column is numeric
            is_numeric = pd.api.types.is_numeric_dtype(self._df[target])
            if is_numeric:
                try:
                    float(v)
                    return v
                except ValueError:
                    pass
            v_esc = v.replace("'", "\\'")
            return f"'{v_esc}'"

        code = [
            f"# If / Else logic on '{target}'",
            "import numpy as np"
        ]
        
        t_fmt = format_val(val_true)
        f_fmt = format_val(val_false)
        c_fmt = format_comp(comp_val)

        # Build condition string
        if op_text == "Equals (==)":
            cond = f"df['{target}'] == {c_fmt}"
        elif op_text == "Not Equals (!=)":
            cond = f"df['{target}'] != {c_fmt}"
        elif op_text == "Greater Than (>)":
            cond = f"df['{target}'] > {c_fmt}"
        elif op_text == "Less Than (<)":
            cond = f"df['{target}'] < {c_fmt}"
        elif op_text == "Greater or Equal (>=)":
            cond = f"df['{target}'] >= {c_fmt}"
        elif op_text == "Less or Equal (<=)":
            cond = f"df['{target}'] <= {c_fmt}"
        elif op_text == "Contains (string)":
            c_esc = comp_val.replace("'", "\\'")
            cond = f"df['{target}'].astype(str).str.contains('{c_esc}', na=False)"
        elif op_text == "Is Missing (NA)":
            cond = f"df['{target}'].isna()"
            
        code.append(f"df['{new_col}'] = np.where({cond}, {t_fmt}, {f_fmt})")
            
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: If / Else",
            "Creates a new column based on a logical condition.\n\n"
            "If the condition evaluates to True for a row, it gets the True value. Otherwise, it gets the False value.\n"
            "This uses highly optimized numpy vectorization."
        )
