"""Correlation Matrix Dialog.

Computes pairwise correlations (Pearson / Spearman / Kendall) for selected
numeric variables and displays the result as an HTML table with significance
stars and an optional heatmap visualisation in the Results tab.
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


class CorrelationDialog(BaseAnalysisDialog):
    """Dialog for computing a correlation matrix with p-values."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Correlation Matrix", df, parent)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_vars = QListWidget()
        layout.addWidget(
            self._create_selector_row(
                "Variables (select 2+ numeric):", self.list_vars, multi_select=True
            )
        )

    def build_options(self, layout: QVBoxLayout) -> None:
        # Method
        group_method = QGroupBox("Options")
        l_method = QVBoxLayout(group_method)

        l_method.addWidget(QLabel("Method:"))
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(["Pearson", "Spearman", "Kendall"])
        l_method.addWidget(self.cmb_method)

        self.chk_heatmap = QCheckBox("Include heatmap visualisation")
        self.chk_heatmap.setChecked(True)
        l_method.addWidget(self.chk_heatmap)

        self.chk_pvalues = QCheckBox("Show p-values and significance stars")
        self.chk_pvalues.setChecked(False)
        l_method.addWidget(self.chk_pvalues)

        layout.addWidget(group_method)

        # Style (for heatmap)
        group_style = QGroupBox("Plot Style")
        l_style = QVBoxLayout(group_style)
        l_style.addWidget(QLabel("Preset:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        l_style.addWidget(self.cmb_style)
        layout.addWidget(group_style)

    def generate_code(self) -> str:
        selected = [self.list_vars.item(i).text() for i in range(self.list_vars.count())]

        if len(selected) < 2:
            QMessageBox.warning(self, "Missing Input", "Please select at least 2 numeric variables.")
            return ""

        method = self.cmb_method.currentText().lower()
        show_heatmap = self.chk_heatmap.isChecked()
        show_pvalues = self.chk_pvalues.isChecked()
        style_name = self.cmb_style.currentText()

        vars_repr = repr(selected)

        code = [
            f"# Correlation Matrix ({method.capitalize()})",
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            "from scipy import stats as scipy_stats",
            "",
            f"cols = {vars_repr}",
            f"method = '{method}'",
            "",
            "if isinstance(df, pl.DataFrame):",
            "    # Filter to numeric columns only and drop nulls",
            "    sub_pl = df.select([",
            "        pl.col(c) for c in cols ",
            "        if df.get_column(c).dtype.is_numeric()",
            "    ]).drop_nulls()",
            "    valid_cols = sub_pl.columns",
            "    sub = sub_pl.to_pandas()",
            "else:",
            "    # Filter to numeric columns only and drop nulls",
            "    valid_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]",
            "    sub = df[valid_cols].dropna()",
            "",
            "if len(sub) < 2 or len(valid_cols) < 2:",
            "    print('Error: Not enough numeric data available for correlation (minimum 2 variables and 2 rows required).')",
            "else:",
            "    # Update cols to only those that were numeric and had data",
            "    cols = valid_cols",
            "    # Correlation coefficients",
            "    corr = sub.corr(method=method)",
            "    n = len(sub)",
        ]

        # Indent the rest of the code generation logic
        indent = "    "
        
        inner_code = []
        if show_pvalues:
            inner_code += [
                "",
                "# P-value matrix",
                "p_matrix = pd.DataFrame(np.ones((len(cols), len(cols))), index=cols, columns=cols)",
                "for i, c1 in enumerate(cols):",
                "    for j, c2 in enumerate(cols):",
                "        if i != j:",
                "            try:",
                "                if method == 'pearson':",
                "                    _, p = scipy_stats.pearsonr(sub[c1], sub[c2])",
                "                elif method == 'spearman':",
                "                    _, p = scipy_stats.spearmanr(sub[c1], sub[c2])",
                "                else:",
                "                    _, p = scipy_stats.kendalltau(sub[c1], sub[c2])",
                "                p_matrix.iloc[i, j] = p",
                "            except Exception:",
                "                p_matrix.iloc[i, j] = np.nan",
                "",
                "def _sig(p):",
                "    if pd.isna(p): return ''",
                "    if p < 0.001: return '***'",
                "    if p < 0.01:  return '**'",
                "    if p < 0.05:  return '*'",
                "    return ''",
            ]
        else:
            inner_code += [
                "",
                "n = len(sub)",
            ]

        inner_code += [
            "",
            "ths = 'padding:7px 10px; font-size:9pt; font-weight:700; color:#64748B; border-bottom:2px solid #CBD5E1; background:#F8FAFC;'",
            "tds = 'padding:6px 10px; border-bottom:1px solid #F1F5F9; font-family:Consolas,monospace; font-size:10pt; text-align:right;'",
            "",
            f"title_html = '<h3 style=\"color:#1E293B; font-family:Segoe UI,sans-serif;\">Correlation Matrix ({method.capitalize()}) &mdash; n = ' + str(n) + '</h3>'",
            "",
            "header = '<table style=\"width:100%; border-collapse:collapse;\">'",
            "header += '<tr><th style=\"' + ths + ' text-align:left;\">Variable</th>'",
            "for c in cols:",
            "    header += f'<th style=\"{ths} text-align:right;\">{c}</th>'",
            "header += '</tr>'",
            "",
            "rows_html = ''",
            "for i, r in enumerate(cols):",
            "    rows_html += '<tr>'",
            "    rows_html += f'<td style=\"{tds} text-align:left; font-weight:600; color:#1E293B; font-family:Segoe UI,sans-serif;\">{r}</td>'",
            "    for j, c in enumerate(cols):",
            "        val = corr.iloc[i, j]",
        ]

        if show_pvalues:
            inner_code += [
                "        p = p_matrix.iloc[i, j]",
                "        stars = _sig(p)",
            ]

        inner_code += [
            "        if i == j:",
            "            color = '#94A3B8'",
            "        elif pd.isna(val):",
            "            color = '#CBD5E1'",
            "        elif abs(val) > 0.7:",
            "            color = '#DC2626' if val < 0 else '#059669'",
            "        elif abs(val) > 0.4:",
            "            color = '#EA580C' if val < 0 else '#0D9488'",
            "        else:",
            "            color = '#334155'",
        ]

        if show_pvalues:
            inner_code += [
                "        star_span = f'<span style=\"color:#4338CA; font-weight:700;\">{stars}</span>' if stars else ''",
                "        val_str = f'{val:.3f}' if not pd.isna(val) else 'NaN'",
                "        rows_html += f'<td style=\"{tds} color:{color};\">{val_str}{star_span}</td>'",
            ]
        else:
            inner_code += [
                "        val_str = f'{val:.3f}' if not pd.isna(val) else 'NaN'",
                "        rows_html += f'<td style=\"{tds} color:{color};\">{val_str}</td>'",
            ]

        inner_code += [
            "    rows_html += '</tr>'",
            "",
        ]

        if show_pvalues:
            inner_code.append("legend = '<div style=\"font-size:8pt; color:#94A3B8; text-align:right; margin-top:4px;\">*** p &lt; 0.001 &nbsp; ** p &lt; 0.01 &nbsp; * p &lt; 0.05</div>'")
            inner_code.append("html_output = title_html + header + rows_html + '</table>' + legend")
        else:
            inner_code.append("html_output = title_html + header + rows_html + '</table>'")

        if show_heatmap:
            style_code = generate_style_code(style_name)
            inner_code += [
                "",
                "import matplotlib.pyplot as plt",
                "import seaborn as sns",
                "import io, base64",
            ]
            for line in style_code.split("\n"):
                if line.strip():
                    inner_code.append(line)
            inner_code += [
                "",
                "fig, ax = plt.subplots(figsize=(8, 6))",
                "colors = plt.rcParams['axes.prop_cycle'].by_key()['color']",
                "c_main = colors[0] if len(colors) > 0 else '#4C72B0'",
                "cmap = sns.blend_palette(['#4A4A4A', '#FFFFFF', c_main], as_cmap=True)",
                "",
                "# Dynamic annotation and label font sizes",
                "n_vars = len(cols)",
                "annot_size = max(6, 12 - n_vars // 2)",
                "label_size = max(6, 10 - n_vars // 3)",
                "",
                "sns.heatmap(corr, annot=True, fmt='.2f', cmap=cmap, vmin=-1, vmax=1, center=0,",
                "            square=True, linewidths=.5, cbar_kws={'shrink': .8}, ax=ax,",
                "            annot_kws={'size': annot_size})",
                "    ",
                "ax.tick_params(axis='both', which='major', labelsize=label_size)",
                "    ",
                "ax.set_title(f'Correlation Heatmap ({method.capitalize()})', pad=16)",
                "fig.tight_layout()",
                "",
                "buf = io.BytesIO()",
                "fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')",
                "plt.close(fig)",
                "buf.seek(0)",
                "img_b64 = base64.b64encode(buf.read()).decode('utf-8')",
                "if \'register_figure\' in globals():",
                "    register_figure(img_b64, fig)",
                "html_output += f'<div style=\"margin-top:24px; text-align:center;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>'",
            ]

        inner_code += [
            "",
            "if 'show_result' in globals():",
            "    show_result('Correlation Matrix', html_output)",
            "else:",
            "    print(corr.to_string())",
        ]

        # Add the indented inner code to the main code list
        code.extend([indent + line for line in inner_code])

        return "\n".join(code)
