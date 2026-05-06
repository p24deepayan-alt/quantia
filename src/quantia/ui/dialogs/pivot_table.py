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
        agg_func_name = self.cmb_agg.currentText()
        agg_func = agg_map[agg_func_name]
        overwrite = self.rad_overwrite.isChecked()

        gb_str = ", ".join(f"'{c}'" for c in groupby_cols)
        val_str = ", ".join(f"'{c}'" for c in value_cols)

        code = [
            f"# Pivot Table / Group By: {agg_func_name}",
            "import polars as pl",
            "import pandas as pd",
            ""
        ]

        code.append("if isinstance(df, pl.DataFrame):")
        if pivot_col:
            # Polars Pivot
            code.append("    # Polars Pivot")
            # Note: Polars pivot aggregate_function can be a string for simple aggs
            code.append(f"    result_df = df.pivot(")
            code.append(f"        values=[{val_str}],")
            code.append(f"        index=[{gb_str}],")
            code.append(f"        on='{pivot_col}',")
            code.append(f"        aggregate_function='{agg_func}'")
            code.append("    )")
        else:
            # Polars Group By
            code.append("    # Polars Group By")
            # In Polars, we need to map the aggregation function to expressions
            pl_agg_map = {
                "sum": "pl.col(c).sum()",
                "mean": "pl.col(c).mean()",
                "median": "pl.col(c).median()",
                "count": "pl.col(c).count()",
                "min": "pl.col(c).min()",
                "max": "pl.col(c).max()",
                "std": "pl.col(c).std()",
                "first": "pl.col(c).first()",
                "last": "pl.col(c).last()"
            }
            pl_exprs = ", ".join(pl_agg_map[agg_func].replace("c", f"'{c}'") for c in value_cols)
            code.append(f"    result_df = df.group_by([{gb_str}]).agg([{pl_exprs}])")

        code.append("else:")
        if pivot_col:
            # Pandas Pivot
            code.append(f"    result_df = pd.pivot_table(")
            code.append(f"        df,")
            code.append(f"        values=[{val_str}],")
            if groupby_cols:
                code.append(f"        index=[{gb_str}],")
            code.append(f"        columns='{pivot_col}',")
            code.append(f"        aggfunc='{agg_func}'")
            code.append("    ).reset_index()")
            # Flatten multi-index columns if they exist
            code.append("    if isinstance(result_df.columns, pd.MultiIndex):")
            code.append("        result_df.columns = ['_'.join(str(c) for c in col).strip('_') for col in result_df.columns.values]")
        else:
            # Pandas Group By
            if len(value_cols) == 1:
                code.append(f"    result_df = df.groupby([{gb_str}])['{value_cols[0]}'].agg('{agg_func}').reset_index()")
            else:
                code.append(f"    result_df = df.groupby([{gb_str}])[[{val_str}]].agg('{agg_func}').reset_index()")

        if overwrite:
            code.append("\ndf = result_df")
            code.append("pivot_df = result_df  # Legacy compatibility")
            code.append("if isinstance(df, pl.DataFrame):")
            code.append("    print(f'Replaced dataset with aggregated Polars results: {df.height} rows, {df.width} columns')")
            code.append("else:")
            code.append("    print(f'Replaced dataset with aggregated Pandas results: {df.shape[0]} rows, {df.shape[1]} columns')")
        else:
            code.append("\npivot_df = result_df  # Legacy compatibility")
            code.append("\n# Format Output")
            code.append("html_output = []")
            code.append(f"html_output.append('<h3>Pivot Table / Group By Results</h3>')")
            code.append(f"html_output.append('<p><b>Aggregation:</b> {agg_func_name}</p>')")
            
            code.append("if isinstance(result_df, pl.DataFrame):")
            code.append("    html_output.append(result_df.to_pandas().to_html(classes='table table-sm table-striped'))")
            code.append("else:")
            code.append("    html_output.append(result_df.to_html(classes='table table-sm table-striped'))")
            
            code.append("if 'display_html' in globals():")
            code.append("    display_html('\\n'.join(html_output))")
            code.append("elif 'show_result' in globals():")
            code.append(f"    show_result('Pivot Table Results', '\\n'.join(html_output))")
            code.append("else:")
            code.append("    print('\\n'.join(html_output))")

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
