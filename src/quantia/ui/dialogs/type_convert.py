"""Type & String Conversion Dialog.

Handles changing variable types (String <-> Numeric) and basic string manipulations
(adding/removing characters).
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


class TypeConvertDialog(BaseAnalysisDialog):
    """Dialog for converting types and manipulating strings."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Convert Type & String Manipulate", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Variables to modify:", self.list_targets, multi_select=True)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        group_op = QGroupBox("Operation")
        l_op = QVBoxLayout(group_op)

        self.rad_to_numeric = QRadioButton("Convert to Numeric")
        self.rad_to_numeric.setChecked(True)
        l_op.addWidget(self.rad_to_numeric)

        self.rad_to_string = QRadioButton("Convert to String (Text)")
        l_op.addWidget(self.rad_to_string)
        
        self.rad_replace = QRadioButton("Remove / Replace Characters")
        l_op.addWidget(self.rad_replace)
        
        self.rad_append = QRadioButton("Add Prefix / Suffix")
        l_op.addWidget(self.rad_append)
        
        layout.addWidget(group_op)

        # String Replace Options
        self.group_replace = QGroupBox("Replace Options")
        l_replace = QVBoxLayout(self.group_replace)
        l_replace.addWidget(QLabel("Target character/string to remove or replace:"))
        self.txt_target = QLineEdit()
        self.txt_target.setPlaceholderText("e.g. $ or ,")
        l_replace.addWidget(self.txt_target)
        
        l_replace.addWidget(QLabel("Replace with (leave blank to remove):"))
        self.txt_replace = QLineEdit()
        l_replace.addWidget(self.txt_replace)
        layout.addWidget(self.group_replace)
        
        # String Append Options
        self.group_append = QGroupBox("Add Prefix / Suffix Options")
        l_append = QVBoxLayout(self.group_append)
        l_append.addWidget(QLabel("Prefix:"))
        self.txt_prefix = QLineEdit()
        l_append.addWidget(self.txt_prefix)
        l_append.addWidget(QLabel("Suffix:"))
        self.txt_suffix = QLineEdit()
        l_append.addWidget(self.txt_suffix)
        layout.addWidget(self.group_append)

        # Output Destination
        group_dest = QGroupBox("Output Destination")
        l_dest = QVBoxLayout(group_dest)
        
        self.rad_new_col = QRadioButton("Create new columns")
        self.rad_new_col.setChecked(True)
        l_dest.addWidget(self.rad_new_col)
        
        self.rad_overwrite = QRadioButton("Overwrite existing columns")
        l_dest.addWidget(self.rad_overwrite)
        
        layout.addWidget(group_dest)

        # Connect signals to toggle visibility/enabled states
        self.group_replace.setEnabled(False)
        self.group_append.setEnabled(False)
        
        def update_ui() -> None:
            self.group_replace.setEnabled(self.rad_replace.isChecked())
            self.group_append.setEnabled(self.rad_append.isChecked())
            
        self.rad_to_numeric.toggled.connect(update_ui)
        self.rad_to_string.toggled.connect(update_ui)
        self.rad_replace.toggled.connect(update_ui)
        self.rad_append.toggled.connect(update_ui)

    def generate_code(self) -> str:
        targets = [self.list_targets.item(i).text() for i in range(self.list_targets.count())]
        if not targets:
            QMessageBox.warning(self, "Missing Input", "Please select at least one variable.")
            return ""

        new_cols = self.rad_new_col.isChecked()
        vars_str = ", ".join(f"'{v}'" for v in targets)
        
        code = [
            "# Type / String Conversion",
            f"target_cols = [{vars_str}]",
            "for col in target_cols:"
        ]
        
        if new_cols:
            code.append("    new_col = 'Mod_' + col")
        else:
            code.append("    new_col = col")

        if self.rad_to_numeric.isChecked():
            code.append("    # Coerce forces unparseable strings to NaN")
            code.append("    df[new_col] = pd.to_numeric(df[col], errors='coerce')")
            
        elif self.rad_to_string.isChecked():
            code.append("    df[new_col] = df[col].astype(str)")
            
        elif self.rad_replace.isChecked():
            targ = self.txt_target.text()
            repl = self.txt_replace.text()
            if not targ:
                QMessageBox.warning(self, "Missing Input", "Please specify the target character to replace.")
                return ""
            code.append(f"    df[new_col] = df[col].astype(str).str.replace({repr(targ)}, {repr(repl)}, regex=False)")
            
        elif self.rad_append.isChecked():
            prefix = self.txt_prefix.text()
            suffix = self.txt_suffix.text()
            code.append(f"    df[new_col] = {repr(prefix)} + df[col].astype(str) + {repr(suffix)}")

        code.append(f"print('Processed {len(targets)} columns.')")
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Convert Help",
            "To Numeric: Converts variables to numbers (e.g., '2.55' -> 2.55). Invalid strings become missing (NaN).\n"
            "Remove/Replace: Use this to remove symbols like '$' or ',' before converting to numeric."
        )
