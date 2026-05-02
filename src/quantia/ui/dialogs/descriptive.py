"""Descriptive Statistics Dialog.

Allows selecting variables to compute comprehensive summary statistics:
- Base: Count, Type
- Numeric: Mean, Median, Mode, Min, Max, Std Dev, Variance, 25th %ile, 75th %ile
- Categorical: Unique Values
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class DescriptiveStatsDialog(BaseAnalysisDialog):
    """Dialog for computing descriptive statistics."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Descriptive Statistics", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        """Add the 'Variables to Analyze' list."""
        self.list_targets = QListWidget()
        row = self._create_selector_row("Variables to Analyze:", self.list_targets, multi_select=True)
        layout.addWidget(row)

    def build_options(self, layout: QVBoxLayout) -> None:
        """Informational text since we output all stats by default now."""
        lbl = QLabel(
            "Descriptive statistics will be computed for all selected variables.\n\n"
            "• Numeric variables: Mean, Median, Mode, Min, Max, Std Dev, Variance, Quartiles.\n"
            "• Categorical variables: Count, Mode, Unique Values.\n\n"
            "The output will be combined into a single results table."
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

    def generate_code(self) -> str:
        """Generate the Python code to compute the stats."""
        targets = []
        for i in range(self.list_targets.count()):
            targets.append(self.list_targets.item(i).text())
            
        if not targets:
            QMessageBox.warning(self, "No Variables", "Please select at least one variable.")
            return ""

        vars_str = ", ".join(f"'{v}'" for v in targets)
        
        code = [
            f"# Descriptive Statistics for: {', '.join(targets)}",
            "import pandas as pd",
            f"vars_to_analyze = [{vars_str}]",
            "results = []",
            "",
            "for col in vars_to_analyze:",
            "    s = df[col]",
            "    is_num = pd.api.types.is_numeric_dtype(s)",
            "    row = {",
            "        'Variable': col,",
            "        'Count': s.count(),",
            "        'Type': 'Numeric' if is_num else 'Categorical',",
            "        'Mean': s.mean() if is_num else None,",
            "        'Median': s.median() if is_num else None,",
            "        'Mode': s.mode()[0] if not s.mode().empty else None,",
            "        'Min': s.min() if is_num else None,",
            "        'Max': s.max() if is_num else None,",
            "        'Std Dev': s.std() if is_num else None,",
            "        'Variance': s.var() if is_num else None,",
            "        '25th %ile': s.quantile(0.25) if is_num else None,",
            "        '75th %ile': s.quantile(0.75) if is_num else None,",
            "        'Unique Values': s.nunique() if not is_num else None",
            "    }",
            "    results.append(row)",
            "",
            "results_df = pd.DataFrame(results)",
            "if 'show_result' in globals():",
            "    show_result('Descriptive Statistics', results_df)",
            "else:",
            "    print(results_df.to_string())"
        ]
        
        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Descriptive Statistics Help",
            "Computes a comprehensive table of summary statistics for all selected variables.\n\n"
            "Numeric and categorical variables are handled automatically.\n"
            "Missing values are excluded from calculations."
        )
