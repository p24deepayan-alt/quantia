import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QListWidget, QAbstractItemView, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QFormLayout,
    QMessageBox
)
from PySide6.QtCore import Qt
from .base import BaseAnalysisDialog
from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from quantia.core.settings import SettingsManager, ComputeMode

class BaseClusteringDialog(BaseAnalysisDialog):
    """Base dialog for clustering models."""
    
    def __init__(self, title, df, parent=None, supports_dendrogram=False):
        self._supports_dendrogram = supports_dendrogram
        super().__init__(title, df, parent)
        
    def _build_selectors(self, layout):
        # Features (X)
        self.list_x = QListWidget()
        row_x = self._create_selector_row("Features (X):", self.list_x, multi_select=True)
        layout.addWidget(row_x)
        
    def build_options(self, layout):
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
        self.hyper_layout = QVBoxLayout()
        self._build_hyperparameters(self.hyper_layout)
        self.hyper_group.setLayout(self.hyper_layout)
        layout.addWidget(self.hyper_group)
            
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
        
        out_layout.addWidget(QLabel("Plot Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        out_layout.addWidget(self.cmb_style)
        
        self.chk_append = QCheckBox("Append Labels to Dataset")
        self.chk_append.setChecked(False)
        out_layout.addWidget(self.chk_append)
        
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)
        
    def _build_hyperparameters(self, layout):
        """Override this in subclasses to add hyperparameters."""
        pass
        
    def _get_model_init_code(self):
        """Override to return the scikit-learn model initialization code."""
        return "model = None # Override in subclass"
        
    def _get_summary_metrics(self):
        """Override to return model-specific summary metrics in HTML."""
        return []
        
    def _get_imports(self):
        """Override to return model-specific imports."""
        return []
        
    def generate_code(self):
        if self.list_x.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Feature (X).")
            return ""
            
        features = [self.list_x.item(i).text() for i in range(self.list_x.count())]
        scale_data = self.chk_scale.isChecked()
        plot_style = self.cmb_style.currentText()
        title = self.windowTitle()
        
        feature_list_str = ", ".join(f"'{f}'" for f in features)
        
        imports = [
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "import io, base64",
            "from sklearn.metrics import silhouette_score"
        ]
        
        if scale_data:
            imports.append("from sklearn.preprocessing import StandardScaler")
            
        if (self.chk_plot.isChecked() and len(features) > 2):
            imports.append("from sklearn.decomposition import PCA")
            
        imports.extend(self._get_imports())
        
        code = imports + [""]
        code.append(f"# Prepare Data for {title}")
        code.append(f"features = [{feature_list_str}]")
        code.append("if isinstance(df, pl.DataFrame):")
        code.append("    X_clean = df.select(features).drop_nulls().to_pandas()")
        code.append("else:")
        code.append("    X_clean = df[features].dropna()")
        code.append("")
        
        code.append("# Handle categorical features automatically")
        code.append("X = pd.get_dummies(X_clean, drop_first=True, dtype=float)")
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
        
        code.append("# Calculate Metrics")
        code.append("n_clusters = len(set(labels)) - (1 if -1 in labels else 0)")
        code.append("valid_idx = labels != -1")
        code.append("if sum(valid_idx) > 1 and len(np.unique(labels[valid_idx])) > 1:")
        
        settings = SettingsManager()
        n_jobs_metrics = -1 if settings.compute_mode == ComputeMode.CPU_MULTI else 1
        code.append(f"    sil_score = silhouette_score(X_train[valid_idx], labels[valid_idx], n_jobs={n_jobs_metrics})")
        code.append("else:")
        code.append("    sil_score = np.nan")
        code.append("")
        
        if self.chk_append.isChecked():
            code.append("# Append labels to original dataframe")
            code.append("if isinstance(df, pl.DataFrame):")
            code.append("    temp_df = df.with_row_index('__row_id__')")
            code.append("    valid_ids = temp_df.select(['__row_id__'] + features).drop_nulls().get_column('__row_id__')")
            code.append("    labels_pl = pl.DataFrame({'Cluster_Label': labels}).with_columns(__row_id__ = valid_ids)")
            code.append("    df = temp_df.join(labels_pl, on='__row_id__', how='left').drop('__row_id__')")
            code.append("else:")
            code.append("    df.loc[X_clean.index, 'Cluster_Label'] = labels")
            code.append("print(f'Added \\'Cluster_Label\\' column to main dataset.')")
            code.append("")
            
        # HTML Report building
        code.append("# ── Format Output ──")
        code.append("if 'show_result' in globals():")
        code.append("    sc = 'padding:10px 14px; background:#F8FAFC; border:1px solid #F1F5F9; text-align:center;'")
        code.append("    lb = 'font-size:8pt; color:#94A3B8; font-weight:600;'")
        code.append("    vl = 'font-size:13pt; font-weight:700; color:#111827; font-family:Consolas,monospace;'")
        
        code.append("    stats_html = f'''<table style=\"width:100%; margin-bottom:16px; border-collapse:collapse;\">")
        code.append("    <tr>")
        code.append(f"      <td style=\"{{sc}}\"><div style=\"{{lb}}\">CLUSTERS</div><div style=\"{{vl}}\">{{n_clusters}}</div></td>")
        code.append(f"      <td style=\"{{sc}}\"><div style=\"{{lb}}\">SILHOUETTE SCORE</div><div style=\"{{vl}}\">{{sil_score:.4f}}</div></td>")
        
        summary_metrics = self._get_summary_metrics()
        for label, val_code in summary_metrics:
            code.append(f"      <td style=\"{{sc}}\"><div style=\"{{lb}}\">{label.upper()}</div><div style=\"{{vl}}\">{{{val_code}}}</div></td>")
        
        code.append("    </tr></table>'''")
        
        code.append(f"    html_output = f'<h3>{title}</h3>' + stats_html")

        if self.chk_profile.isChecked():
            code.append("    # Cluster Profiles Table")
            code.append("    profile_df = X_clean.copy()")
            code.append("    profile_df['Cluster'] = labels")
            code.append("    means = profile_df.groupby('Cluster').mean().round(3)")
            code.append("    counts = profile_df.groupby('Cluster').size().rename('Count')")
            code.append("    summary_table = pd.concat([counts, means], axis=1)")

            code.append("    ths = 'padding:7px 10px; font-size:9pt; font-weight:700; color:#64748B; border-bottom:2px solid #CBD5E1; background:#F8FAFC;'")
            code.append("    html_output += '<h4>Cluster Profiles (Averages)</h4>'")
            code.append("    html_output += summary_table.to_html(classes='table table-sm table-striped', border=0)")

        code.append("    plots_to_draw = []")
        if self.chk_plot.isChecked(): code.append("    plots_to_draw.append('scatter')")
        if self.chk_dendrogram.isChecked() and self._supports_dendrogram: code.append("    plots_to_draw.append('dendrogram')")

        if self.chk_plot.isChecked() or (self.chk_dendrogram.isChecked() and self._supports_dendrogram):
            style_code = generate_style_code(plot_style)
            code.append("")
            code.append("    # ── Plots ──")
            for line in style_code.split("\n"):
                if line.strip(): code.append(f"    {line}")
                
            code.append("    if plots_to_draw:")
            code.append("        for p_type in plots_to_draw:")
            code.append("            fig, ax = plt.subplots(figsize=(8, 8))")
            
            first_p = True
            if self.chk_plot.isChecked():
                code.append("            if p_type == 'scatter':")
                if len(features) > 2:
                    code.append("                pca = PCA(n_components=2)")
                    code.append("                X_pca = pca.fit_transform(X_train)")
                    code.append("                scatter_df = pd.DataFrame({'PC1': X_pca[:, 0], 'PC2': X_pca[:, 1], 'Cluster': labels})")
                    code.append("                sns.scatterplot(data=scatter_df, x='PC1', y='PC2', hue='Cluster', palette='tab10', ax=ax, legend='full')")
                    code.append("                ax.set_title('Cluster Scatter (PCA 2D Projection)')")
                elif len(features) == 2:
                    code.append(f"                sns.scatterplot(data=X_train, x=X_train.columns[0], y=X_train.columns[1], hue=labels, palette='tab10', ax=ax, legend='full')")
                    code.append("                ax.set_title('Cluster Scatter Plot')")
                else:
                    code.append("                ax.text(0.5, 0.5, 'Need at least 2 features\\nfor scatter plot', ha='center', va='center')")
                first_p = False
                
            if self.chk_dendrogram.isChecked() and self._supports_dendrogram:
                if_str = "if" if first_p else "elif"
                code.append(f"            {if_str} p_type == 'dendrogram':")
                code.append("                from scipy.cluster.hierarchy import dendrogram")
                code.append("                def plot_dendrogram_internal(model, **kwargs):")
                code.append("                    counts = np.zeros(model.children_.shape[0])")
                code.append("                    n_samples = len(model.labels_)")
                code.append("                    for i, merge in enumerate(model.children_):")
                code.append("                        current_count = 0")
                code.append("                        for child_idx in merge:")
                code.append("                            if child_idx < n_samples:")
                code.append("                                current_count += 1")
                code.append("                            else:")
                code.append("                                current_count += counts[child_idx - n_samples]")
                code.append("                        counts[i] = current_count")
                code.append("                    linkage_matrix = np.column_stack([model.children_, model.distances_, counts]).astype(float)")
                code.append("                    dendrogram(linkage_matrix, **kwargs)")
                code.append("")
                code.append("                plot_dendrogram_internal(model, truncate_mode='level', p=5, ax=ax)")
                code.append("                ax.set_title('Hierarchical Dendrogram')")
                
            code.append("            plt.tight_layout()")
            code.append("            buf = io.BytesIO()")
            code.append("            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
            code.append("            plt.close(fig)")
            code.append("            buf.seek(0)")
            code.append("            img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
            code.append("            html_output += f'<div style=\"margin-top:24px; text-align:center;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>'")

        code.append(f"    show_result('{title}', html_output)")
        code.append("else:")
        code.append(f"    print(f'Clusters: {{n_clusters}}, Silhouette: {{sil_score:.4f}}')")
        
        return "\n".join(code)

class KMeansDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("K-Means Clustering", df, parent)
        
    def _build_hyperparameters(self, layout):
        # Auto-selection (Elbow Method)
        self.chk_auto = QCheckBox("Auto-select k (Elbow Method)")
        layout.addWidget(self.chk_auto)
        
        params_widget = QWidget()
        params_layout = QFormLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        
        self.spin_k = QSpinBox()
        self.spin_k.setRange(2, 100)
        self.spin_k.setValue(3)
        params_layout.addRow("Number of Clusters (k):", self.spin_k)
        
        self.spin_max_k = QSpinBox()
        self.spin_max_k.setRange(3, 20)
        self.spin_max_k.setValue(10)
        params_layout.addRow("Max k to test:", self.spin_max_k)
        self.spin_max_k.hide()
        
        layout.addWidget(params_widget)
        
        self.chk_auto.toggled.connect(lambda checked: self.spin_k.setVisible(not checked))
        self.chk_auto.toggled.connect(lambda checked: self.spin_max_k.setVisible(checked))
        
    def _get_imports(self):
        return ["from sklearn.cluster import KMeans"]
        
    def _get_summary_metrics(self):
        return [("WCSS (Inertia)", "model.inertia_:.1f")]
        
    def _get_model_init_code(self):
        if self.chk_auto.isChecked():
            settings = SettingsManager()
            n_jobs = -1 if settings.compute_mode == ComputeMode.CPU_MULTI else 1
            # Elbow method logic with parallel execution
            return (
                "from joblib import Parallel, delayed\n"
                "def get_inertia(k, data):\n"
                "    from sklearn.cluster import KMeans\n"
                "    km = KMeans(n_clusters=k, random_state=42, n_init=10)\n"
                "    km.fit(data)\n"
                "    return km.inertia_\n\n"
                f"k_range = range(1, {self.spin_max_k.value()} + 1)\n"
                f"wcss = Parallel(n_jobs={n_jobs})(delayed(get_inertia)(k, X_train) for k in k_range)\n\n"
                "# Simple elbow detection (max curvature)\n"
                "def find_elbow(k_values, wcss_values):\n"
                "    from numpy import diff\n"
                "    deltas = diff(wcss_values)\n"
                "    accels = diff(deltas)\n"
                "    return k_values[np.argmax(accels) + 1]\n\n"
                "best_k = find_elbow(list(k_range), wcss)\n"
                "print(f'Optimal k detected: {best_k}')\n"
                "model = KMeans(n_clusters=best_k, random_state=42, n_init=10)"
            )
        return f"model = KMeans(n_clusters={self.spin_k.value()}, random_state=42, n_init=10)"

class HierarchicalDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("Hierarchical Clustering", df, parent, supports_dendrogram=True)
        
    def _build_hyperparameters(self, layout):
        form = QFormLayout()
        self.spin_k = QSpinBox()
        self.spin_k.setRange(2, 100)
        self.spin_k.setValue(3)
        form.addRow("Number of Clusters:", self.spin_k)
        
        self.cmb_linkage = QComboBox()
        self.cmb_linkage.addItems(["ward", "complete", "average", "single"])
        form.addRow("Linkage:", self.cmb_linkage)
        layout.addLayout(form)
        
    def _get_imports(self):
        return ["from sklearn.cluster import AgglomerativeClustering"]
        
    def _get_model_init_code(self):
        # compute_distances=True is required to plot the dendrogram
        return f"model = AgglomerativeClustering(n_clusters={self.spin_k.value()}, linkage='{self.cmb_linkage.currentText()}', compute_distances=True)"

class DBSCANDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("DBSCAN Clustering", df, parent)
        
    def _build_hyperparameters(self, layout):
        form = QFormLayout()
        self.spin_eps = QDoubleSpinBox()
        self.spin_eps.setRange(0.01, 100.0)
        self.spin_eps.setValue(0.5)
        self.spin_eps.setSingleStep(0.1)
        form.addRow("Epsilon (Radius):", self.spin_eps)
        
        self.spin_min_samples = QSpinBox()
        self.spin_min_samples.setRange(2, 1000)
        self.spin_min_samples.setValue(5)
        form.addRow("Min Samples:", self.spin_min_samples)
        layout.addLayout(form)
        
    def _get_imports(self):
        return ["from sklearn.cluster import DBSCAN"]
        
    def _get_summary_metrics(self):
        # Calculate noise points count
        return [("Noise Points", "list(labels).count(-1)")]
        
    def _get_model_init_code(self):
        return f"model = DBSCAN(eps={self.spin_eps.value()}, min_samples={self.spin_min_samples.value()})"

class GMMDialog(BaseClusteringDialog):
    def __init__(self, df, parent=None):
        super().__init__("Gaussian Mixture Model (GMM)", df, parent)
        
    def _build_hyperparameters(self, layout):
        form = QFormLayout()
        self.spin_k = QSpinBox()
        self.spin_k.setRange(2, 100)
        self.spin_k.setValue(3)
        form.addRow("Number of Components:", self.spin_k)
        
        self.cmb_covariance = QComboBox()
        self.cmb_covariance.addItems(["full", "tied", "diag", "spherical"])
        form.addRow("Covariance Type:", self.cmb_covariance)
        layout.addLayout(form)
        
    def _get_imports(self):
        return ["from sklearn.mixture import GaussianMixture"]
        
    def _get_summary_metrics(self):
        return [("AIC", "model.aic(X_train):.1f"), ("BIC", "model.bic(X_train):.1f")]
        
    def _get_model_init_code(self):
        return f"model = GaussianMixture(n_components={self.spin_k.value()}, covariance_type='{self.cmb_covariance.currentText()}', random_state=42)"
