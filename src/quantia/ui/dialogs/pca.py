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
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "from sklearn.decomposition import PCA"
        ]

        if self.chk_scale.isChecked():
            code.append("from sklearn.preprocessing import StandardScaler")

        code.append("\n# Prepare Data")
        code.append(f"features = [{feat_str}]")
        code.append("X = df[features].copy()")
        code.append("X = X.dropna() # PCA cannot handle missing values")
        
        if self.chk_scale.isChecked():
            code.append("X_scaled = StandardScaler().fit_transform(X)")
        else:
            code.append("X_scaled = X.values")

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
        if 'display_html' in globals():
            code.append("display_html('\\n'.join(html_output))")
        elif 'show_result' in globals():
            code.append(f"show_result('{title}', '\\n'.join(html_output))")
        else:
            code.append("print('\\n'.join(html_output))")

        if self.chk_append.isChecked():
            code.append("\n# Append PCs to Dataset")
            code.append("for i in range(pca.n_components_):")
            # We align using the index of the dropna'd X to avoid misaligning rows
            code.append(f"    df.loc[X.index, f'PC{{i+1}}'] = X_pca[:, i]")
            code.append("print(f'\\nAppended {pca.n_components_} Principal Components to the dataset.')")

        plots_to_draw = []
        if self.chk_scree.isChecked(): plots_to_draw.append("scree")
        if self.chk_biplot.isChecked(): plots_to_draw.append("biplot")

        if plots_to_draw:
            code.append(f"\nfig, axes = plt.subplots(1, {len(plots_to_draw)}, figsize=({6 * len(plots_to_draw)}, 5))")
            code.append(f"if {len(plots_to_draw)} == 1: axes = [axes]")
            code.append("ax_idx = 0\n")

            if self.chk_scree.isChecked():
                code.append("# Scree Plot")
                code.append("axes[ax_idx].bar(range(1, pca.n_components_ + 1), pca.explained_variance_ratio_ * 100, color='#2C3E8F')")
                code.append("axes[ax_idx].plot(range(1, pca.n_components_ + 1), pca.explained_variance_ratio_.cumsum() * 100, 'ro-', label='Cumulative')")
                code.append("axes[ax_idx].set_xlabel('Principal Component')")
                code.append("axes[ax_idx].set_ylabel('Variance Explained (%)')")
                code.append("axes[ax_idx].set_title('Scree Plot')")
                code.append("axes[ax_idx].legend()")
                code.append("axes[ax_idx].set_xticks(range(1, pca.n_components_ + 1))")
                code.append("ax_idx += 1\n")

            if self.chk_biplot.isChecked():
                code.append("# Biplot (PC1 vs PC2)")
                code.append("axes[ax_idx].scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.5, color='#26A69A')")
                code.append("axes[ax_idx].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')")
                code.append("if pca.n_components_ > 1:")
                code.append("    axes[ax_idx].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')")
                code.append("axes[ax_idx].set_title('PCA Biplot')")
                
                code.append("\n# Overlay loadings as arrows (scaled for visibility)")
                code.append("if pca.n_components_ > 1:")
                code.append("    loadings = pca.components_.T * np.sqrt(pca.explained_variance_) * 2")
                code.append("    for i, feature in enumerate(features):")
                code.append("        axes[ax_idx].arrow(0, 0, loadings[i, 0], loadings[i, 1], color='r', alpha=0.8, head_width=0.05)")
                code.append("        axes[ax_idx].text(loadings[i, 0]*1.15, loadings[i, 1]*1.15, feature, color='darkred', ha='center', va='center')")
                code.append("    axes[ax_idx].axhline(y=0, color='k', linestyle='--', alpha=0.3)")
                code.append("    axes[ax_idx].axvline(x=0, color='k', linestyle='--', alpha=0.3)")

            code.append("\nplt.tight_layout()")
            code.append("plt.show()")

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: PCA",
            "Principal Component Analysis reduces the dimensionality of large data sets.\n\n"
            "It transforms a large set of variables into a smaller one that still contains most of the information in the large set."
        )
