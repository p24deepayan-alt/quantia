import pandas as pd
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QListWidget, QAbstractItemView, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QFormLayout
)
from PySide6.QtCore import Qt
from .base import BaseAnalysisDialog

class BaseClusteringDialog(BaseAnalysisDialog):
    """Base dialog for clustering models."""
    
    def __init__(self, title, df, parent=None, supports_dendrogram=False):
        self._supports_dendrogram = supports_dendrogram
        super().__init__(title, df, parent)
        
    def _build_selectors(self, layout):
        # Features (X)
        layout.addWidget(QLabel("Features (X):"))
        self.list_x = QListWidget()
        self.list_x.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_x.addItems(self.df.columns)
        layout.addWidget(self.list_x)
        
    def _build_options(self, layout):
        # Preprocessing Group
        prep_group = QGroupBox("Preprocessing")
        prep_layout = QVBoxLayout()
        self.chk_scale = QCheckBox("Scale Data (StandardScaler)")
        self.chk_scale.setChecked(True) # Highly recommended for clustering
        prep_layout.addWidget(self.chk_scale)
        prep_group.setLayout(prep_layout)
        layout.addWidget(prep_group)
        
        # Hyperparameters Group
        self.hyper_group = QGroupBox("Hyperparameters")
        self.hyper_layout = QFormLayout()
        self._build_hyperparameters(self.hyper_layout)
        self.hyper_group.setLayout(self.hyper_layout)
        if self.hyper_layout.rowCount() > 0:
            layout.addWidget(self.hyper_group)
        else:
            self.hyper_group.hide()
            
        # Outputs Group
        out_group = QGroupBox("Outputs")
        out_layout = QVBoxLayout()
        
        self.chk_profile = QCheckBox("Cluster Profile (Means)")
        self.chk_profile.setChecked(True)
        out_layout.addWidget(self.chk_profile)
        
        self.chk_plot = QCheckBox("2D Scatter Plot (PCA if >2 vars)")
        self.chk_plot.setChecked(True)
        out_layout.addWidget(self.chk_plot)
        
        self.chk_dendrogram = QCheckBox("Dendrogram")
        self.chk_dendrogram.setChecked(True)
        if not self._supports_dendrogram:
            self.chk_dendrogram.setEnabled(False)
            self.chk_dendrogram.setChecked(False)
            self.chk_dendrogram.hide()
        out_layout.addWidget(self.chk_dendrogram)
        
        self.chk_append = QCheckBox("Append Labels to Dataset")
        self.chk_append.setChecked(False)
        out_layout.addWidget(self.chk_append)
        
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)
        
    def _build_hyperparameters(self, layout):
        """Override this in subclasses to add hyperparameters to the form layout."""
        pass
        
    def _get_model_init_code(self):
        """Override to return the scikit-learn model initialization code."""
        return "model = None # Override in subclass"
        
    def _get_imports(self):
        """Override to return model-specific imports."""
        return []
        
    def generate_code(self):
        if not self.list_x.selectedItems():
            return "# Please select at least one Feature (X)."
            
        features = [item.text() for item in self.list_x.selectedItems()]
        scale_data = self.chk_scale.isChecked()
        
        feature_list_str = ", ".join(f"'{f}'" for f in features)
        
        imports = [
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "from sklearn.metrics import silhouette_score"
        ]
        
        if scale_data:
            imports.append("from sklearn.preprocessing import StandardScaler")
            
        if self.chk_plot.isChecked() and len(features) > 2:
            imports.append("from sklearn.decomposition import PCA")
            
        imports.extend(self._get_imports())
        
        code = imports + [""]
        code.append(f"# Prepare Data for {self.windowTitle()}")
        code.append(f"features = [{feature_list_str}]")
        code.append("X = df[features].copy()")
        code.append("")
        
        code.append("# Handle categorical features automatically")
        code.append("X = pd.get_dummies(X, drop_first=True, dtype=float)")
        code.append("")
        
        if scale_data:
            code.append("# Scale Data (Distance-based metrics require scaling)")
            code.append("scaler = StandardScaler()")
            code.append("X_scaled = scaler.fit_transform(X)")
            code.append("X_train = pd.DataFrame(X_scaled, columns=X.columns)")
            code.append("")
        else:
            code.append("X_train = X.copy()")
            code.append("")
            
        code.append("# Initialize and Fit Model")
        code.append(self._get_model_init_code())
        code.append("labels = model.fit_predict(X_train)")
        code.append("")
        
        code.append("# Calculate Silhouette Score (ignoring noise labels '-1' in DBSCAN if present)")
        code.append("valid_idx = labels != -1")
        code.append("if sum(valid_idx) > 1 and len(np.unique(labels[valid_idx])) > 1:")
        code.append("    sil_score = silhouette_score(X_train[valid_idx], labels[valid_idx])")
        code.append("else:")
        code.append("    sil_score = np.nan")
        code.append("")
        
        if self.chk_append.isChecked():
            code.append("# Append labels to original dataframe")
            code.append("df['Cluster_Label'] = labels")
            code.append("print(f'Added \\'Cluster_Label\\' column to main dataset.')")
            code.append("")
            
        # HTML Report building
        code.append("# Format Output")
        code.append("html_output = []")
        code.append(f"html_output.append('<h3>{self.windowTitle()}</h3>')")
        code.append("n_clusters = len(set(labels)) - (1 if -1 in labels else 0)")
        code.append("html_output.append(f'<p><b>Features:</b> {len(features)} selected<br><b>Clusters Found:</b> {n_clusters}<br><b>Silhouette Score:</b> {sil_score:.3f}</p>')")
        
        if self.chk_profile.isChecked():
            code.append("# Calculate Cluster Profiles (Means of original unscaled features)")
            code.append("profile_df = df[features].copy()")
            code.append("profile_df['Cluster'] = labels")
            code.append("means = profile_df.groupby('Cluster').mean().round(3)")
            code.append("counts = profile_df.groupby('Cluster').size().rename('Count')")
            code.append("summary_table = pd.concat([counts, means], axis=1)")
            code.append("html_output.append('<h4>Cluster Profiles (Averages)</h4>')")
            code.append("html_output.append(summary_table.to_html(classes='table table-sm table-striped'))")
            
            code.append("if 'display_html' in globals():")
            code.append("    display_html('\\n'.join(html_output))")
            code.append("elif 'show_result' in globals():")
            code.append(f"    show_result('{self.windowTitle()}', '\\n'.join(html_output))")
            code.append("else:")
            code.append("    print('\\n'.join(html_output))")
        code.append("")
        
        plots_to_draw = []
        if self.chk_plot.isChecked(): plots_to_draw.append("scatter")
        if self.chk_dendrogram.isChecked() and self._supports_dendrogram: plots_to_draw.append("dendro")
        
        if plots_to_draw:
            code.append(f"fig, axes = plt.subplots(1, {len(plots_to_draw)}, figsize=({6 * len(plots_to_draw)}, 5))")
            code.append(f"if {len(plots_to_draw)} == 1: axes = [axes]")
            code.append("ax_idx = 0")
            code.append("")
            
            if self.chk_plot.isChecked():
                code.append("# 2D Scatter Plot")
                if len(features) > 2:
                    code.append("pca = PCA(n_components=2)")
                    code.append("X_pca = pca.fit_transform(X_train)")
                    code.append("scatter_df = pd.DataFrame({'PC1': X_pca[:, 0], 'PC2': X_pca[:, 1], 'Cluster': labels})")
                    code.append("sns.scatterplot(data=scatter_df, x='PC1', y='PC2', hue='Cluster', palette='tab10', ax=axes[ax_idx], legend='full')")
                    code.append("axes[ax_idx].set_title('Cluster Scatter (PCA 2D Projection)')")
                elif len(features) == 2:
                    code.append(f"sns.scatterplot(data=X_train, x=X_train.columns[0], y=X_train.columns[1], hue=labels, palette='tab10', ax=axes[ax_idx], legend='full')")
                    code.append("axes[ax_idx].set_title('Cluster Scatter Plot')")
                else:
                    code.append("axes[ax_idx].text(0.5, 0.5, 'Need at least 2 features\\nfor scatter plot', ha='center', va='center')")
                code.append("ax_idx += 1")
                code.append("")
                
            if self.chk_dendrogram.isChecked() and self._supports_dendrogram:
                code.append("# Dendrogram")
                code.append("from scipy.cluster.hierarchy import dendrogram")
                code.append("def plot_dendrogram(model, **kwargs):")
                code.append("    counts = np.zeros(model.children_.shape[0])")
                code.append("    n_samples = len(model.labels_)")
                code.append("    for i, merge in enumerate(model.children_):")
                code.append("        current_count = 0")
                code.append("        for child_idx in merge:")
                code.append("            if child_idx < n_samples:")
                code.append("                current_count += 1")
                code.append("            else:")
                code.append("                current_count += counts[child_idx - n_samples]")
                code.append("        counts[i] = current_count")
                code.append("    linkage_matrix = np.column_stack([model.children_, model.distances_, counts]).astype(float)")
                code.append("    dendrogram(linkage_matrix, **kwargs)")
                code.append("")
                code.append("plot_dendrogram(model, truncate_mode='level', p=5, ax=axes[ax_idx])")
                code.append("axes[ax_idx].set_title('Hierarchical Dendrogram')")
                code.append("ax_idx += 1")
                
            code.append("plt.tight_layout()")
            code.append("plt.show()")
            
        return "\n".join(code)

class KMeansDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("K-Means Clustering", df, parent)
        
    def _build_hyperparameters(self, layout):
        self.spin_k = QSpinBox()
        self.spin_k.setRange(2, 100)
        self.spin_k.setValue(3)
        layout.addRow("Number of Clusters (k):", self.spin_k)
        
    def _get_imports(self):
        return ["from sklearn.cluster import KMeans"]
        
    def _get_model_init_code(self):
        return f"model = KMeans(n_clusters={self.spin_k.value()}, random_state=42)"

class HierarchicalDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("Hierarchical Clustering", df, parent, supports_dendrogram=True)
        
    def _build_hyperparameters(self, layout):
        self.spin_k = QSpinBox()
        self.spin_k.setRange(2, 100)
        self.spin_k.setValue(3)
        layout.addRow("Number of Clusters:", self.spin_k)
        
        self.cmb_linkage = QComboBox()
        self.cmb_linkage.addItems(["ward", "complete", "average", "single"])
        layout.addRow("Linkage:", self.cmb_linkage)
        
    def _get_imports(self):
        return ["from sklearn.cluster import AgglomerativeClustering"]
        
    def _get_model_init_code(self):
        # compute_distances=True is required to plot the dendrogram
        return f"model = AgglomerativeClustering(n_clusters={self.spin_k.value()}, linkage='{self.cmb_linkage.currentText()}', compute_distances=True)"

class DBSCANDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("DBSCAN Clustering", df, parent)
        
    def _build_hyperparameters(self, layout):
        self.spin_eps = QDoubleSpinBox()
        self.spin_eps.setRange(0.01, 100.0)
        self.spin_eps.setValue(0.5)
        self.spin_eps.setSingleStep(0.1)
        layout.addRow("Epsilon (Radius):", self.spin_eps)
        
        self.spin_min_samples = QSpinBox()
        self.spin_min_samples.setRange(2, 1000)
        self.spin_min_samples.setValue(5)
        layout.addRow("Min Samples:", self.spin_min_samples)
        
    def _get_imports(self):
        return ["from sklearn.cluster import DBSCAN"]
        
    def _get_model_init_code(self):
        return f"model = DBSCAN(eps={self.spin_eps.value()}, min_samples={self.spin_min_samples.value()})"

class GMMDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("Gaussian Mixture Model (GMM)", df, parent)
        
    def _build_hyperparameters(self, layout):
        self.spin_k = QSpinBox()
        self.spin_k.setRange(2, 100)
        self.spin_k.setValue(3)
        layout.addRow("Number of Components:", self.spin_k)
        
        self.cmb_covariance = QComboBox()
        self.cmb_covariance.addItems(["full", "tied", "diag", "spherical"])
        layout.addRow("Covariance Type:", self.cmb_covariance)
        
    def _get_imports(self):
        return ["from sklearn.mixture import GaussianMixture"]
        
    def _get_model_init_code(self):
        return f"model = GaussianMixture(n_components={self.spin_k.value()}, covariance_type='{self.cmb_covariance.currentText()}', random_state=42)"
