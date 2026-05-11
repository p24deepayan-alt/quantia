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
from quantia.ui.central.plotly_styles import generate_plotly_style_code
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
            f"# OLS Regression: {dep_var} ~ {', '.join(indep_vars + inter_vars)}",
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
                code.append(f"    res_curr = sm.OLS(y, X_curr).fit() if X_curr is not None else None")
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
                code.append(f"        res_test = sm.OLS(y, test_X).fit()")
                code.append("        ")
                code.append("        # Block p-value (min p of the new dummy set)")
                code.append("        new_dummy_indices = list(range(len(test_indices) - len(var_groups[v]), len(test_indices)))")
                code.append("        p = np.min([res_test.pvalues.iloc[i] for i in new_dummy_indices])")
                code.append("        ")
                code.append("        if p < best_p:")
                code.append("            best_p = p")
                code.append("            best_v = v")
                code.append("            changed = 'add'")
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
                code.append(f"    best_score = sm.OLS(y, X_curr).fit().{metric} if X_curr is not None else np.inf")
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
                code.append(f"        score = sm.OLS(y, test_X).fit().{metric}")
                code.append("        if score < best_score:")
                code.append("            best_score = score")
                code.append("            best_v = v")
                code.append("            changed = 'add'")
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
                code.append(f"            score = sm.OLS(y, test_X).fit().{metric}")
                code.append("            if score < best_score:")
                code.append("                best_score = score")
                code.append("                best_v = v")
                code.append("                changed = 'drop'")
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
        
        fit_args = "cov_type='HC3'" if robust_se else ""
        code.append(f"results = sm.OLS(y, X).fit({fit_args})")
        
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
            if self._is_plotly():
                plotly_style_code = generate_plotly_style_code(plot_style)
                code.append("")
                code.append("    import plotly.graph_objects as go")
                code.append("    from scipy import stats")
                for line in plotly_style_code.split("\n"):
                    if line.strip():
                        code.append(f"    {line}")
                # Residuals vs Fitted (Plotly)
                code.append("    fig_res = go.Figure()")
                code.append("    fig_res.add_trace(go.Scatter(x=results.fittedvalues, y=results.resid,")
                code.append("                                  mode='markers', opacity=0.5, name='Residuals'))")
                code.append("    fig_res.update_layout(title='Residuals vs Fitted',")
                code.append("                          xaxis_title='Fitted values', yaxis_title='Residuals')")
                code.append("    if 'show_plotly' in globals():")
                code.append("        show_plotly('Residuals vs Fitted', fig_res.to_html(include_plotlyjs='cdn'))")
                # Q-Q Plot (Plotly)
                code.append("    (osm, osr), (slope, intercept, _) = stats.probplot(results.resid, dist='norm', plot=None)")
                code.append("    import numpy as np")
                code.append("    fig_qq = go.Figure()")
                code.append("    fig_qq.add_trace(go.Scatter(x=osm, y=osr, mode='markers', name='Sample', opacity=0.5))")
                code.append("    fig_qq.add_trace(go.Scatter(x=osm, y=intercept + slope * np.array(osm),")
                code.append("                                mode='lines', name='Reference',")
                code.append("                                line=dict(color='red', width=2)))")
                code.append("    fig_qq.update_layout(title='Normal Q-Q',")
                code.append("                         xaxis_title='Theoretical Quantiles', yaxis_title='Sample Quantiles')")
                code.append("    if 'show_plotly' in globals():")
                code.append("        show_plotly('Normal Q-Q', fig_qq.to_html(include_plotlyjs='cdn'))")
            else:
                style_code = generate_style_code(plot_style)
                code.append("")
                code.append("    import matplotlib.pyplot as plt")
                code.append("    import seaborn as sns")
                code.append("    import io, base64")
                code.append("    from scipy import stats")
                for line in style_code.split("\n"):
                    if line.strip():
                        code.append(f"    {line}")
                code.append("    # Residuals vs Fitted")
                code.append("    fig, ax = plt.subplots(figsize=(8, 8))")
                code.append("    sns.residplot(x=results.fittedvalues, y=results.resid, ax=ax, lowess=True, scatter_kws={'alpha': 0.5})")
                code.append("    ax.set_title('Residuals vs Fitted')")
                code.append("    ax.set_xlabel('Fitted values')")
                code.append("    ax.set_ylabel('Residuals')")
                code.append("    fig.tight_layout()")
                code.append("    buf = io.BytesIO()")
                code.append("    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
                code.append("    plt.close(fig)")
                code.append("    buf.seek(0)")
                code.append("    img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
                code.append("    if \'register_figure\' in globals():")
                code.append("        register_figure(img_b64, fig)")
                code.append("    html_output += f'<div style=\"margin-top:24px; text-align:center;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>'")
                
                # Manual Q-Q plot
                code.append("    fig, ax = plt.subplots(figsize=(8, 8))")
                code.append("    (osm, osr), (slope, intercept, _) = stats.probplot(results.resid, dist='norm', plot=None)")
                code.append("    ax.scatter(osm, osr, alpha=0.5)")
                code.append("    ax.plot(osm, intercept + slope*osm, color='red', lw=2)")
                code.append("    ax.set_title('Normal Q-Q')")
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
        code.append("    show_result('Linear Regression', html_output)")
        code.append("else:")
        code.append("    print('OLS Regression Results')")
        code.append("    print(f'R-squared: {results.rsquared:.4f}')")
        code.append("    print(results.params)")


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
