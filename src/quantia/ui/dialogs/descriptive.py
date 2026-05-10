"""Descriptive Statistics Dialog.

Allows selecting variables to compute summary statistics:
- All variables: Variable name, Type, Count
- Numeric: Mean, Median, Mode, Standard Deviation, Variance
- Categorical: Count of Unique values, Top 2 categories
- Binary: % of TRUE/Yes/1
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
        """Informational text."""
        lbl = QLabel(
            "Descriptive statistics will be computed for all selected variables.\n\n"
            "• Numeric: Mean, Median, Mode, Std Dev, Variance\n"
            "• Categorical: Unique count, Top 2 categories\n"
            "• Binary: % of TRUE/Yes/1\n\n"
            "Each variable shows Name, Type and Count."
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
            "import polars as pl",
            "import numpy as np",
            f"vars_to_analyze = [{vars_str}]",
            "",
            "# Convert to pandas for uniform processing",
            "if isinstance(df, pl.DataFrame):",
            "    _pdf = df.select(vars_to_analyze).to_pandas()",
            "else:",
            "    _pdf = df[vars_to_analyze]",
            "",
            "# Classify each variable",
            "def _classify(s):",
            "    if pd.api.types.is_bool_dtype(s):",
            "        return 'Binary'",
            "    if pd.api.types.is_numeric_dtype(s):",
            "        vals = s.dropna().unique()",
            "        if set(vals).issubset({0, 1, 0.0, 1.0, True, False}):",
            "            return 'Binary'",
            "        return 'Numeric'",
            "    if pd.api.types.is_object_dtype(s) or pd.api.types.is_categorical_dtype(s):",
            "        vals = s.dropna().unique()",
            "        lower = {str(v).strip().lower() for v in vals}",
            "        if lower.issubset({'true', 'false', 'yes', 'no', '1', '0'}):",
            "            return 'Binary'",
            "        return 'Categorical'",
            "    return 'Categorical'",
            "",
            "if 'show_result' in globals():",
            "    ths = 'padding:8px 12px; font-size:10pt; font-weight:700; color:#475569; border-bottom:2px solid #CBD5E1; text-align:left; background:#F8FAFC;'",
            "    tds = 'padding:8px 12px; font-size:10pt; color:#1E293B; border-bottom:1px solid #E2E8F0; text-align:left;'",
            "    tds_val = 'padding:8px 12px; font-size:10pt; color:#1E293B; border-bottom:1px solid #E2E8F0; text-align:right; font-family:Fira Code,Consolas,monospace;'",
            "",
            "    html = '<h3 style=\"color:#1E293B; font-family:Segoe UI,sans-serif;\">Descriptive Statistics</h3>'",
            "",
            "    for i, col in enumerate(vars_to_analyze):",
            "        if 'progress' in globals(): progress(int((i+1)/len(vars_to_analyze)*100))",
            "        s = _pdf[col]",
            "        count = int(s.count())",
            "        vtype = _classify(s)",
            "",
            "        # Variable header",
            "        html += f'<div style=\"margin-bottom:20px;\">'",
            "        html += f'<h4 style=\"margin:0 0 8px 0; color:#334155; font-family:Segoe UI,sans-serif;\">{col}</h4>'",
            "",
            "        # Common info row",
            "        html += f'<div style=\"padding:8px 12px; background:#F8FAFC; border-radius:4px; margin-bottom:8px; font-size:10pt; color:#475569;\">'",
            "        html += f'<b>Type:</b> {vtype} &nbsp;|&nbsp; <b>Count:</b> {count:,}'",
            "        html += '</div>'",
            "",
            "        if vtype == 'Numeric':",
            "            mean_v = s.mean()",
            "            median_v = s.median()",
            "            mode_s = s.mode()",
            "            mode_v = mode_s.iloc[0] if len(mode_s) > 0 else None",
            "            std_v = s.std()",
            "            var_v = s.var()",
            "",
            "            html += '<table style=\"border-collapse:collapse; min-width:900px;\">'",
            "            html += f'<tr><th style=\"{ths}\">Statistic</th><th style=\"{ths} text-align:right;\">Value</th></tr>'",
            "            fmt = lambda v: f'{v:,.4f}' if v is not None and not (isinstance(v, float) and np.isnan(v)) else '—'",
            "            html += f'<tr><td style=\"{tds}\">Mean</td><td style=\"{tds_val}\">{fmt(mean_v)}</td></tr>'",
            "            html += f'<tr><td style=\"{tds}\">Median</td><td style=\"{tds_val}\">{fmt(median_v)}</td></tr>'",
            "            html += f'<tr><td style=\"{tds}\">Mode</td><td style=\"{tds_val}\">{fmt(mode_v)}</td></tr>'",
            "            html += f'<tr><td style=\"{tds}\">Standard Deviation</td><td style=\"{tds_val}\">{fmt(std_v)}</td></tr>'",
            "            html += f'<tr><td style=\"{tds}\">Variance</td><td style=\"{tds_val}\">{fmt(var_v)}</td></tr>'",
            "            html += '</table>'",
            "",
            "        elif vtype == 'Binary':",
            "            # Compute % of TRUE/Yes/1",
            "            clean = s.dropna()",
            "            if pd.api.types.is_numeric_dtype(clean) or pd.api.types.is_bool_dtype(clean):",
            "                true_count = int((clean.astype(bool)).sum())",
            "            else:",
            "                true_count = int(clean.astype(str).str.strip().str.lower().isin(['true', 'yes', '1']).sum())",
            "            total = len(clean)",
            "            pct = (true_count / total * 100) if total > 0 else 0",
            "",
            "            html += '<table style=\"border-collapse:collapse; min-width:900px;\">'",
            "            html += f'<tr><th style=\"{ths}\">Statistic</th><th style=\"{ths} text-align:right;\">Value</th></tr>'",
            "            html += f'<tr><td style=\"{tds}\">% TRUE / Yes / 1</td><td style=\"{tds_val}\">{pct:.2f}%</td></tr>'",
            "            html += '</table>'",
            "",
            "        else:  # Categorical",
            "            n_unique = s.nunique()",
            "            top2 = s.value_counts().head(2)",
            "",
            "            html += '<table style=\"border-collapse:collapse; min-width:900px;\">'",
            "            html += f'<tr><th style=\"{ths}\">Statistic</th><th style=\"{ths} text-align:right;\">Value</th></tr>'",
            "            html += f'<tr><td style=\"{tds}\">Unique Values</td><td style=\"{tds_val}\">{n_unique}</td></tr>'",
            "            for rank, (cat, cnt) in enumerate(top2.items(), 1):",
            "                html += f'<tr><td style=\"{tds}\">Top {rank}: {cat}</td><td style=\"{tds_val}\">{cnt:,}</td></tr>'",
            "            html += '</table>'",
            "",
            "        html += '</div>'",
            "",
            "    show_result('Descriptive Statistics', html)",
            "else:",
            "    for col in vars_to_analyze:",
            "        s = _pdf[col]",
            "        vtype = _classify(s)",
            "        print(f'\\n{col} (Type: {vtype}, Count: {s.count()})')",
            "        if vtype == 'Numeric':",
            "            print(f'  Mean={s.mean():.4f}  Median={s.median():.4f}  Mode={s.mode().iloc[0] if len(s.mode())>0 else None}')",
            "            print(f'  Std Dev={s.std():.4f}  Variance={s.var():.4f}')",
            "        elif vtype == 'Binary':",
            "            clean = s.dropna()",
            "            if pd.api.types.is_numeric_dtype(clean) or pd.api.types.is_bool_dtype(clean):",
            "                pct = clean.astype(bool).mean() * 100",
            "            else:",
            "                pct = clean.astype(str).str.strip().str.lower().isin(['true','yes','1']).mean() * 100",
            "            print(f'  % TRUE/Yes/1 = {pct:.2f}%')",
            "        else:",
            "            print(f'  Unique={s.nunique()}  Top 2: {s.value_counts().head(2).to_dict()}')",
        ]

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Descriptive Statistics Help",
            "Computes summary statistics for all selected variables.\n\n"
            "• Numeric: Mean, Median, Mode, Std Dev, Variance\n"
            "• Categorical: Unique count, Top 2 categories\n"
            "• Binary: % of TRUE/Yes/1\n\n"
            "Missing values are excluded from calculations."
        )
