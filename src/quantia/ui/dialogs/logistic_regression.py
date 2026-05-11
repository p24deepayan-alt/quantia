"""Logistic Regression Dialog.

Allows selecting a binary dependent variable (Y) and one or more independent variables (X).
Generates code using scikit-learn LogisticRegression to perform multi-threaded regression.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import itertools

from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from quantia.ui.central.plotly_styles import generate_plotly_style_code
from quantia.ui.dialogs.base import BaseAnalysisDialog
from quantia.core.settings import SettingsManager, ComputeMode


class LogisticRegressionDialog(BaseAnalysisDialog):
    """Dialog for performing Logistic Regression."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Logistic Regression", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        """Add Dependent and Independent Variable selectors."""
        self.list_dependent = QListWidget()
        row_dep = self._create_selector_row("Dependent Variable (Y, binary):", self.list_dependent, multi_select=False)
        layout.addWidget(row_dep)

        self.list_independent = QListWidget()
        row_indep = self._create_selector_row("Independent Variables (X):", self.list_independent, multi_select=True)
        layout.addWidget(row_indep)

        # Interaction Terms Section
        lbl_inter = QLabel("Interaction Terms (X1 * X2):")
        layout.addWidget(lbl_inter)
        
        inter_container = QWidget()
        h_inter = QHBoxLayout(inter_container)
        h_inter.setContentsMargins(0,0,0,0)
        
        self.list_interactions = QListWidget()
        h_inter.addWidget(self.list_interactions)
        
        btn_layout = QVBoxLayout()
        self.btn_add_inter = QPushButton("Add 2-Way\nInteractions")
        self.btn_add_inter.clicked.connect(self._add_interaction)
        self.btn_remove_inter = QPushButton("Remove")
        self.btn_remove_inter.clicked.connect(self._remove_interaction)
        btn_layout.addWidget(self.btn_add_inter)
        btn_layout.addWidget(self.btn_remove_inter)
        btn_layout.addStretch()
        h_inter.addLayout(btn_layout)
        
        layout.addWidget(inter_container)

    def _add_interaction(self) -> None:
        items = self.list_independent.selectedItems()
        if len(items) < 2:
            QMessageBox.warning(self, "Invalid Selection", "Please select at least 2 variables in the Independent Variables (X) list to create an interaction term.")
            return
            
        vars_selected = [item.text() for item in items]
        pairs = list(itertools.combinations(vars_selected, 2))
        
        existing = [self.list_interactions.item(i).text() for i in range(self.list_interactions.count())]
        
        for p1, p2 in pairs:
            term1 = f"{p1} * {p2}"
            term2 = f"{p2} * {p1}"
            if term1 not in existing and term2 not in existing:
                self.list_interactions.addItem(term1)
                
    def _remove_interaction(self) -> None:
        for item in self.list_interactions.selectedItems():
            self.list_interactions.takeItem(self.list_interactions.row(item))

    def build_options(self, layout: QVBoxLayout) -> None:
        """Add options for the regression."""
        group_model = QGroupBox("Model Options")
        l_opts = QVBoxLayout(group_model)

        self.chk_intercept = QCheckBox("Include Intercept (Constant)")
        self.chk_intercept.setChecked(True)
        l_opts.addWidget(self.chk_intercept)
        
        l_opts.addWidget(QLabel("Classification Threshold (0 to 1):"))
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(0.01, 0.99)
        self.spin_threshold.setSingleStep(0.05)
        self.spin_threshold.setValue(0.50)
        l_opts.addWidget(self.spin_threshold)

        layout.addWidget(group_model)

        # Stepwise Selection
        group_step = QGroupBox("Model Selection")
        l_step = QVBoxLayout(group_step)
        
        self.chk_stepwise = QCheckBox("Auto-select best model (Stepwise)")
        l_step.addWidget(self.chk_stepwise)
        
        l_step.addWidget(QLabel("Criterion:"))
        self.cmb_criterion = QComboBox()
        self.cmb_criterion.addItems(["AIC (Bidirectional)", "BIC (Bidirectional)", "p-value (Bidirectional)"])
        l_step.addWidget(self.cmb_criterion)
        
        self.cmb_criterion.setEnabled(False)
        self.chk_stepwise.toggled.connect(self.cmb_criterion.setEnabled)
        
        layout.addWidget(group_step)

        # Diagnostic Plots
        group_plots = QGroupBox("Diagnostic Plots")
        l_plots = QVBoxLayout(group_plots)
        self.chk_plots = QCheckBox("Generate ROC Curve & Confusion Matrix")
        l_plots.addWidget(self.chk_plots)

        l_plots.addWidget(QLabel("Plot Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        self.cmb_style.setEnabled(False)
        self.chk_plots.toggled.connect(self.cmb_style.setEnabled)
        l_plots.addWidget(self.cmb_style)

        layout.addWidget(group_plots)

    def generate_code(self) -> str:
        """Generate the Python code to run the logistic regression."""
        dep_var = self.list_dependent.item(0).text() if self.list_dependent.count() > 0 else None
        indep_vars = [self.list_independent.item(i).text() for i in range(self.list_independent.count())]
        inter_vars = [self.list_interactions.item(i).text() for i in range(self.list_interactions.count())]

        if not dep_var:
            QMessageBox.warning(self, "Missing Input", "Please select a Dependent Variable (Y).")
            return ""
        if not indep_vars and not inter_vars:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Independent Variable (X).")
            return ""

        # Enforce marginality at data level: constituents must be in indep_vars
        for ivar in inter_vars:
            v1, v2 = ivar.split(' * ')
            if v1 not in indep_vars: indep_vars.append(v1)
            if v2 not in indep_vars: indep_vars.append(v2)

        include_intercept = self.chk_intercept.isChecked()
        threshold = self.spin_threshold.value()
        stepwise = self.chk_stepwise.isChecked()
        criterion = self.cmb_criterion.currentText()
        show_plots = self.chk_plots.isChecked()
        plot_style = self.cmb_style.currentText()

        indep_str = ", ".join(f"'{v}'" for v in indep_vars)
        inter_str = ", ".join(f"'{v}'" for v in inter_vars)

        code = [
            f"# Logistic Regression: {dep_var} ~ {', '.join(indep_vars + inter_vars)}",
            "import statsmodels.api as sm",
            "import pandas as pd",
            "import polars as pl",
            "import numpy as np",
            "import warnings",
            "warnings.simplefilter('ignore', RuntimeWarning)",
            "",
            "# Prepare data",
            f"model_vars = ['{dep_var}', {indep_str}]",
            "if isinstance(df, pl.DataFrame):",
            "    model_data = df.select(model_vars).drop_nulls().to_pandas()",
            "else:",
            "    model_data = df[model_vars].dropna()",
            f"y_raw = model_data['{dep_var}']",
            "if pd.api.types.is_bool_dtype(y_raw):",
            "    y = y_raw.astype(int)",
            "elif y_raw.dtype == object or pd.api.types.is_string_dtype(y_raw):",
            "    y = y_raw.str.lower().str.strip().map({'yes': 1, 'no': 0})",
            "else:",
            "    y = pd.to_numeric(y_raw, errors='coerce')",
            "y = y.dropna()",
            "if not set(y.unique()).issubset({0, 1}):",
            "    print('Error: Dependent variable must be binary (0 and 1, True/False, or Yes/No).')",
            "    if 'show_result' in globals():",
            "        show_result('Logistic Regression Error', '<h3 style=\"color:red; font-family:sans-serif;\">Error: Dependent variable must be binary (0 and 1, True/False, or Yes/No).</h3>')",
            "    raise ValueError('Dependent variable must be binary (0 and 1, True/False, or Yes/No).')",
            f"X_all = model_data.loc[y.index, [{indep_str}]]",
            "X_all = pd.get_dummies(X_all, drop_first=True, dtype=float)",
        ]

        if inter_vars or stepwise:
            code.append("")
            code.append("# Group dummy columns by their original categorical variable")
            code.append(f"original_vars = [{indep_str}]")
            code.append("var_groups = {}")
            code.append("for v in original_vars:")
            code.append("    if v in X_all.columns:")
            code.append("        var_groups[v] = [v]")
            code.append("    else:")
            code.append("        var_groups[v] = [c for c in X_all.columns if c.startswith(f'{v}_')]")
            code.append("")

        if inter_vars:
            code.append("# Create interaction columns")
            code.append(f"interaction_vars = [{inter_str}]")
            code.append("for ivar in interaction_vars:")
            code.append("    v1, v2 = ivar.split(' * ')")
            code.append("    inter_cols = []")
            code.append("    for c1 in var_groups[v1]:")
            code.append("        for c2 in var_groups[v2]:")
            code.append("            col_name = f'{c1}:{c2}'")
            code.append("            X_all[col_name] = X_all[c1] * X_all[c2]")
            code.append("            inter_cols.append(col_name)")
            code.append("    var_groups[ivar] = inter_cols")
            code.append("")

        if stepwise:
            code.append("# Perform Bidirectional Stepwise Selection (Optimized via NumPy)")
            if inter_vars:
                code.append("available_vars = original_vars + interaction_vars")
            else:
                code.append("available_vars = original_vars")
            
            code.append("X_all_np = X_all.values")
            if include_intercept:
                code.append("X_all_np = np.column_stack([np.ones(X_all_np.shape[0]), X_all_np])")
                code.append("col_map = {col: i + 1 for i, col in enumerate(X_all.columns)}")
                code.append("const_idx = [0]")
            else:
                code.append("col_map = {col: i for i, col in enumerate(X_all.columns)}")
                code.append("const_idx = []")
                
            code.append("current_vars = []") 

            code.append("while True:")
            code.append("    changed = False")

            if "p-value" in criterion:
                code.append("    curr_indices = const_idx + [col_map[c] for ov in current_vars for c in var_groups[ov]]")
                code.append(f"    X_curr = X_all_np[:, curr_indices] if len(curr_indices) > len(const_idx) else None")
                code.append("    try:")
                code.append(f"        res_curr = sm.Logit(y, X_curr).fit(method='bfgs', maxiter=250, disp=0) if X_curr is not None else None")
                code.append("    except:")
                code.append("        res_curr = None")
                code.append("    ")
                code.append("    # 1. Try adding the most significant variable")
                code.append("    candidates_add = []")
                code.append("    for v in available_vars:")
                code.append("        if v not in current_vars:")
                code.append("            if ' * ' in v:")
                code.append("                p1, p2 = v.split(' * ')")
                code.append("                if p1 in current_vars and p2 in current_vars:")
                code.append("                    candidates_add.append(v)")
                code.append("            else:")
                code.append("                candidates_add.append(v)")
                code.append("    best_p = 0.05")
                code.append("    best_v = None")
                code.append("    for v in candidates_add:")
                code.append("        test_indices = curr_indices + [col_map[c] for c in var_groups[v]]")
                code.append(f"        test_X = X_all_np[:, test_indices]")
                code.append("        try:")
                code.append(f"            res_test = sm.Logit(y, test_X).fit(method='bfgs', maxiter=250, disp=0)")
                code.append("            new_dummy_indices = list(range(len(test_indices) - len(var_groups[v]), len(test_indices)))")
                code.append("            p = np.min([res_test.pvalues.iloc[i] for i in new_dummy_indices])")
                code.append("            if p < best_p:")
                code.append("                best_p = p")
                code.append("                best_v = v")
                code.append("                changed = 'add'")
                code.append("        except:")
                code.append("            pass")
                code.append("    ")
                code.append("    if changed == 'add':")
                code.append("        current_vars.append(best_v)")
                code.append("        curr_indices = const_idx + [col_map[c] for ov in current_vars for c in var_groups[ov]]")
                code.append(f"        print(f'Added {{best_v}} (p={{best_p:.4f}})')")
                code.append("        continue")
                code.append("    ")
                code.append("    # 2. Try dropping the least significant variable")
                code.append("    if len(current_vars) > 0:")
                code.append("        max_p = -1")
                code.append("        worst_v = None")
                code.append("        for v in current_vars:")
                code.append("            can_drop = True")
                code.append("            for cv in current_vars:")
                code.append("                if ' * ' in cv and v in cv.split(' * '):")
                code.append("                    can_drop = False")
                code.append("                    break")
                code.append("            if not can_drop:")
                code.append("                continue")
                code.append("            ")
                code.append("            # Identify dummy indices for this variable")
                code.append("            start_idx = len(const_idx)")
                code.append("            for cv in current_vars:")
                code.append("                dummy_range = range(start_idx, start_idx + len(var_groups[cv]))")
                code.append("                if cv == v:")
                code.append("                    p = np.max([res_curr.pvalues.iloc[i] for i in dummy_range])")
                code.append("                    break")
                code.append("                start_idx += len(var_groups[cv])")
                code.append("            ")
                code.append("            if p > max_p:")
                code.append("                max_p = p")
                code.append("                worst_v = v")
                code.append("        ")
                code.append("        if max_p >= 0.05:")
                code.append("            current_vars.remove(worst_v)")
                code.append(f"            print(f'Dropped {{worst_v}} (p={{max_p:.4f}})')")
                code.append("            changed = 'drop'")
                code.append("            continue")
            else:
                metric = "aic" if "AIC" in criterion else "bic"
                code.append("    curr_indices = const_idx + [col_map[c] for ov in current_vars for c in var_groups[ov]]")
                code.append(f"    X_curr = X_all_np[:, curr_indices] if len(curr_indices) > len(const_idx) else None")
                code.append("    try:")
                code.append(f"        best_score = sm.Logit(y, X_curr).fit(method='bfgs', maxiter=250, disp=0).{metric} if X_curr is not None else np.inf")
                code.append("    except:")
                code.append("        best_score = np.inf")
                code.append("    ")
                code.append("    # 1. Try adding a variable")
                code.append("    candidates_add = []")
                code.append("    for v in available_vars:")
                code.append("        if v not in current_vars:")
                code.append("            if ' * ' in v:")
                code.append("                p1, p2 = v.split(' * ')")
                code.append("                if p1 in current_vars and p2 in current_vars:")
                code.append("                    candidates_add.append(v)")
                code.append("            else:")
                code.append("                candidates_add.append(v)")
                code.append("    best_v = None")
                code.append("    for v in candidates_add:")
                code.append("        test_indices = curr_indices + [col_map[c] for c in var_groups[v]]")
                code.append(f"        test_X = X_all_np[:, test_indices]")
                code.append("        try:")
                code.append(f"            score = sm.Logit(y, test_X).fit(method='bfgs', maxiter=250, disp=0).{metric}")
                code.append("            if score < best_score:")
                code.append("                best_score = score")
                code.append("                best_v = v")
                code.append("                changed = 'add'")
                code.append("        except:")
                code.append("            pass")
                code.append("    ")
                code.append("    if changed == 'add':")
                code.append("        current_vars.append(best_v)")
                code.append("        curr_indices = const_idx + [col_map[c] for ov in current_vars for c in var_groups[ov]]")
                code.append(f"        print(f'Added {{best_v}} ({{best_score:.2f}})')")
                code.append("        continue")
                code.append("        ")
                code.append("    # 2. Try dropping a variable")
                code.append("    if len(current_vars) > 1:")
                code.append("        for v in current_vars:")
                code.append("            can_drop = True")
                code.append("            for cv in current_vars:")
                code.append("                if ' * ' in cv and v in cv.split(' * '):")
                code.append("                    can_drop = False")
                code.append("                    break")
                code.append("            if not can_drop:")
                code.append("                continue")
                code.append("            test_vars = [cv for cv in current_vars if cv != v]")
                code.append("            test_indices = const_idx + [col_map[c] for ov in test_vars for c in var_groups[ov]]")
                code.append(f"            test_X = X_all_np[:, test_indices]")
                code.append("            try:")
                code.append(f"                score = sm.Logit(y, test_X).fit(method='bfgs', maxiter=250, disp=0).{metric}")
                code.append("                if score < best_score:")
                code.append("                    best_score = score")
                code.append("                    best_v = v")
                code.append("                    changed = 'drop'")
                code.append("            except:")
                code.append("                pass")
                code.append("        if changed == 'drop':")
                code.append("            current_vars.remove(best_v)")
                code.append("            curr_indices = const_idx + [col_map[c] for ov in current_vars for c in var_groups[ov]]")
                code.append(f"            print(f'Dropped {{best_v}} ({{best_score:.2f}})')")
                code.append("            continue")
            code.append("    break")
            code.append("final_cols = [c for ov in current_vars for c in var_groups[ov]]")
            code.append("X = X_all[final_cols] if final_cols else pd.DataFrame(index=X_all.index)")

        else:
            code.append("if 'var_groups' in locals() or 'var_groups' in globals():")
            code.append("    final_cols = [c for ov in (indep_vars + interaction_vars if 'interaction_vars' in locals() else indep_vars) for c in var_groups[ov]]")
            code.append("    X = X_all[final_cols] if final_cols else pd.DataFrame(index=X_all.index)")
            code.append("else:")
            code.append("    X = X_all")

        code.append("")
        if include_intercept:
            code.append("X = sm.add_constant(X, has_constant='add')")

        code.append("")
        code.append(f"results = sm.Logit(y, X).fit(method='bfgs', maxiter=1000, disp=0)")

        code.append("")
        code.append("if 'show_result' in globals():")
        code.append("    ci = results.conf_int()")
        code.append("    odds_ratios = np.exp(results.params)")
        code.append("")
        code.append("    # ── Equation ──")
        code.append("    eq_terms = []")
        code.append("    for var, coef in results.params.items():")
        code.append("        if var == 'const':")
        code.append("            eq_terms.append(f'{coef:.4f}')")
        code.append("        else:")
        code.append("            sign = '+' if coef >= 0 else '-'")
        code.append("            eq_terms.append(f'{sign} {abs(coef):.4f}\\u00b7{var}')")
        code.append(f"    eq_str = ' '.join(eq_terms)")
        code.append("")
        code.append("    eq_html = f'''<table style=\"width:100%; margin-bottom:16px;\">")
        code.append("    <tr><td style=\"background:#EEF2FF; border-left:3px solid #6366F1; padding:12px 16px;")
        code.append(f"        font-family:Cambria,Georgia,serif; font-size:12pt; color:#1E293B;\"><b style=\"color:#4338CA;\">Logit(P({dep_var}=1))</b> = {{eq_str}}</td></tr></table>'''")
        code.append("")
        code.append("    # ── Model Summary Card ──")
        code.append("    sc = 'padding:10px 14px; background:#F8FAFC; border:1px solid #F1F5F9; text-align:center;'")
        code.append("    lb = 'font-size:8pt; color:#94A3B8; font-weight:600;'")
        code.append("    vl = 'font-size:13pt; font-weight:700; color:#111827; font-family:Consolas,monospace;'")
        code.append("    stats_html = f'''<table style=\"width:100%; margin-bottom:16px; border-collapse:collapse;\">")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">PSEUDO R-SQUARED</div><div style=\"{vl}\">{results.prsquared:.4f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">LOG-LIKELIHOOD</div><div style=\"{vl}\">{results.llf:.2f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">LL-NULL</div><div style=\"{vl}\">{results.llnull:.2f}</div></td>")
        code.append("    </tr>")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">AIC</div><div style=\"{vl}\">{results.aic:.1f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">BIC</div><div style=\"{vl}\">{results.bic:.1f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">LLR P-VALUE</div><div style=\"{vl}\">{results.llr_pvalue:.2e}</div></td>")
        code.append("    </tr>")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">OBSERVATIONS</div><div style=\"{vl}\">{int(results.nobs)}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">DF RESIDUALS</div><div style=\"{vl}\">{int(results.df_resid)}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">DF MODEL</div><div style=\"{vl}\">{int(results.df_model)}</div></td>")
        code.append("    </tr></table>'''")
        code.append("")
        code.append("    # ── Coefficients Table ──")
        code.append("    ths = 'padding:7px 10px; font-size:9pt; font-weight:700; color:#64748B; border-bottom:2px solid #CBD5E1; background:#F8FAFC;'")
        code.append("    tds = 'padding:6px 10px; border-bottom:1px solid #F1F5F9; font-family:Consolas,monospace; font-size:10pt; color:#334155; text-align:right;'")
        code.append("    coef_header = f'''<table style=\"width:100%; border-collapse:collapse; margin-bottom:6px;\">")
        code.append("    <tr>")
        code.append("      <th style=\"{ths} text-align:left;\">Variable</th>")
        code.append("      <th style=\"{ths} text-align:right;\">Coef.</th>")
        code.append("      <th style=\"{ths} text-align:right;\">Std. Err.</th>")
        code.append("      <th style=\"{ths} text-align:right;\">z</th>")
        code.append("      <th style=\"{ths} text-align:right;\">P&gt;|z|</th>")
        code.append("      <th style=\"{ths} text-align:right; color:#0F766E;\">Odds Ratio</th>")
        code.append("      <th style=\"{ths} text-align:right;\">[0.025</th>")
        code.append("      <th style=\"{ths} text-align:right;\">0.975]</th>")
        code.append("      <th style=\"{ths} text-align:center;\">Sig.</th>")
        code.append("    </tr>'''")
        code.append("")
        code.append("    coef_rows = ''")
        code.append("    for i, var in enumerate(results.params.index):")
        code.append("        p = results.pvalues[var]")
        code.append("        stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''")
        code.append("        sc2 = '#4338CA' if stars else '#CBD5E1'")
        code.append("        coef_rows += f'''<tr>")
        code.append("          <td style=\"{tds} text-align:left; font-weight:600; color:#1E293B; font-family:Segoe UI,sans-serif;\">{var}</td>")
        code.append("          <td style=\"{tds}\">{results.params[var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{results.bse[var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{results.tvalues[var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{results.pvalues[var]:.4f}</td>")
        code.append("          <td style=\"{tds} color:#0F766E; font-weight:600;\">{odds_ratios[var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{ci.iloc[i, 0]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{ci.iloc[i, 1]:.4f}</td>")
        code.append("          <td style=\"{tds} text-align:center; color:{sc2}; font-weight:700;\">{stars}</td>")
        code.append("        </tr>'''")
        code.append("")
        code.append("    coef_html = coef_header + coef_rows + '</table>'")
        code.append("    legend = '<div style=\"font-size:8pt; color:#94A3B8; text-align:right;\">*** p &lt; 0.001 &nbsp; ** p &lt; 0.01 &nbsp; * p &lt; 0.05</div>'")
        code.append("    html_output = eq_html + stats_html + coef_html + legend")

        if show_plots:
            if self._is_plotly():
                plotly_style_code = generate_plotly_style_code(plot_style)
                code.append("")
                code.append("    import plotly.graph_objects as go")
                code.append("    from sklearn.metrics import roc_curve, auc, confusion_matrix")
                for line in plotly_style_code.split("\n"):
                    if line.strip():
                        code.append(f"    {line}")
                # ROC Curve (Plotly)
                code.append("    y_pred_prob = results.predict(X)")
                code.append("    fpr, tpr, _ = roc_curve(y, y_pred_prob)")
                code.append("    roc_auc = auc(fpr, tpr)")
                code.append("    fig_roc = go.Figure()")
                code.append("    fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines',")
                code.append("                                  name=f'ROC (AUC={roc_auc:.3f})', line=dict(width=2)))")
                code.append("    fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines',")
                code.append("                                  name='Random', line=dict(dash='dash')))")
                code.append("    fig_roc.update_layout(title='ROC Curve', xaxis_title='FPR', yaxis_title='TPR')")
                code.append("    if 'show_plotly' in globals():")
                code.append("        html_output += f'<div style=\"margin-top:24px; text-align:center;\">{fig_roc.to_html(include_plotlyjs=\"cdn\", full_html=False)}</div>'")
                # Confusion Matrix (Plotly)
                code.append(f"    y_pred_class = (y_pred_prob > {threshold:.2f}).astype(int)")
                code.append("    cm = confusion_matrix(y, y_pred_class)")
                code.append("    fig_cm = go.Figure(data=go.Heatmap(")
                code.append("        z=cm, text=cm, texttemplate='%{text}',")
                code.append("        colorscale='Blues', colorbar=dict(title='Count')))")
                code.append(f"    fig_cm.update_layout(title='Confusion Matrix (Threshold={threshold:.2f})',")
                code.append("                         xaxis_title='Predicted', yaxis_title='Actual')")
                code.append("    if 'show_plotly' in globals():")
                code.append("        html_output += f'<div style=\"margin-top:24px; text-align:center;\">{fig_cm.to_html(include_plotlyjs=\"cdn\", full_html=False)}</div>'")
            else:
                style_code = generate_style_code(plot_style)
                code.append("")
                code.append("    import matplotlib.pyplot as plt")
                code.append("    import seaborn as sns")
                code.append("    from sklearn.metrics import roc_curve, auc, confusion_matrix")
                code.append("    import io, base64")
                for line in style_code.split("\n"):
                    if line.strip():
                        code.append(f"    {line}")
                code.append("    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']")
                code.append("    c_main = colors[0] if len(colors) > 0 else 'darkorange'")
                code.append("    c_alt = colors[1] if len(colors) > 1 else 'navy'")

                # ROC Curve
                code.append("    fig, ax = plt.subplots(figsize=(8, 8))")
                code.append("    y_pred_prob = results.predict(X)")
                code.append("    fpr, tpr, _ = roc_curve(y, y_pred_prob)")
                code.append("    roc_auc = auc(fpr, tpr)")
                code.append("    ax.plot(fpr, tpr, color=c_main, lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')")
                code.append("    ax.plot([0, 1], [0, 1], color=c_alt, lw=2, linestyle='--')")
                code.append("    ax.set_xlim([0.0, 1.0])")
                code.append("    ax.set_ylim([0.0, 1.05])")
                code.append("    ax.set_xlabel('False Positive Rate')")
                code.append("    ax.set_ylabel('True Positive Rate')")
                code.append("    ax.set_title('Receiver Operating Characteristic')")
                code.append("    ax.legend(loc='lower right')")
                code.append("    fig.tight_layout()")
                code.append("    buf = io.BytesIO()")
                code.append("    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
                code.append("    plt.close(fig)")
                code.append("    buf.seek(0)")
                code.append("    img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
                code.append("    if \'register_figure\' in globals():")
                code.append("        register_figure(img_b64, fig)")
                code.append("    html_output += f'<div style=\"margin-top:24px; text-align:center;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>'")

                # Confusion Matrix
                code.append("    fig, ax = plt.subplots(figsize=(8, 8))")
                code.append(f"    y_pred_class = (y_pred_prob > {threshold:.2f}).astype(int)")
                code.append("    cm = confusion_matrix(y, y_pred_class)")
                code.append("    cmap = sns.light_palette(c_main, as_cmap=True)")
                code.append("    sns.heatmap(cm, annot=True, fmt='d', cmap=cmap, ax=ax, cbar=False)")
                code.append(f"    ax.set_title('Confusion Matrix (Threshold={threshold:.2f})')")
                code.append("    ax.set_xlabel('Predicted Label')")
                code.append("    ax.set_ylabel('True Label')")
                code.append("    fig.tight_layout()")
                code.append("    buf = io.BytesIO()")
                code.append("    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
                code.append("    plt.close(fig)")
                code.append("    buf.seek(0)")
                code.append("    img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
                code.append("    if \'register_figure\' in globals():")
                code.append("        register_figure(img_b64, fig)")
                code.append("    html_output += f'<div style=\"margin-top:24px; text-align:center;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>'")

        code.append("")
        code.append("    show_result('Logistic Regression', html_output)")
        code.append("else:")
        code.append("    print('Logistic Regression Results')")
        code.append("    print(f'Pseudo R-squared: {results.prsquared:.4f}')")
        code.append("    print(results.params)")


        return "\n".join(code)
    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Logistic Regression Help",
            "Performs Logistic Regression for binary classification.\n\n"
            "Dependent Variable (Y): The binary (0/1) variable to predict.\n"
            "Independent Variables (X): The predictor variables.\n\n"
            "Odds Ratio: Represents the exponentiated coefficient (e^Coef), interpreting the multiplicative change in odds for a 1-unit increase in X."
        )
