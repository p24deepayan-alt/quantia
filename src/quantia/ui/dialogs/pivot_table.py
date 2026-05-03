"""Pivot Table / Group-By Dialog.

Allows grouping by categorical columns and aggregating values.
Supports simple GroupBy as well as true Pivot Tables.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class PivotTableDialog(BaseAnalysisDialog):
    """Dialog for creating Pivot Tables and Group-By aggregations."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Pivot Table / Group By", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        # Group By (Rows)
        self.list_groupby = QListWidget()
        row_groupby = self._create_selector_row("Group By Columns (Rows):", self.list_groupby, multi_select=True)
        layout.addWidget(row_groupby)

        # Pivot Column (Columns)
        self.list_pivot = QListWidget()
        row_pivot = self._create_selector_row("Pivot Column (Columns) [Optional]:", self.list_pivot, multi_select=False)
        layout.addWidget(row_pivot)

        # Values
        self.list_values = QListWidget()
        row_values = self._create_selector_row("Value Columns (To Aggregate):", self.list_values, multi_select=True)
        layout.addWidget(row_values)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Aggregation
        group_agg = QGroupBox("Aggregation Function")
        l_agg = QVBoxLayout(group_agg)
        
        self.cmb_agg = QComboBox()
        self.cmb_agg.addItems([
            "Sum",
            "Mean",
            "Median",
            "Count",
            "Min",
            "Max",
            "Standard Deviation",
            "First",
            "Last"
        ])
        l_agg.addWidget(self.cmb_agg)
        layout.addWidget(group_agg)

        # Output Destination
        group_dest = QGroupBox("Output Destination")
        l_dest = QVBoxLayout(group_dest)
        
        self.rad_display = QRadioButton("Display as result only")
        self.rad_display.setChecked(True)
        l_dest.addWidget(self.rad_display)

        self.rad_overwrite = QRadioButton("Replace current dataset with result")
        l_dest.addWidget(self.rad_overwrite)
        
        layout.addWidget(group_dest)

    def generate_code(self) -> str:
        groupby_cols = [self.list_groupby.item(i).text() for i in range(self.list_groupby.count())]
        value_cols = [self.list_values.item(i).text() for i in range(self.list_values.count())]
        pivot_col = self.list_pivot.item(0).text() if self.list_pivot.count() > 0 else None

        if not groupby_cols and not pivot_col:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Group By or Pivot column.")
            return ""

        if not value_cols:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Value column to aggregate.")
            return ""

        agg_map = {
            "Sum": "sum",
            "Mean": "mean",
            "Median": "median",
            "Count": "count",
            "Min": "min",
            "Max": "max",
            "Standard Deviation": "std",
            "First": "first",
            "Last": "last"
        }
        agg_func = agg_map[self.cmb_agg.currentText()]
        overwrite = self.rad_overwrite.isChecked()

        gb_str = ", ".join(f"'{c}'" for c in groupby_cols)
        val_str = ", ".join(f"'{c}'" for c in value_cols)

        code = [
            f"# Pivot Table / Group By: {self.cmb_agg.currentText()}"
        ]

        if pivot_col:
            # True Pivot Table
            code.append("import pandas as pd")
            code.append(f"pivot_df = pd.pivot_table(")
            code.append(f"    df,")
            code.append(f"    values=[{val_str}],")
            if groupby_cols:
                code.append(f"    index=[{gb_str}],")
            code.append(f"    columns='{pivot_col}',")
            code.append(f"    aggfunc='{agg_func}'")
            code.append(")")
            code.append("pivot_df = pivot_df.reset_index()")
            # Flatten multi-index columns if they exist
            code.append("if isinstance(pivot_df.columns, pd.MultiIndex):")
            code.append("    pivot_df.columns = ['_'.join(str(c) for c in col).strip('_') for col in pivot_df.columns.values]")
            
            result_var = "pivot_df"
            
        else:
            # Simple Group By
            if len(value_cols) == 1:
                code.append(f"grouped_df = df.groupby([{gb_str}])['{value_cols[0]}'].agg('{agg_func}').reset_index()")
            else:
                code.append(f"grouped_df = df.groupby([{gb_str}])[[{val_str}]].agg('{agg_func}').reset_index()")
            
            result_var = "grouped_df"

        if overwrite:
            code.append(f"\ndf = {result_var}")
            code.append("print(f'Replaced dataset with aggregated results: {df.shape[0]} rows, {df.shape[1]} columns')")
        else:
            code.append("\n# Format Output")
            code.append("html_output = []")
            code.append(f"html_output.append('<h3>Pivot Table / Group By Results</h3>')")
            code.append(f"html_output.append('<p><b>Aggregation:</b> {self.cmb_agg.currentText()}</p>')")
            code.append(f"html_output.append({result_var}.to_html(classes='table table-sm table-striped'))")
            code.append("display_html('\\n'.join(html_output))")

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Pivot Table / Group By",
            "Aggregates data based on categorical groupings.\n\n"
            "Group By: The rows of your result.\n"
            "Pivot Column: The columns of your result (optional).\n"
            "Value Columns: The numeric data to aggregate.\n\n"
            "You can choose to view the result as a report table, or replace your entire dataset with the aggregated version."
        )
