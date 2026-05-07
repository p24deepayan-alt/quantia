"""Principal Component Analysis (PCA) Dialog.

Performs dimensionality reduction, plots scree/biplots,
and can append PCs to the dataset.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class PCADialog(BaseAnalysisDialog):
    """Dialog for Principal Component Analysis."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Principal Component Analysis (PCA)", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_features = QListWidget()
        row_feat = self._create_selector_row("Features (Numeric):", self.list_features, multi_select=True)
        layout.addWidget(row_feat)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Settings
        group_set = QGroupBox("Settings")
        l_set = QVBoxLayout(group_set)
        
        l_set.addWidget(QLabel("Number of Components:"))
        self.spin_components = QSpinBox()
        self.spin_components.setRange(2, 50)
        self.spin_components.setValue(2)
        l_set.addWidget(self.spin_components)
        
        self.chk_scale = QCheckBox("Scale Data (StandardScaler)")
        self.chk_scale.setChecked(True)
        l_set.addWidget(self.chk_scale)
        
        layout.addWidget(group_set)

        # Outputs
        group_out = QGroupBox("Outputs")
        l_out = QVBoxLayout(group_out)
        
        self.chk_var_table = QCheckBox("Explained Variance Table")
        self.chk_var_table.setChecked(True)
        l_out.addWidget(self.chk_var_table)
        
        self.chk_scree = QCheckBox("Scree Plot")
        self.chk_scree.setChecked(True)
        l_out.addWidget(self.chk_scree)
        
        self.chk_biplot = QCheckBox("Biplot (PC1 vs PC2)")
        self.chk_biplot.setChecked(True)
        l_out.addWidget(self.chk_biplot)
        
        self.chk_append = QCheckBox("Append Principal Components to Dataset")
        self.chk_append.setChecked(False)
        l_out.addWidget(self.chk_append)
        
        layout.addWidget(group_out)

    def generate_code(self) -> str:
        features = [self.list_features.item(i).text() for i in range(self.list_features.count())]
        
        if len(features) < 2:
            QMessageBox.warning(self, "Missing Input", "Please select at least TWO numeric features for PCA.")
            return ""

        n_comp = self.spin_components.value()
        if n_comp > len(features):
            n_comp = len(features)

        feat_str = ", ".join(f"'{f}'" for f in features)

        code = [
            f"# Principal Component Analysis (PCA)",
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "from sklearn.decomposition import PCA"
        ]

        if self.chk_scale.isChecked():
            code.append("from sklearn.preprocessing import StandardScaler")

        code.append("\n# Prepare Data")
        code.append(f"features = [{feat_str}]")
        code.append("if isinstance(df, pl.DataFrame):")
        code.append("    # Extract data using Polars for speed, keeping track of rows if appending")
        code.append("    X_pd = df.select(features).drop_nulls().to_pandas()")
        code.append("else:")
        code.append("    X_pd = df[features].dropna()")
        
        if self.chk_scale.isChecked():
            code.append("X_scaled = StandardScaler().fit_transform(X_pd)")
        else:
            code.append("X_scaled = X_pd.values")

        code.append("\n# Fit PCA")
        code.append(f"pca = PCA(n_components={n_comp})")
        code.append("X_pca = pca.fit_transform(X_scaled)")

        # Output Text/HTML
        code.append("\n# Format Output")
        code.append("html_output = []")
        code.append(f"html_output.append('<h3>Principal Component Analysis</h3>')")
        code.append(f"html_output.append(f'<p><b>Features:</b> {{len(features)}}<br><b>Components:</b> {n_comp}</p>')")

        if self.chk_var_table.isChecked():
            code.append("var_df = pd.DataFrame({")
            code.append("    'Component': [f'PC{i+1}' for i in range(pca.n_components_)],")
            code.append("    'Explained Variance (%)': (pca.explained_variance_ratio_ * 100).round(2),")
            code.append("    'Cumulative Variance (%)': (pca.explained_variance_ratio_.cumsum() * 100).round(2)")
            code.append("})")
            code.append("html_output.append('<h4>Explained Variance</h4>')")
            code.append("html_output.append(var_df.to_html(index=False, classes='table table-sm table-striped'))")

        title = self.windowTitle()
        
        code.append("plots_to_draw = []")
        if self.chk_scree.isChecked(): code.append("plots_to_draw.append('scree')")
        if self.chk_biplot.isChecked(): code.append("plots_to_draw.append('biplot')")

        if self.chk_scree.isChecked() or self.chk_biplot.isChecked():
            code.append("\n# --- Plots ---")
            code.append("import io, base64")
            code.append("if plots_to_draw:")
            code.append("    for p_type in plots_to_draw:")
            code.append("        fig, ax = plt.subplots(figsize=(8, 8))")

            first_p = True
            if self.chk_scree.isChecked():
                code.append("        if p_type == 'scree':")
                code.append("            ax.bar(range(1, pca.n_components_ + 1), pca.explained_variance_ratio_ * 100, color='#2C3E8F')")
                code.append("            ax.plot(range(1, pca.n_components_ + 1), pca.explained_variance_ratio_.cumsum() * 100, 'ro-', label='Cumulative')")
                code.append("            ax.set_xlabel('Principal Component')")
                code.append("            ax.set_ylabel('Variance Explained (%)')")
                code.append("            ax.set_title('Scree Plot')")
                code.append("            ax.legend()")
                code.append("            ax.set_xticks(range(1, pca.n_components_ + 1))")
                first_p = False

            if self.chk_biplot.isChecked():
                if_str = "if" if first_p else "elif"
                code.append(f"        {if_str} p_type == 'biplot':")
                code.append("            ax.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.5, color='#26A69A')")
                code.append("            ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')")
                code.append("            if pca.n_components_ > 1:")
                code.append("                ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')")
                code.append("            ax.set_title('PCA Biplot')")
                
                code.append("            # Overlay loadings as arrows (scaled for visibility)")
                code.append("            if pca.n_components_ > 1:")
                code.append("                loadings = pca.components_.T * np.sqrt(pca.explained_variance_) * 2")
                code.append("                for i, feature in enumerate(features):")
                code.append("                    ax.arrow(0, 0, loadings[i, 0], loadings[i, 1], color='r', alpha=0.8, head_width=0.05)")
                code.append("                    ax.text(loadings[i, 0]*1.15, loadings[i, 1]*1.15, feature, color='darkred', ha='center', va='center')")
                code.append("                ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)")
                code.append("                ax.axvline(x=0, color='k', linestyle='--', alpha=0.3)")

            code.append("        plt.tight_layout()")
            code.append("        buf = io.BytesIO()")
            code.append("        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
            code.append("        plt.close(fig)")
            code.append("        buf.seek(0)")
            code.append("        img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
            code.append("        html_output.append(f'<div style=\"margin-top:24px; text-align:center;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>')")

        code.append("\nif 'show_result' in globals():")
        code.append(f"    show_result('{title}', '\\n'.join(html_output))")
        code.append("else:")
        code.append("    print('\\n'.join(html_output))")

        if self.chk_append.isChecked():
            code.append("\n# Append PCs to Dataset")
            code.append("if isinstance(df, pl.DataFrame):")
            code.append("    pc_names = [f'PC{i+1}' for i in range(pca.n_components_)]")
            code.append("    # To align correctly, we use row indices")
            code.append("    temp_df = df.with_row_index('__row_id__')")
            code.append("    valid_ids = temp_df.select(['__row_id__'] + features).drop_nulls().get_column('__row_id__')")
            code.append("    pcs_pl = pl.DataFrame(X_pca, schema=pc_names).with_columns(__row_id__ = valid_ids)")
            code.append("    df = temp_df.join(pcs_pl, on='__row_id__', how='left').drop('__row_id__')")
            code.append("else:")
            code.append("    for i in range(pca.n_components_):")
            # We align using the index of the dropna'd X_pd to avoid misaligning rows
            code.append(f"        df.loc[X_pd.index, f'PC{{i+1}}'] = X_pca[:, i]")
            code.append("print(f'\\nAppended {pca.n_components_} Principal Components to the dataset.')")

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: PCA",
            "Principal Component Analysis reduces the dimensionality of large data sets.\n\n"
            "It transforms a large set of variables into a smaller one that still contains most of the information in the large set."
        )
