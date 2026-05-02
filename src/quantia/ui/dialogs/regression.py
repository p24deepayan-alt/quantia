"""Linear Regression Dialog.

Allows selecting a dependent variable (Y) and one or more independent variables (X).
Generates code using statsmodels.api.OLS to perform linear regression.
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

        if not dep_var:
            QMessageBox.warning(self, "Missing Input", "Please select a Dependent Variable (Y).")
            return ""
        if not indep_vars:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Independent Variable (X).")
            return ""

        include_intercept = self.chk_intercept.isChecked()
        robust_se = self.chk_robust.isChecked()
        stepwise = self.chk_stepwise.isChecked()
        criterion = self.cmb_criterion.currentText()
        show_plots = self.chk_plots.isChecked()
        plot_style = self.cmb_style.currentText()

        indep_str = ", ".join(f"'{v}'" for v in indep_vars)

        code = [
            f"# OLS Regression: {dep_var} ~ {', '.join(indep_vars)}",
            "import statsmodels.api as sm",
            "import pandas as pd",
            "import numpy as np",
            "import warnings",
            "warnings.simplefilter('ignore', RuntimeWarning)",
            "",
            "# Prepare data",
            f"model_vars = ['{dep_var}', {indep_str}]",
            "model_data = df[model_vars].dropna()",
            f"y = model_data['{dep_var}']",
            f"X_all = model_data[[{indep_str}]]",
            "X_all = pd.get_dummies(X_all, drop_first=True, dtype=float)",
        ]

        if stepwise:
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
            code.append("# Perform Bidirectional Stepwise Selection (Variables kept together)")
            code.append("available_vars = original_vars")
            code.append("current_vars = []") # Start empty for bidirectional
            
            code.append("while True:")
            code.append("    changed = False")
            
            if "p-value" in criterion:
                code.append("    curr_cols = [c for ov in current_vars for c in var_groups[ov]]")
                code.append(f"    X_curr = sm.add_constant(X_all[curr_cols]) if {include_intercept} and curr_cols else X_all[curr_cols] if curr_cols else None")
                code.append("    res_curr = sm.OLS(y, X_curr).fit() if X_curr is not None else None")
                code.append("    ")
                code.append("    # 1. Try adding the most significant variable (F-test for blocks)")
                code.append("    candidates_add = [v for v in available_vars if v not in current_vars]")
                code.append("    best_p = 0.05")
                code.append("    best_v = None")
                code.append("    for v in candidates_add:")
                code.append("        test_vars = current_vars + [v]")
                code.append("        test_cols = [c for ov in test_vars for c in var_groups[ov]]")
                code.append(f"        test_X = sm.add_constant(X_all[test_cols]) if {include_intercept} else X_all[test_cols]")
                code.append("        res_test = sm.OLS(y, test_X).fit()")
                code.append("        if res_curr is None:")
                code.append("            p = res_test.f_pvalue if hasattr(res_test, 'f_pvalue') and not pd.isna(res_test.f_pvalue) else 1.0")
                code.append("        else:")
                code.append("            _, p, _ = res_test.compare_f_test(res_curr)")
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
                code.append("    # 2. Try dropping the least significant variable (F-test)")
                code.append("    if len(current_vars) > 0:")
                code.append("        max_p = -1")
                code.append("        worst_v = None")
                code.append("        for v in current_vars:")
                code.append("            test_vars = [cv for cv in current_vars if cv != v]")
                code.append("            test_cols = [c for ov in test_vars for c in var_groups[ov]]")
                code.append(f"            test_X = sm.add_constant(X_all[test_cols]) if {include_intercept} and test_cols else X_all[test_cols] if test_cols else None")
                code.append("            if test_X is None:")
                code.append("                p = res_curr.f_pvalue if hasattr(res_curr, 'f_pvalue') and not pd.isna(res_curr.f_pvalue) else 1.0")
                code.append("            else:")
                code.append("                res_test = sm.OLS(y, test_X).fit()")
                code.append("                _, p, _ = res_curr.compare_f_test(res_test)")
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
                code.append(f"    X_curr = sm.add_constant(X_all[curr_cols]) if {include_intercept} and curr_cols else X_all[curr_cols] if curr_cols else None")
                code.append(f"    best_score = sm.OLS(y, X_curr).fit().{metric} if X_curr is not None else np.inf")
                code.append("    ")
                code.append("    # 1. Try adding a variable")
                code.append("    candidates_add = [v for v in available_vars if v not in current_vars]")
                code.append("    best_v = None")
                code.append("    for v in candidates_add:")
                code.append("        test_vars = current_vars + [v]")
                code.append("        test_cols = [c for ov in test_vars for c in var_groups[ov]]")
                code.append(f"        test_X = sm.add_constant(X_all[test_cols]) if {include_intercept} else X_all[test_cols]")
                code.append(f"        score = sm.OLS(y, test_X).fit().{metric}")
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
                code.append("            test_vars = [cv for cv in current_vars if cv != v]")
                code.append("            test_cols = [c for ov in test_vars for c in var_groups[ov]]")
                code.append(f"            test_X = sm.add_constant(X_all[test_cols]) if {include_intercept} else X_all[test_cols]")
                code.append(f"            score = sm.OLS(y, test_X).fit().{metric}")
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
            code.append("X = X_all")

        if include_intercept:
            code.append("X = sm.add_constant(X)")

        code.append("")
        cov_type = "'HC3'" if robust_se else "'nonrobust'"
        code.append(f"results = sm.OLS(y, X).fit(cov_type={cov_type})")
        
        code.append("")
        code.append("if 'show_result' in globals():")
        code.append("    ci = results.conf_int()")
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
        code.append(f"        font-family:Cambria,Georgia,serif; font-size:12pt; color:#1E293B;\"><b style=\"color:#4338CA;\">{dep_var}</b> = {{eq_str}}</td></tr></table>'''")
        code.append("")
        code.append("    # ── Model Summary Card ──")
        code.append("    sc = 'padding:10px 14px; background:#F8FAFC; border:1px solid #F1F5F9; text-align:center;'")
        code.append("    lb = 'font-size:8pt; color:#94A3B8; font-weight:600;'")
        code.append("    vl = 'font-size:13pt; font-weight:700; color:#111827; font-family:Consolas,monospace;'")
        code.append("    stats_html = f'''<table style=\"width:100%; margin-bottom:16px; border-collapse:collapse;\">")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">R-SQUARED</div><div style=\"{vl}\">{results.rsquared:.4f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">ADJ. R-SQUARED</div><div style=\"{vl}\">{results.rsquared_adj:.4f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">F-STATISTIC</div><div style=\"{vl}\">{results.fvalue:.2f}</div></td>")
        code.append("    </tr>")
        code.append("    <tr>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">AIC</div><div style=\"{vl}\">{results.aic:.1f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">BIC</div><div style=\"{vl}\">{results.bic:.1f}</div></td>")
        code.append("      <td style=\"{sc}\"><div style=\"{lb}\">PROB (F-STAT)</div><div style=\"{vl}\">{results.f_pvalue:.2e}</div></td>")
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
        code.append("      <th style=\"{ths} text-align:right;\">t</th>")
        code.append("      <th style=\"{ths} text-align:right;\">P&gt;|t|</th>")
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
            code.append("    sns.residplot(x=results.fittedvalues, y=results.resid, ax=axes[0], lowess=True, scatter_kws={'alpha': 0.5})")
            code.append("    axes[0].set_title('Residuals vs Fitted')")
            code.append("    axes[0].set_xlabel('Fitted values')")
            code.append("    axes[0].set_ylabel('Residuals')")
            code.append("    sm.qqplot(results.resid, line='45', fit=True, ax=axes[1])")
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
        code.append("    print(results.summary())")

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self, 
            "Linear Regression Help",
            "Performs Ordinary Least Squares (OLS) regression.\n\n"
            "Dependent Variable (Y): The continuous variable you want to predict.\n"
            "Independent Variables (X): The predictor variables.\n\n"
            "Note: Missing values across any selected variables will be dropped prior to fitting."
        )
