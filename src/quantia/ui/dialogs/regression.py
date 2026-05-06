"""Linear Regression Dialog.

Allows selecting a dependent variable (Y) and one or more independent variables (X).
Generates code using scikit-learn LinearRegression to perform multi-threaded regression.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from quantia.ui.dialogs.base import BaseAnalysisDialog


class LinearRegressionDialog(BaseAnalysisDialog):
    """Dialog for performing Ordinary Least Squares (OLS) regression."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Linear Regression", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        """Add Dependent and Independent Variable selectors."""
        self.list_dependent = QListWidget()
        row_dep = self._create_selector_row("Dependent Variable (Y):", self.list_dependent, multi_select=False)
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
        
        self.chk_robust = QCheckBox("Robust Standard Errors (HC3)")
        l_opts.addWidget(self.chk_robust)

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
        self.chk_plots = QCheckBox("Generate Residuals & Q-Q Plots")
        l_plots.addWidget(self.chk_plots)

        l_plots.addWidget(QLabel("Plot Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        self.cmb_style.setEnabled(False)
        self.chk_plots.toggled.connect(self.cmb_style.setEnabled)
        l_plots.addWidget(self.cmb_style)

        layout.addWidget(group_plots)

    def generate_code(self) -> str:
        """Generate the Python code to run the regression."""
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
        robust_se = self.chk_robust.isChecked()
        stepwise = self.chk_stepwise.isChecked()
        criterion = self.cmb_criterion.currentText()
        show_plots = self.chk_plots.isChecked()
        plot_style = self.cmb_style.currentText()

        indep_str = ", ".join(f"'{v}'" for v in indep_vars)
        inter_str = ", ".join(f"'{v}'" for v in inter_vars)

        code = [
            f"# OLS Regression (Multi-threaded): {dep_var} ~ {', '.join(indep_vars + inter_vars)}",
            "from sklearn.linear_model import LinearRegression",
            "from scipy import stats",
            "import pandas as pd",
            "import polars as pl",
            "import numpy as np",
            "import warnings",
            "warnings.simplefilter('ignore', RuntimeWarning)",
            "",
            "def calculate_ols_stats(X, y, include_intercept=True):",
            "    # Prepare X with intercept if requested",
            "    if include_intercept and (X is None or 'const' not in X.columns):",
            "        if X is None:",
            "             X_model = np.ones((len(y), 1))",
            "             feature_names = ['const']",
            "        else:",
            "             X_model = np.column_stack([np.ones(X.shape[0]), X])",
            "             feature_names = ['const'] + list(X.columns)",
            "    else:",
            "        X_model = X.values if X is not None else np.empty((len(y), 0))",
            "        feature_names = list(X.columns) if X is not None else []",
            "    ",
            "    n, p = X_model.shape",
            "    # We use n_jobs=-1 for multi-threaded performance",
            "    model = LinearRegression(n_jobs=-1, fit_intercept=False).fit(X_model, y)",
            "    ",
            "    y_pred = model.predict(X_model)",
            "    residuals = y - y_pred",
            "    df_resid = n - p",
            "    df_model = p - (1 if include_intercept else 0)",
            "    ",
            "    sse = np.sum(residuals**2)",
            "    ssr = np.sum((y_pred - np.mean(y))**2)",
            "    sst = sse + ssr",
            "    ",
            "    r2 = 1 - (sse / np.sum((y - np.mean(y))**2))",
            "    adj_r2 = 1 - (1 - r2) * (n - 1) / df_resid",
            "    ",
            "    # F-statistic",
            "    if df_model > 0 and df_resid > 0:",
            "        f_stat = (ssr / df_model) / (sse / df_resid)",
            "        f_pvalue = 1 - stats.f.cdf(f_stat, df_model, df_resid)",
            "    else:",
            "        f_stat, f_pvalue = 0.0, 1.0",
            "    ",
            "    # Standard Errors & Coeff stats",
            "    mse = sse / df_resid if df_resid > 0 else np.nan",
            "    # Use pseudo-inverse for stability with collinear features",
            "    var_cov = mse * np.linalg.pinv(X_model.T @ X_model) if df_resid > 0 else np.full((p,p), np.nan)",
            "    std_err = np.sqrt(np.diagonal(var_cov))",
            "    ",
            "    coeffs = model.coef_",
            "    t_stats = coeffs / std_err",
            "    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df_resid))",
            "    ",
            "    # Confidence Intervals (95%)",
            "    t_crit = stats.t.ppf(0.975, df_resid)",
            "    conf_low = coeffs - t_crit * std_err",
            "    conf_high = coeffs + t_crit * std_err",
            "    ",
            "    # Log-likelihood, AIC, BIC",
            "    # Assuming normal distribution of residuals",
            "    llf = -(n/2) * (1 + np.log(2 * np.pi * sse / n))",
            "    aic = 2 * p - 2 * llf",
            "    bic = p * np.log(n) - 2 * llf",
            "    ",
            "    return {",
            "        'model': model, 'params': pd.Series(coeffs, index=feature_names),",
            "        'bse': pd.Series(std_err, index=feature_names),",
            "        'tvalues': pd.Series(t_stats, index=feature_names),",
            "        'pvalues': pd.Series(p_values, index=feature_names),",
            "        'conf_int': pd.DataFrame({'low': conf_low, 'high': conf_high}, index=feature_names),",
            "        'rsquared': r2, 'rsquared_adj': adj_r2,",
            "        'fvalue': f_stat, 'f_pvalue': f_pvalue,",
            "        'aic': aic, 'bic': bic, 'llf': llf,",
            "        'nobs': n, 'df_resid': df_resid, 'df_model': df_model,",
            "        'fittedvalues': y_pred, 'resid': residuals",
            "    }",
            "",
            "# Prepare data",
            f"model_vars = ['{dep_var}', {indep_str}]",
            "if isinstance(df, pl.DataFrame):",
            "    # Multi-threaded extraction via Polars",
            "    model_data = df.select(model_vars).drop_nulls().to_pandas()",
            "else:",
            "    model_data = df[model_vars].dropna()",
            "",
            f"y = model_data['{dep_var}']",
            f"X_all = model_data[[{indep_str}]]",
            "X_all = pd.get_dummies(X_all, drop_first=True, dtype=float)",
        ]

        if inter_vars or stepwise:
            code.append("")
            code.append("# Group dummy columns by their original variable")
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
            code.append("# Perform Bidirectional Stepwise Selection")
            if inter_vars:
                code.append("available_vars = original_vars + interaction_vars")
            else:
                code.append("available_vars = original_vars")
            code.append("current_vars = []") # Start empty for bidirectional
            
            code.append("while True:")
            code.append("    changed = False")
            
            if "p-value" in criterion:
                code.append("    curr_cols = [c for ov in current_vars for c in var_groups[ov]]")
                code.append(f"    X_curr = X_all[curr_cols] if curr_cols else None")
                code.append(f"    res_curr = calculate_ols_stats(X_curr, y, {include_intercept}) if X_curr is not None else None")
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
                code.append("        test_vars = current_vars + [v]")
                code.append("        test_cols = [c for ov in test_vars for c in var_groups[ov]]")
                code.append(f"        test_X = X_all[test_cols]")
                code.append(f"        res_test = calculate_ols_stats(test_X, y, {include_intercept})")
                code.append("        ")
                code.append("        # Block p-value (min p of the new dummy set)")
                code.append("        new_dummies = var_groups[v]")
                code.append("        p = np.min([res_test['pvalues'][d] for d in new_dummies if d in res_test['pvalues']])")
                code.append("        ")
                code.append("        if p < best_p:")
                code.append("            best_p = p")
                code.append("            best_v = v")
                code.append("            changed = 'add'")
                code.append("    ")
                code.append("    if changed == 'add':")
                code.append("        current_vars.append(best_v)")
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
                code.append("            new_dummies = var_groups[v]")
                code.append("            p = np.max([res_curr['pvalues'][d] for d in new_dummies if d in res_curr['pvalues']])")
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
                code.append("    curr_cols = [c for ov in current_vars for c in var_groups[ov]]")
                code.append(f"    X_curr = X_all[curr_cols] if curr_cols else None")
                code.append(f"    best_score = calculate_ols_stats(X_curr, y, {include_intercept})['{metric}'] if X_curr is not None else np.inf")
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
                code.append("        test_vars = current_vars + [v]")
                code.append("        test_cols = [c for ov in test_vars for c in var_groups[ov]]")
                code.append(f"        test_X = X_all[test_cols]")
                code.append(f"        score = calculate_ols_stats(test_X, y, {include_intercept})['{metric}']")
                code.append("        if score < best_score:")
                code.append("            best_score = score")
                code.append("            best_v = v")
                code.append("            changed = 'add'")
                code.append("    ")
                code.append("    if changed == 'add':")
                code.append("        current_vars.append(best_v)")
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
                code.append("            test_cols = [c for ov in test_vars for c in var_groups[ov]]")
                code.append(f"            test_X = X_all[test_cols]")
                code.append(f"            score = calculate_ols_stats(test_X, y, {include_intercept})['{metric}']")
                code.append("            if score < best_score:")
                code.append("                best_score = score")
                code.append("                best_v = v")
                code.append("                changed = 'drop'")
                code.append("        if changed == 'drop':")
                code.append("            current_vars.remove(best_v)")
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
        code.append(f"results = calculate_ols_stats(X, y, {include_intercept})")
        
        code.append("")
        code.append("if 'show_result' in globals():")
        code.append("    ci = results['conf_int']")
        code.append("")
        code.append("    # ── Equation ──")
        code.append("    eq_terms = []")
        code.append("    for var, coef in results['params'].items():")
        code.append("        if var == 'const':")
        code.append("            eq_terms.append(f'{coef:.4f}')")
        code.append("        else:")
        code.append("            sign = '+' if coef >= 0 else '-'")
        code.append("            eq_terms.append(f'{sign} {abs(coef):.4f}\\u00b7{var}')")
        code.append(f"    eq_str = ' '.join(eq_terms)")
        code.append("")
        code.append("    eq_html = f'''<table style=\"width:100%; margin-bottom:16px;\">")
        code.append("    <tr><td style=\"background:#EEF2FF; border-left:3px solid #6366F1; padding:12px 16px;")
        code.append(f"        font-family:Cambria,Georgia,serif; font-size:12pt; color:#1E293B;\"><b style=\"color:#4338CA;\">{dep_var}</b> = {{eq_str}}</td></tr></table>'''")
        code.append("")
        code.append("    # ── Model Summary Card ──")
        code.append("    sc = 'padding:10px 14px; background:#F8FAFC; border:1px solid #F1F5F9; text-align:center;'")
        code.append("    lb = 'font-size:8pt; color:#94A3B8; font-weight:600;'")
        code.append("    vl = 'font-size:13pt; font-weight:700; color:#111827; font-family:Consolas,monospace;'")
        code.append("    stats_html = f'''<table style=\"width:100%; margin-bottom:16px; border-collapse:collapse;\">")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">R-SQUARED</div><div style=\"{vl}\">{results['rsquared']:.4f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">ADJ. R-SQUARED</div><div style=\"{vl}\">{results['rsquared_adj']:.4f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">F-STATISTIC</div><div style=\"{vl}\">{results['fvalue']:.2f}</div></td>")
        code.append("    </tr>")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">AIC</div><div style=\"{vl}\">{results['aic']:.1f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">BIC</div><div style=\"{vl}\">{results['bic']:.1f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">PROB (F-STAT)</div><div style=\"{vl}\">{results['f_pvalue']:.2e}</div></td>")
        code.append("    </tr>")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">OBSERVATIONS</div><div style=\"{vl}\">{int(results['nobs'])}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">DF RESIDUALS</div><div style=\"{vl}\">{int(results['df_resid'])}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">DF MODEL</div><div style=\"{vl}\">{int(results['df_model'])}</div></td>")
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
        code.append("      <th style=\"{ths} text-align:right;\">t</th>")
        code.append("      <th style=\"{ths} text-align:right;\">P&gt;|t|</th>")
        code.append("      <th style=\"{ths} text-align:right;\">[0.025</th>")
        code.append("      <th style=\"{ths} text-align:right;\">0.975]</th>")
        code.append("      <th style=\"{ths} text-align:center;\">Sig.</th>")
        code.append("    </tr>'''")
        code.append("")
        code.append("    coef_rows = ''")
        code.append("    for i, var in enumerate(results['params'].index):")
        code.append("        p = results['pvalues'][var]")
        code.append("        stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''")
        code.append("        sc2 = '#4338CA' if stars else '#CBD5E1'")
        code.append("        coef_rows += f'''<tr>")
        code.append("          <td style=\"{tds} text-align:left; font-weight:600; color:#1E293B; font-family:Segoe UI,sans-serif;\">{var}</td>")
        code.append("          <td style=\"{tds}\">{results['params'][var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{results['bse'][var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{results['tvalues'][var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{results['pvalues'][var]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{ci.iloc[i, 0]:.4f}</td>")
        code.append("          <td style=\"{tds}\">{ci.iloc[i, 1]:.4f}</td>")
        code.append("          <td style=\"{tds} text-align:center; color:{sc2}; font-weight:700;\">{stars}</td>")
        code.append("        </tr>'''")
        code.append("")
        code.append("    coef_html = coef_header + coef_rows + '</table>'")
        code.append("    legend = '<div style=\"font-size:8pt; color:#94A3B8; text-align:right;\">*** p &lt; 0.001 &nbsp; ** p &lt; 0.01 &nbsp; * p &lt; 0.05</div>'")
        code.append("    html_output = eq_html + stats_html + coef_html + legend")
        
        if show_plots:
            style_code = generate_style_code(plot_style)
            code.append("")
            code.append("    import matplotlib.pyplot as plt")
            code.append("    import seaborn as sns")
            code.append("    import io, base64")
            for line in style_code.split("\n"):
                if line.strip():
                    code.append(f"    {line}")
            code.append("    fig, axes = plt.subplots(1, 2, figsize=(10, 4))")
            code.append("    sns.residplot(x=results['fittedvalues'], y=results['resid'], ax=axes[0], lowess=True, scatter_kws={'alpha': 0.5})")
            code.append("    axes[0].set_title('Residuals vs Fitted')")
            code.append("    axes[0].set_xlabel('Fitted values')")
            code.append("    axes[0].set_ylabel('Residuals')")
            
            # Manual Q-Q plot
            code.append("    osm, osr = stats.probplot(results['resid'], dist='norm', plot=None)")
            code.append("    axes[1].scatter(osm, osr, alpha=0.5)")
            code.append("    slope, intercept, _, _, _ = stats.linregress(osm, osr)")
            code.append("    axes[1].plot(osm, intercept + slope*osm, color='red', lw=2)")
            
            code.append("    axes[1].set_title('Normal Q-Q')")
            code.append("    fig.tight_layout()")
            code.append("    buf = io.BytesIO()")
            code.append("    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')")
            code.append("    plt.close(fig)")
            code.append("    buf.seek(0)")
            code.append("    img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
            code.append("    plots_html = f'<div style=\"margin-top:24px; text-align:center;\"><img src=\"data:image/png;base64,{img_b64}\" style=\"max-width:100%; border:1px solid #E2E8F0; border-radius:4px;\"/></div>'")
            code.append("    html_output += plots_html")

        code.append("")
        code.append("    show_result('Linear Regression', html_output)")
        code.append("else:")
        code.append("    print('OLS Regression Results')")
        code.append("    print(f'R-squared: {results[\"rsquared\"]:.4f}')")
        code.append("    print(results[\"params\"])")

        return \"\\n\".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Linear Regression Help",
            "Performs Ordinary Least Squares (OLS) regression.\n\n"
            "Dependent Variable (Y): The continuous variable you want to predict.\n"
            "Independent Variables (X): The predictor variables.\n\n"
            "Note: Missing values across any selected variables will be dropped prior to fitting."
        )
