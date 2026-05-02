"""ANOVA Model Comparison Dialog.

Allows comparing two nested OLS regression models using an F-test (ANOVA).
User selects a single Dependent Variable (Y), and independent variables
for Model 1 (Reduced) and Model 2 (Full).
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class AnovaModelComparisonDialog(BaseAnalysisDialog):
    """Dialog for comparing two nested OLS models via ANOVA."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("ANOVA Model Comparison", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        """Add Dependent and Independent Variable selectors for two models."""
        self.list_dependent = QListWidget()
        self.list_dependent.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        row_dep = self._create_selector_row("Dependent Variable (Y) for both models:", self.list_dependent, multi_select=False)
        layout.addWidget(row_dep)

        # Horizontal layout for Model 1 and Model 2 X variables
        models_layout = QHBoxLayout()
        
        # Model 1 (Baseline)
        group_m1 = QGroupBox("Baseline Model (Simpler)")
        l_m1 = QVBoxLayout(group_m1)
        self.cmb_m1_history = QComboBox()
        self.cmb_m1_history.addItem("Select previous model...")
        self.cmb_m1_history.currentIndexChanged.connect(lambda idx: self._apply_history(idx, self.cmb_m1_history, self.list_m1_x))
        l_m1.addWidget(self.cmb_m1_history)

        self.list_m1_x = QListWidget()
        self.list_m1_x.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_m1_x.addItems(list(self._df.columns))
        l_m1.addWidget(self.list_m1_x)
        models_layout.addWidget(group_m1)

        # Model 2 (Expanded)
        group_m2 = QGroupBox("Expanded Model (More Variables)")
        l_m2 = QVBoxLayout(group_m2)
        self.cmb_m2_history = QComboBox()
        self.cmb_m2_history.addItem("Select previous model...")
        self.cmb_m2_history.currentIndexChanged.connect(lambda idx: self._apply_history(idx, self.cmb_m2_history, self.list_m2_x))
        l_m2.addWidget(self.cmb_m2_history)

        self.list_m2_x = QListWidget()
        self.list_m2_x.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_m2_x.addItems(list(self._df.columns))
        l_m2.addWidget(self.list_m2_x)
        models_layout.addWidget(group_m2)

        layout.addLayout(models_layout)

    def load_history(self, script_text: str, model_history: list = None) -> None:
        import re
        
        seen_models = set()
        
        # 1. Add explicitly tracked models from execution history (catches stepwise variables!)
        if model_history:
            for y_name, x_names in reversed(model_history): # latest first
                indep_str = ", ".join(x_names)
                display_text = f"Executed: {y_name} ~ {indep_str}"
                key = (y_name, tuple(sorted(x_names)))
                if key not in seen_models:
                    seen_models.add(key)
                    self.cmb_m1_history.addItem(display_text, (y_name, x_names))
                    self.cmb_m2_history.addItem(display_text, (y_name, x_names))

        # 2. Add parsed headers from script editor (catches models generated but not executed)
        pattern = re.compile(r"# (?:OLS|Logistic) Regression: (.+?) ~ (.+)")
        matches = pattern.findall(script_text)
        
        for dep_var, indep_str in reversed(matches):
            indep_vars = [v.strip() for v in indep_str.split(",")]
            key = (dep_var, tuple(sorted(indep_vars)))
            if key not in seen_models:
                seen_models.add(key)
                display_text = f"Script: {dep_var} ~ {indep_str}"
                self.cmb_m1_history.addItem(display_text, (dep_var, indep_vars))
                self.cmb_m2_history.addItem(display_text, (dep_var, indep_vars))

    def _apply_history(self, idx: int, cmb: QComboBox, list_widget: QListWidget) -> None:
        if idx == 0:
            return  # The placeholder item
            
        data = cmb.itemData(idx)
        if not data:
            return
            
        dep_var, indep_vars = data
        
        # Set dependent variable
        items = self.list_dependent.findItems(dep_var, Qt.MatchFlag.MatchExactly)
        if items:
            self.list_dependent.setCurrentItem(items[0])
            
        # Select independent variables
        list_widget.clearSelection()
        for var in indep_vars:
            items = list_widget.findItems(var, Qt.MatchFlag.MatchExactly)
            if items:
                items[0].setSelected(True)

    def build_options(self, layout: QVBoxLayout) -> None:
        """Add options for the comparison."""
        group_opts = QGroupBox("Options")
        l_opts = QVBoxLayout(group_opts)

        self.chk_intercept = QCheckBox("Include Intercept in both models")
        self.chk_intercept.setChecked(True)
        l_opts.addWidget(self.chk_intercept)
        
        lbl = QLabel(
            "Note: The Baseline Model should be a subset of the Expanded Model "
            "(nested models) for the ANOVA F-test to be statistically valid."
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #64748B; font-style: italic; margin-top: 8px;")
        l_opts.addWidget(lbl)

        layout.addWidget(group_opts)

    def generate_code(self) -> str:
        dep_var = ""
        if self.list_dependent.currentItem():
            dep_var = self.list_dependent.currentItem().text()

        m1_vars = [self.list_m1_x.item(i).text() for i in range(self.list_m1_x.count()) if self.list_m1_x.item(i).isSelected()]
        m2_vars = [self.list_m2_x.item(i).text() for i in range(self.list_m2_x.count()) if self.list_m2_x.item(i).isSelected()]

        if not dep_var:
            QMessageBox.warning(self, "Missing Input", "Please select a Dependent Variable (Y).")
            return ""
        if not m1_vars:
            QMessageBox.warning(self, "Missing Input", "Please select at least one independent variable for Model 1.")
            return ""
        if not m2_vars:
            QMessageBox.warning(self, "Missing Input", "Please select at least one independent variable for Model 2.")
            return ""

        include_intercept = self.chk_intercept.isChecked()

        m1_str = ", ".join(f"'{v}'" for v in m1_vars)
        m2_str = ", ".join(f"'{v}'" for v in m2_vars)
        
        # Combine all needed columns to drop NAs consistently
        all_vars = list(set([dep_var] + m1_vars + m2_vars))
        all_vars_str = ", ".join(f"'{v}'" for v in all_vars)

        code = [
            f"# ANOVA Model Comparison",
            f"# Model 1 (Baseline): {dep_var} ~ {', '.join(m1_vars)}",
            f"# Model 2 (Expanded): {dep_var} ~ {', '.join(m2_vars)}",
            "import statsmodels.api as sm",
            "from statsmodels.stats.anova import anova_lm",
            "import pandas as pd",
            "",
            "# Prepare dataset (drop missing values across all used columns to ensure comparable samples)",
            f"model_data = df[[{all_vars_str}]].dropna()",
            f"y = model_data['{dep_var}']",
            "",
            "# Fit Model 1 (Baseline)",
            f"X1 = model_data[[{m1_str}]]",
            "X1 = pd.get_dummies(X1, drop_first=True, dtype=float)",
            "if " + str(include_intercept) + ":",
            "    X1 = sm.add_constant(X1)",
            "model1 = sm.OLS(y, X1).fit()",
            "",
            "# Fit Model 2 (Expanded)",
            f"X2 = model_data[[{m2_str}]]",
            "X2 = pd.get_dummies(X2, drop_first=True, dtype=float)",
            "if " + str(include_intercept) + ":",
            "    X2 = sm.add_constant(X2)",
            "model2 = sm.OLS(y, X2).fit()",
            "",
            "# Perform ANOVA",
            "anova_results = anova_lm(model1, model2)",
            "",
            "# Format results",
            "if 'show_result' in globals():",
            "    # Clean up ANOVA table for display",
            "    res_df = anova_results.copy()",
            "    res_df.index = ['Model 1 (Baseline)', 'Model 2 (Expanded)']",
            "    res_df.index.name = 'Model'",
            "    res_df = res_df.reset_index()",
            "    ",
            "    # Format numeric columns safely",
            "    if 'ss_diff' in res_df.columns: res_df['ss_diff'] = res_df['ss_diff'].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '')",
            "    if 'F' in res_df.columns: res_df['F'] = res_df['F'].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '')",
            "    if 'Pr(>F)' in res_df.columns:",
            "        res_df['p-value'] = res_df['Pr(>F)'].apply(lambda x: f'{x:.4e}' if pd.notna(x) and x < 0.001 else (f'{x:.4f}' if pd.notna(x) else ''))",
            "        res_df = res_df.drop('Pr(>F)', axis=1)",
            "    ",
            "    # Build HTML table manually",
            "    ths = 'padding:8px 12px; font-size:10pt; font-weight:700; color:#475569; border-bottom:2px solid #E2E8F0; text-align:left; background:#F8FAFC;'",
            "    tds = 'padding:8px 12px; font-size:10pt; color:#1E293B; border-bottom:1px solid #F1F5F9;'",
            "    ",
            "    html = '<h3 style=\"color:#1E293B; font-family:Segoe UI,sans-serif;\">ANOVA Model Comparison (F-test)</h3>'",
            "    html += '<table style=\"width:100%; border-collapse:collapse; margin-top:10px;\"><tr>'",
            "    for col in res_df.columns:",
            "        html += f'<th style=\"{ths}\">{col}</th>'",
            "    html += '</tr>'",
            "    ",
            "    for _, row in res_df.iterrows():",
            "        html += '<tr>'",
            "        for val in row:",
            "            html += f'<td style=\"{tds}\">{val}</td>'",
            "        html += '</tr>'",
            "    html += '</table>'",
            "    ",
            "    html += '<div style=\"margin-top:16px; padding:12px; background:#F0FDF4; border-left:4px solid #22C55E; color:#166534; font-family:Segoe UI,sans-serif;\">'",
            "    p_val = anova_results['Pr(>F)'].iloc[1]",
            "    if pd.notna(p_val) and p_val < 0.05:",
            "        html += f'<b>Significant Difference (p = {p_val:.4f}):</b> The Expanded Model provides a significantly better fit to the data than the Baseline Model.'",
            "    elif pd.notna(p_val):",
            "        html += f'<b>No Significant Difference (p = {p_val:.4f}):</b> The Expanded Model does not significantly improve the fit over the Baseline Model.'",
            "    html += '</div>'",
            "    ",
            "    show_result('ANOVA Comparison', html)",
            "else:",
            "    print(anova_results.to_string())"
        ]

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "ANOVA Model Comparison",
            "This dialog compares two OLS regression models using an ANOVA F-test.\n\n"
            "1. Select the shared Dependent Variable (Y).\n"
            "2. Select independent variables for the Baseline Model (e.g., control variables).\n"
            "3. Select independent variables for the Expanded Model (e.g., controls + new predictors).\n\n"
            "The test will determine if the additional variables in the Expanded Model significantly improve the model fit compared to the Baseline Model."
        )
