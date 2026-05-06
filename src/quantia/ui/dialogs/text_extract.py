"""Text Before / After Dialog.

Splits strings by a delimiter and keeps the first or second half.
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


class TextExtractDialog(BaseAnalysisDialog):
    """Dialog for extracting text before or after a delimiter."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Text Before / After", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Target Column (String):", self.list_targets, multi_select=False)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Delimiter
        group_delim = QGroupBox("Delimiter / Separator")
        l_delim = QVBoxLayout(group_delim)
        self.txt_delimiter = QLineEdit()
        self.txt_delimiter.setPlaceholderText("e.g. - or _ or space")
        l_delim.addWidget(self.txt_delimiter)
        layout.addWidget(group_delim)

        # Mode
        group_mode = QGroupBox("Extraction Mode")
        l_mode = QVBoxLayout(group_mode)
        self.rad_before = QRadioButton("Keep Text BEFORE Delimiter")
        self.rad_before.setChecked(True)
        self.rad_after = QRadioButton("Keep Text AFTER Delimiter")
        l_mode.addWidget(self.rad_before)
        l_mode.addWidget(self.rad_after)
        layout.addWidget(group_mode)

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
        delim = self.txt_delimiter.text()
        
        if not delim:
            QMessageBox.warning(self, "Missing Input", "Please enter a delimiter.")
            return ""

        new_col = self.txt_new_col.text().strip()
        if not new_col:
            new_col = target

        mode = "Before" if self.rad_before.isChecked() else "After"
        
        # Escape quotes in delimiter for the generated code
        delim_esc = delim.replace("'", "\\'")

        code = [
            f"# Text Extract: Keep Text {mode} '{delim}' in '{target}'",
            "import polars as pl",
            "import pandas as pd",
            "",
            "if isinstance(df, pl.DataFrame):",
            "    # Multi-threaded extraction via Polars",
        ]

        if mode == "Before":
            code.append(f"    res = pl.col('{target}').cast(pl.Utf8).str.split_exact('{delim_esc}', 1).struct.field('field_0')")
            code.append(f"    df = df.with_columns(res.replace('', None).alias('{new_col}'))")
        else:
            code.append(f"    res = pl.col('{target}').cast(pl.Utf8).str.split_exact('{delim_esc}', 1).struct.field('field_1')")
            code.append(f"    df = df.with_columns(res.replace('', None).alias('{new_col}'))")

        code.extend([
            "else:",
            f"    # Pandas fallback"
        ])
        
        if mode == "Before":
            code.append(f"    res = df['{target}'].astype(str).str.split('{delim_esc}').str[0]")
            code.append(f"    df['{new_col}'] = res.mask(res == '')")
        else:
            code.append(f"    res = df['{target}'].astype(str).str.split('{delim_esc}', n=1).str[1]")
            code.append(f"    df['{new_col}'] = res.mask(res == '')")
            
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Text Before / After",
            "Extracts text based on a delimiter.\n\n"
            "Keep Text BEFORE: Splits the string and keeps everything before the first occurrence of the delimiter.\n"
            "Keep Text AFTER: Splits the string and keeps everything after the first occurrence."
        )
