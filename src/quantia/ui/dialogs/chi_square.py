"""Chi-Square Test of Independence Dialog.

Computes a cross-tabulation and performs a Chi-Square test for independence
between two categorical variables.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QGroupBox,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class ChiSquareDialog(BaseAnalysisDialog):
    """Dialog for performing a Chi-Square test of independence."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Chi-Square Test", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_row = QListWidget()
        self.list_row.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(
            self._create_selector_row(
                "Row Variable (Categorical):", self.list_row, multi_select=False
            )
        )

        self.list_col = QListWidget()
        self.list_col.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(
            self._create_selector_row(
                "Column Variable (Categorical):", self.list_col, multi_select=False
            )
        )

    def build_options(self, layout: QVBoxLayout) -> None:
        group_opts = QGroupBox("Options")
        l_opts = QVBoxLayout(group_opts)

        self.chk_expected = QCheckBox("Show expected frequencies in table")
        self.chk_expected.setChecked(False)
        l_opts.addWidget(self.chk_expected)
        
        self.chk_margins = QCheckBox("Show row and column totals (margins)")
        self.chk_margins.setChecked(True)
        l_opts.addWidget(self.chk_margins)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        row_var = ""
        col_var = ""
        
        if self.list_row.currentItem():
            row_var = self.list_row.currentItem().text()
        if self.list_col.currentItem():
            col_var = self.list_col.currentItem().text()

        if not row_var or not col_var:
            QMessageBox.warning(self, "Missing Input", "Please select both a Row and Column variable.")
            return ""
            
        if row_var == col_var:
            QMessageBox.warning(self, "Invalid Input", "Row and Column variables must be different.")
            return ""

        show_expected = self.chk_expected.isChecked()
        show_margins = self.chk_margins.isChecked()

        code = [
            f"# Chi-Square Test of Independence: {row_var} vs {col_var}",
            "import polars as pl",
            "import pandas as pd",
            "from scipy.stats import chi2_contingency",
            "",
            "if isinstance(df, pl.DataFrame):",
            f"    sub = df.select(['{row_var}', '{col_var}']).drop_nulls().to_pandas()",
            "else:",
            f"    sub = df[['{row_var}', '{col_var}']].dropna()",
            "",
            f"crosstab = pd.crosstab(sub['{row_var}'], sub['{col_var}'])",
            "",
            "chi2, p, dof, expected = chi2_contingency(crosstab)",
            "",
            "if 'show_result' in globals():",
            "    ths = 'padding:8px 12px; font-size:10pt; font-weight:700; color:#475569; border-bottom:2px solid #CBD5E1; text-align:right; background:#F8FAFC;'",
            "    tds = 'padding:8px 12px; font-size:10pt; color:#1E293B; border-bottom:1px solid #E2E8F0; text-align:right;'",
            "    tds_bold = 'padding:8px 12px; font-size:10pt; font-weight:600; color:#1E293B; border-bottom:1px solid #E2E8F0; text-align:left; background:#F8FAFC;'",
            "    ",
            f"    html = f'<h3 style=\"color:#1E293B; font-family:Segoe UI,sans-serif;\">Chi-Square Test: {row_var} \u00d7 {col_var}</h3>'",
            "    ",
            "    # Build summary card",
            "    p_formatted = f'<span style=\"color:#16A34A; font-weight:bold;\">&lt; 0.001</span>' if p < 0.001 else f'<span style=\"color:#DC2626; font-weight:bold;\">{p:.4f}</span>'",
            "    html += f'<div style=\"padding:12px 16px; background:#F0FDF4 if {p < 0.05} else #FEF2F2; border-left:4px solid #22C55E if {p < 0.05} else #EF4444; border-radius:4px; margin-bottom:20px;\">'",
            "    html += f'<b>\u03c7\u00b2</b> = {chi2:.4f} &nbsp;|&nbsp; <b>df</b> = {dof} &nbsp;|&nbsp; <b>p-value</b> = {p_formatted}'",
            "    if p < 0.05:",
            "        html += '<br><span style=\"color:#166534; font-size:9pt; margin-top:4px; display:inline-block;\">Significant relationship between the variables.</span>'",
            "    else:",
            "        html += '<br><span style=\"color:#991B1B; font-size:9pt; margin-top:4px; display:inline-block;\">No significant relationship between the variables.</span>'",
            "    html += '</div>'",
            "    ",
            "    # Build Contingency Table HTML",
            "    html += '<h4 style=\"margin-bottom:8px; color:#334155;\">Contingency Table (Observed' + (' / Expected' if " + str(show_expected) + " else '') + ')</h4>'",
            "    html += '<table style=\"border-collapse:collapse; min-width:300px;\"><tr>'",
            "    html += f'<th style=\"{ths}\"></th>'",
            "    for col in crosstab.columns:",
            "        html += f'<th style=\"{ths}\">{col}</th>'",
            "    if " + str(show_margins) + ":",
            "        html += f'<th style=\"{ths} border-left:2px solid #E2E8F0;\">Total</th>'",
            "    html += '</tr>'",
            "    ",
            "    for i, row_idx in enumerate(crosstab.index):",
            "        html += '<tr>'",
            "        html += f'<td style=\"{tds_bold}\">{row_idx}</td>'",
            "        row_total = 0",
            "        for j, col_idx in enumerate(crosstab.columns):",
            "            obs = crosstab.iloc[i, j]",
            "            row_total += obs",
            "            cell_html = f'{obs}'",
            "            if " + str(show_expected) + ":",
            "                exp = expected[i, j]",
            "                cell_html += f'<br><span style=\"color:#94A3B8; font-size:8.5pt;\">({exp:.1f})</span>'",
            "            html += f'<td style=\"{tds}\">{cell_html}</td>'",
            "        if " + str(show_margins) + ":",
            "            html += f'<td style=\"{tds} border-left:2px solid #E2E8F0; font-weight:600;\">{row_total}</td>'",
            "        html += '</tr>'",
            "    ",
            "    if " + str(show_margins) + ":",
            "        html += '<tr>'",
            "        html += f'<td style=\"{tds_bold} border-top:2px solid #E2E8F0;\">Total</td>'",
            "        for j, col_idx in enumerate(crosstab.columns):",
            "            col_total = crosstab.iloc[:, j].sum()",
            "            html += f'<td style=\"{tds} border-top:2px solid #E2E8F0; font-weight:600;\">{col_total}</td>'",
            "        html += f'<td style=\"{tds} border-top:2px solid #E2E8F0; border-left:2px solid #E2E8F0; font-weight:bold; color:#0F172A;\">{crosstab.values.sum()}</td>'",
            "        html += '</tr>'",
            "        ",
            "    html += '</table>'",
            "    ",
            "    show_result('Chi-Square Test', html)",
            "else:",
            "    print(f'Chi-Square: {chi2:.4f}, p: {p:.4e}')",
            "    print('Observed frequencies:')",
            "    print(crosstab.to_string())"
        ]

        return "\n".join(code)
