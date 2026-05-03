"""Find & Replace Dialog.

Replaces string substrings in a column, optionally using Regex.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class FindReplaceDialog(BaseAnalysisDialog):
    """Dialog for Find & Replace in string columns."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Find & Replace", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Target Column (String):", self.list_targets, multi_select=False)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Find
        group_find = QGroupBox("Find Text")
        l_find = QVBoxLayout(group_find)
        self.txt_find = QLineEdit()
        self.txt_find.setPlaceholderText("Text to search for")
        l_find.addWidget(self.txt_find)
        
        self.chk_regex = QCheckBox("Use Regular Expressions (Regex)")
        l_find.addWidget(self.chk_regex)
        
        layout.addWidget(group_find)

        # Replace
        group_replace = QGroupBox("Replace With")
        l_replace = QVBoxLayout(group_replace)
        self.txt_replace = QLineEdit()
        self.txt_replace.setPlaceholderText("Leave blank to remove text")
        l_replace.addWidget(self.txt_replace)
        layout.addWidget(group_replace)

        # Output
        group_out = QGroupBox("Output")
        l_out = QVBoxLayout(group_out)
        l_out.addWidget(QLabel("New Column Name:"))
        self.txt_new_col = QLineEdit()
        self.txt_new_col.setPlaceholderText("Leave blank to overwrite")
        l_out.addWidget(self.txt_new_col)
        layout.addWidget(group_out)

    def generate_code(self) -> str:
        if self.list_targets.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select a target column.")
            return ""

        target = self.list_targets.item(0).text()
        find_str = self.txt_find.text()
        
        if not find_str:
            QMessageBox.warning(self, "Missing Input", "Please enter text to find.")
            return ""

        replace_str = self.txt_replace.text()
        regex = self.chk_regex.isChecked()

        new_col = self.txt_new_col.text().strip()
        if not new_col:
            new_col = target

        code = [
            f"# String Find & Replace",
        ]
        
        # Escape quotes
        f_esc = find_str.replace("'", "\\'")
        r_esc = replace_str.replace("'", "\\'")
        
        code.append(f"df['{new_col}'] = df['{target}'].astype(str).str.replace(r'{f_esc}', '{r_esc}', regex={regex})")
            
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Find & Replace",
            "Finds a specific string and replaces it.\n\n"
            "If Regex is checked, the 'Find' box accepts regular expressions (e.g., ^[A-Z] or \\d+)."
        )
