"""Independent t-test Dialog.

Allows selecting a test variable and a grouping variable with two groups.
Generates code using scipy.stats.ttest_ind to compare means.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class TTestDialog(BaseAnalysisDialog):
    """Dialog for performing an independent two-sample t-test."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Independent Samples t-test", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        """Add Test Variables and Grouping Variable selectors."""
        # Test Variables (Numeric)
        self.list_test_vars = QListWidget()
        row_test = self._create_selector_row("Test Variables:", self.list_test_vars, multi_select=True)
        layout.addWidget(row_test)

        # Grouping Variable (Categorical/Two groups)
        self.list_group_var = QListWidget()
        row_group = self._create_selector_row("Grouping Variable:", self.list_group_var, multi_select=False)
        layout.addWidget(row_group)

    def build_options(self, layout: QVBoxLayout) -> None:
        """Add options for the t-test."""
        group_assumptions = QGroupBox("Assumptions & Options")
        l_opts = QVBoxLayout(group_assumptions)

        self.chk_welch = QCheckBox("Assume unequal variances (Welch's t-test)")
        self.chk_welch.setChecked(True)
        l_opts.addWidget(self.chk_welch)

        l_opts.addWidget(QLabel("Alternative Hypothesis:"))
        self.cmb_alternative = QComboBox()
        self.cmb_alternative.addItems(["two-sided", "less", "greater"])
        l_opts.addWidget(self.cmb_alternative)

        layout.addWidget(group_assumptions)

    def generate_code(self) -> str:
        """Generate the Python code to compute the t-test."""
        test_vars = [self.list_test_vars.item(i).text() for i in range(self.list_test_vars.count())]
        group_var = self.list_group_var.item(0).text() if self.list_group_var.count() > 0 else None

        if not test_vars:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Test Variable.")
            return ""
        if not group_var:
            QMessageBox.warning(self, "Missing Input", "Please select a Grouping Variable.")
            return ""

        # Validate that the grouping variable has exactly two unique values
        try:
            import polars as pl
            if isinstance(self._df, pl.DataFrame):
                unique_groups = self._df[group_var].drop_nulls().unique().to_list()
            else:
                unique_groups = self._df[group_var].dropna().unique().tolist()
        except (ImportError, AttributeError):
            unique_groups = self._df[group_var].dropna().unique().tolist()

        if len(unique_groups) != 2:
            QMessageBox.warning(self, "Invalid Grouping", 
                                f"The grouping variable '{group_var}' must have exactly 2 unique values. "
                                f"Found {len(unique_groups)}.")
            return ""

        group1, group2 = unique_groups[0], unique_groups[1]
        
        equal_var = not self.chk_welch.isChecked()
        alternative = self.cmb_alternative.currentText()

        vars_str = ", ".join(f"'{v}'" for v in test_vars)

        code = [
            f"# Independent t-test for: {', '.join(test_vars)} by {group_var}",
            "import polars as pl",
            "import pandas as pd",
            "from scipy import stats",
            "",
            f"test_vars = [{vars_str}]",
            f"group_var = '{group_var}'",
            f"group1_val, group2_val = {repr(group1)}, {repr(group2)}",
            "",
            "results = []",
            "if isinstance(df, pl.DataFrame):",
            "    for var in test_vars:",
            "        data1 = df.filter(pl.col(group_var) == group1_val).select(var).drop_nulls().to_series()",
            "        data2 = df.filter(pl.col(group_var) == group2_val).select(var).drop_nulls().to_series()",
            f"        res = stats.ttest_ind(data1, data2, equal_var={equal_var}, alternative='{alternative}')",
            "        results.append({",
            "            'Variable': var,",
            "            't-statistic': float(res.statistic),",
            "            'p-value': float(res.pvalue),",
            f"            'Mean ({group1})': data1.mean(),",
            f"            'Mean ({group2})': data2.mean(),",
            "        })",
            "else:",
            "    for var in test_vars:",
            "        data1 = df[df[group_var] == group1_val][var].dropna()",
            "        data2 = df[df[group_var] == group2_val][var].dropna()",
            f"        res = stats.ttest_ind(data1, data2, equal_var={equal_var}, alternative='{alternative}')",
            "        results.append({",
            "            'Variable': var,",
            "            't-statistic': res.statistic,",
            "            'p-value': res.pvalue,",
            f"            'Mean ({group1})': data1.mean(),",
            f"            'Mean ({group2})': data2.mean(),",
            "        })",
            "",
            "results_df = pd.DataFrame(results)",
            "if 'show_result' in globals():",
            "    show_result('Independent t-test', results_df)",
            "else:",
            "    print(results_df.to_string())"
        ]

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Independent t-test Help",
            "Compares the means of two independent groups in order to determine whether "
            "there is statistical evidence that the associated population means are significantly different.\n\n"
            "Requirements:\n"
            "1. Test Variable(s): Must be numeric.\n"
            "2. Grouping Variable: Must contain exactly two distinct groups."
        )
