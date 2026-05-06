"""Merge / Join Data Dialog.

Handles merging the current dataframe with an external file.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class MergeJoinDialog(BaseAnalysisDialog):
    """Dialog for merging/joining with an external file."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Merge / Join Data", df, parent)
        self.btn_help.clicked.connect(self._show_help)
        self._external_path = ""

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_targets = QListWidget()
        row = self._create_selector_row("Merge Key (Current Data):", self.list_targets, multi_select=False)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        # External File Selection
        group_file = QGroupBox("External Dataset")
        l_file = QVBoxLayout(group_file)
        
        h_file = QHBoxLayout()
        self.txt_file = QLineEdit()
        self.txt_file.setReadOnly(True)
        self.txt_file.setPlaceholderText("Select file to merge...")
        h_file.addWidget(self.txt_file)
        
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_file)
        h_file.addWidget(btn_browse)
        l_file.addLayout(h_file)

        l_file.addWidget(QLabel("Merge Key (External Data):"))
        self.txt_ext_key = QLineEdit()
        self.txt_ext_key.setPlaceholderText("Column name in external file")
        l_file.addWidget(self.txt_ext_key)

        layout.addWidget(group_file)

        # Join Type
        group_join = QGroupBox("Join Type")
        l_join = QVBoxLayout(group_join)
        self.cmb_how = QComboBox()
        self.cmb_how.addItems(["inner (Intersection)", "left (Keep all current)", "right (Keep all external)", "outer (Union)"])
        l_join.addWidget(self.cmb_how)
        layout.addWidget(group_join)

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Merge", "", "Data Files (*.csv *.xlsx *.xls *.parquet)"
        )
        if path:
            self._external_path = path
            self.txt_file.setText(Path(path).name)

    def generate_code(self) -> str:
        if self.list_targets.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select a Merge Key from the current data.")
            return ""

        if not self._external_path:
            QMessageBox.warning(self, "Missing Input", "Please select an external file to merge with.")
            return ""

        ext_key = self.txt_ext_key.text()
        if not ext_key:
            QMessageBox.warning(self, "Missing Input", "Please specify the merge key column for the external file.")
            return ""

        current_key = self.list_targets.item(0).text()
        how_str = self.cmb_how.currentText().split()[0]
        ext = Path(self._external_path).suffix.lower()

        code = [
            f"# Merge/Join Data with {Path(self._external_path).name}",
            "import polars as pl",
            "import pandas as pd",
            f"ext_path = r'{self._external_path}'",
            "",
            "if isinstance(df, pl.DataFrame):",
            "    # Multi-threaded loading and join via Polars"
        ]

        # Load external data (Polars branch)
        if ext == ".csv":
            code.append("    df_ext = pl.read_csv(ext_path)")
        elif ext in [".xls", ".xlsx"]:
            code.append("    df_ext = pl.from_pandas(pd.read_excel(ext_path))")
        elif ext == ".parquet":
            code.append("    df_ext = pl.read_parquet(ext_path)")
        
        # Perform merge (Polars branch)
        if how_str == "right":
            # Polars uses left, swap for right
            code.append(f"    df = df_ext.join(df, left_on='{ext_key}', right_on='{current_key}', how='left')")
        else:
            code.append(f"    df = df.join(df_ext, left_on='{current_key}', right_on='{ext_key}', how='{how_str}')")
        
        code.append("else:")

        # Load external data (Pandas branch)
        if ext == ".csv":
            code.append("    df_ext = pd.read_csv(ext_path, low_memory=False)")
        elif ext in [".xls", ".xlsx"]:
            code.append("    df_ext = pd.read_excel(ext_path)")
        elif ext == ".parquet":
            code.append("    df_ext = pd.read_parquet(ext_path)")

        # Perform merge (Pandas branch)
        code.append(
            f"    df = pd.merge(df, df_ext, left_on='{current_key}', right_on='{ext_key}', how='{how_str}')"
        )
        code.append("print(f'Merge successful. New shape: {df.shape}')")

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Merge Data Help",
            "Combines the current dataset with another file based on a common key (column).\n\n"
            "Inner: Only keep rows where the key exists in both datasets.\n"
            "Left: Keep all rows from the current dataset.\n"
            "Right: Keep all rows from the external file.\n"
            "Outer: Keep all rows from both datasets."
        )
