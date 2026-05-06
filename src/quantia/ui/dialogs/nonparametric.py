"""Non-parametric Tests Dialog.

Provides Mann-Whitney U, Wilcoxon Signed-Rank, and Kruskal-Wallis tests.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class NonParametricDialog(BaseAnalysisDialog):
    """Dialog for performing non-parametric statistical tests."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Non-Parametric Tests", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        # Test Type Selection
        group_type = QGroupBox("Test Type")
        l_type = QVBoxLayout(group_type)
        
        self.radio_indep = QRadioButton("Independent Samples (Mann-Whitney / Kruskal-Wallis)")
        self.radio_paired = QRadioButton("Paired Samples (Wilcoxon Signed-Rank)")
        self.radio_indep.setChecked(True)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.radio_indep)
        self.btn_group.addButton(self.radio_paired)
        
        l_type.addWidget(self.radio_indep)
        l_type.addWidget(self.radio_paired)
        layout.addWidget(group_type)

        # Stacked widget for different inputs
        self.stacked = QStackedWidget()
        
        # Page 1: Independent
        page_indep = QWidget()
        l_indep = QVBoxLayout(page_indep)
        l_indep.setContentsMargins(0, 0, 0, 0)
        
        self.list_indep_num = QListWidget()
        self.list_indep_num.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        l_indep.addWidget(self._create_selector_row("Numeric Variable:", self.list_indep_num, False))
        
        self.list_indep_cat = QListWidget()
        self.list_indep_cat.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        l_indep.addWidget(self._create_selector_row("Grouping Variable (Categorical):", self.list_indep_cat, False))
        
        # Page 2: Paired
        page_paired = QWidget()
        l_paired = QVBoxLayout(page_paired)
        l_paired.setContentsMargins(0, 0, 0, 0)
        
        self.list_paired_vars = QListWidget()
        self.list_paired_vars.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        l_paired.addWidget(self._create_selector_row("Select Exactly 2 Numeric Variables:", self.list_paired_vars, True))
        
        self.stacked.addWidget(page_indep)
        self.stacked.addWidget(page_paired)
        layout.addWidget(self.stacked)
        
        # Connect radio buttons to flip pages
        self.radio_indep.toggled.connect(lambda: self.stacked.setCurrentIndex(0))
        self.radio_paired.toggled.connect(lambda: self.stacked.setCurrentIndex(1))

    def build_options(self, layout: QVBoxLayout) -> None:
        group_opts = QGroupBox("Options")
        l_opts = QVBoxLayout(group_opts)

        l_opts.addWidget(QLabel("Alternative Hypothesis:"))
        self.cmb_alt = QComboBox()
        self.cmb_alt.addItems(["two-sided", "less", "greater"])
        l_opts.addWidget(self.cmb_alt)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        is_indep = self.radio_indep.isChecked()
        alt = self.cmb_alt.currentText()
        
        if is_indep:
            if not self.list_indep_num.currentItem() or not self.list_indep_cat.currentItem():
                QMessageBox.warning(self, "Missing Input", "Please select both a numeric and a grouping variable.")
                return ""
            num_var = self.list_indep_num.currentItem().text()
            cat_var = self.list_indep_cat.currentItem().text()
            
            code = [
                f"# Non-Parametric Independent Test: {num_var} grouped by {cat_var}",
                "import polars as pl",
                "import pandas as pd",
                "import scipy.stats as stats",
                "import numpy as np",
                "",
                "if isinstance(df, pl.DataFrame):",
                f"    sub = df.select(['{num_var}', '{cat_var}']).drop_nulls().to_pandas()",
                "else:",
                f"    sub = df[['{num_var}', '{cat_var}']].dropna()",
                "",
                f"groups = [group[{repr(num_var)}].values for name, group in sub.groupby('{cat_var}')]",
                f"group_names = [name for name, group in sub.groupby('{cat_var}')]",
                "n_groups = len(groups)",
                "",
                "if n_groups < 2:",
                "    print('Error: Grouping variable must have at least 2 unique levels.')",
                "elif n_groups == 2:",
                f"    # Mann-Whitney U test (2 groups)",
                f"    stat, p = stats.mannwhitneyu(groups[0], groups[1], alternative='{alt}')",
                "    test_name = 'Mann-Whitney U Test'",
                "    stat_name = 'U'",
                "else:",
                f"    # Kruskal-Wallis H test (3+ groups)",
                "    if '" + alt + "' != 'two-sided':",
                "        print('Note: Kruskal-Wallis does not support one-sided alternatives. Using two-sided.')",
                "    stat, p = stats.kruskal(*groups)",
                "    test_name = 'Kruskal-Wallis H Test'",
                "    stat_name = 'H'",
                "",
                "# Calculate medians for reporting",
                "medians = [np.median(g) for g in groups]",
            ]
            
        else:
            selected = [self.list_paired_vars.item(i).text() for i in range(self.list_paired_vars.count()) if self.list_paired_vars.item(i).isSelected()]
            if len(selected) != 2:
                QMessageBox.warning(self, "Missing Input", "Please select exactly 2 numeric variables for a paired test.")
                return ""
            v1, v2 = selected
            
            code = [
                f"# Wilcoxon Signed-Rank Test: {v1} vs {v2}",
                "import polars as pl",
                "import pandas as pd",
                "import scipy.stats as stats",
                "import numpy as np",
                "",
                "if isinstance(df, pl.DataFrame):",
                f"    sub = df.select(['{v1}', '{v2}']).drop_nulls().to_pandas()",
                "else:",
                f"    sub = df[['{v1}', '{v2}']].dropna()",
                "",
                f"stat, p = stats.wilcoxon(sub['{v1}'], sub['{v2}'], alternative='{alt}')",
                "test_name = 'Wilcoxon Signed-Rank Test'",
                "stat_name = 'W'",
                "n_groups = 2",
                f"group_names = ['{v1}', '{v2}']",
                f"medians = [sub['{v1}'].median(), sub['{v2}'].median()]",
            ]

        code += [
            "",
            "if 'show_result' in globals():",
            "    ths = 'padding:8px 12px; font-size:10pt; font-weight:700; color:#475569; border-bottom:2px solid #CBD5E1; text-align:left; background:#F8FAFC;'",
            "    tds = 'padding:8px 12px; font-size:10pt; color:#1E293B; border-bottom:1px solid #E2E8F0; text-align:left;'",
            "    ",
            f"    html = f'<h3 style=\"color:#1E293B; font-family:Segoe UI,sans-serif;\">{{test_name}}</h3>'",
            "    ",
            "    # Summary Card",
            "    p_formatted = f'<span style=\"color:#16A34A; font-weight:bold;\">&lt; 0.001</span>' if p < 0.001 else f'<span style=\"color:#DC2626; font-weight:bold;\">{{p:.4f}}</span>'",
            "    html += f'<div style=\"padding:12px 16px; background:#F0FDF4 if p < 0.05 else #FEF2F2; border-left:4px solid #22C55E if p < 0.05 else #EF4444; border-radius:4px; margin-bottom:20px;\">'",
            f"    html += f'<b>{{stat_name}}</b> = {{stat:.4f}} &nbsp;|&nbsp; <b>p-value</b> = {{p_formatted}} &nbsp;|&nbsp; <b>Alternative:</b> {alt}'",
            "    if p < 0.05:",
            "        html += '<br><span style=\"color:#166534; font-size:9pt; margin-top:4px; display:inline-block;\">Significant difference between distributions.</span>'",
            "    else:",
            "        html += '<br><span style=\"color:#991B1B; font-size:9pt; margin-top:4px; display:inline-block;\">No significant difference between distributions.</span>'",
            "    html += '</div>'",
            "    ",
            "    # Group Medians Table",
            "    html += '<h4 style=\"margin-bottom:8px; color:#334155;\">Group Medians</h4>'",
            "    html += '<table style=\"border-collapse:collapse; min-width:300px;\"><tr>'",
            "    html += f'<th style=\"{ths}\">Group</th><th style=\"{ths}\">Median</th></tr>'",
            "    for name, med in zip(group_names, medians):",
            "        html += f'<tr><td style=\"{tds}\"><b>{{name}}</b></td><td style=\"{tds}\">{{med:.4f}}</td></tr>'",
            "    html += '</table>'",
            "    ",
            "    show_result(test_name, html)",
            "else:",
            "    print(f'{test_name}: {stat_name}={stat:.4f}, p={p:.4e}')",
            "    for name, med in zip(group_names, medians):",
            "        print(f'  Median of {name}: {med:.4f}')"
        ]

        return "\n".join(code)
