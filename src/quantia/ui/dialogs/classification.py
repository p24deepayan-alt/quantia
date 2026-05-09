import pandas as pd
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QListWidget, QAbstractItemView, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QFormLayout,
    QMessageBox
)
from PySide6.QtCore import Qt
from quantia.core.settings import SettingsManager, ComputeMode
from .base import BaseAnalysisDialog

class BaseClassificationDialog(BaseAnalysisDialog):
    """Base dialog for classification models."""
    
    def __init__(self, title, df, parent=None, mandatory_scaling=False, supports_feature_importance=False):
        self._mandatory_scaling = mandatory_scaling
        self._supports_feature_importance = supports_feature_importance
        super().__init__(title, df, parent)
        
    def _build_selectors(self, layout):
        # Target Variable
        self.list_dependent = QListWidget()
        row_y = self._create_selector_row("Target Variable (Y):", self.list_dependent, multi_select=False)
        layout.addWidget(row_y)
        
        # Features
        self.list_independent = QListWidget()
        row_x = self._create_selector_row("Features (X):", self.list_independent, multi_select=True)
        layout.addWidget(row_x)
        
    def build_options(self, layout):
        # Validation Group
        val_group = QGroupBox("Validation")
        val_layout = QVBoxLayout()
        
        form_val = QFormLayout()
        self.spin_test_size = QSpinBox()
        self.spin_test_size.setRange(5, 95)
        self.spin_test_size.setValue(20)
        self.spin_test_size.setSuffix("%")
        form_val.addRow("Test Set Size:", self.spin_test_size)
        val_layout.addLayout(form_val)
        val_group.setLayout(val_layout)
        layout.addWidget(val_group)
        
        # Preprocessing Group
        prep_group = QGroupBox("Preprocessing")
        prep_layout = QVBoxLayout()
        self.chk_scale = QCheckBox("Scale Data (StandardScaler)")
        self.chk_scale.setChecked(self._mandatory_scaling)
        if self._mandatory_scaling: self.chk_scale.setEnabled(False)
        prep_layout.addWidget(self.chk_scale)
        prep_group.setLayout(prep_layout)
        layout.addWidget(prep_group)
        
        # Outputs Group
        out_group = QGroupBox("Outputs")
        out_layout = QVBoxLayout()
        self.chk_report = QCheckBox("Classification Report")
        self.chk_report.setChecked(True)
        self.chk_cm = QCheckBox("Confusion Matrix")
        self.chk_roc = QCheckBox("ROC Curve")
        self.chk_feat_imp = QCheckBox("Feature Importance")
        self.chk_feat_imp.setEnabled(self._supports_feature_importance)
        out_layout.addWidget(self.chk_report)
        out_layout.addWidget(self.chk_cm)
        out_layout.addWidget(self.chk_roc)
        out_layout.addWidget(self.chk_feat_imp)
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)
        
        # Hyperparameters (Subclasses)
        self.hp_group = QGroupBox("Hyperparameters")
        hp_layout = QFormLayout()
        self._build_hyperparameters(hp_layout)
        self.hp_group.setLayout(hp_layout)
        layout.addWidget(self.hp_group)

    def _build_hyperparameters(self, layout):
        pass
        
    def _add_extra_plots_logic(self, code):
        """Override to add custom plot logic before the main loop."""
        pass

    def _add_extra_plots_rendering(self, code):
        """Override to add custom plot rendering inside the main loop."""
        pass
        
    def _get_imports(self):
        """Override to return model-specific imports."""
        return []

    def _get_model_init_code(self):
        """Override to return model initialization code."""
        return "model = None"

    def _get_model_train_code(self):
        return [
            "# Initialize and Train Model",
            self._get_model_init_code(),
            "model.fit(X_train, y_train)"
        ]

    def generate_code(self):
        if self.list_dependent.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select a Target Variable (Y).")
            return ""
        if self.list_independent.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select at least one Feature (X).")
            return ""
            
        target = self.list_dependent.item(0).text()
        features = [self.list_independent.item(i).text() for i in range(self.list_independent.count())]
        test_size = self.spin_test_size.value() / 100.0
        scale_data = self.chk_scale.isChecked()
        
        code = [
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "import io",
            "import base64",
            "from sklearn.model_selection import train_test_split",
            "from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc",
            f"features = {features}",
        ]
        code.extend(self._get_imports())
        code.append("")
        
        code.append("if isinstance(df, pl.DataFrame):")
        code.append(f"    # Extract and clean data using Polars")
        code.append(f"    combined = df.select([{', '.join([f'\"{f}\"' for f in features + [target]])}]).drop_nulls()")
        code.append(f"    X = combined.select([{', '.join([f'\"{f}\"' for f in features])}]).to_pandas()")
        code.append(f"    y = combined.select('{target}').to_pandas().iloc[:, 0]")
        code.append("else:")
        code.append(f"    # Standard Pandas extraction and cleaning")
        code.append(f"    combined = df[[{', '.join([f'\"{f}\"' for f in features + [target]])}]].dropna()")
        code.append(f"    X = combined[[{', '.join([f'\"{f}\"' for f in features])}]]")
        code.append(f"    y = combined['{target}']")
        code.append("")
        
        code.append("# Handle categorical features")
        code.append("X = pd.get_dummies(X, drop_first=True, dtype=float)")
        code.append("")
        
        code.append("# Train/Test Split")
        code.append(f"X_train, X_test, y_train, y_test = train_test_split(X, y, test_size={test_size}, random_state=42, stratify=y)")
        code.append("")
        
        if scale_data:
            code.append("# Scale Data")
            code.append("from sklearn.preprocessing import StandardScaler")
            code.append("scaler = StandardScaler()")
            code.append("X_train = scaler.fit_transform(X_train)")
            code.append("X_test = scaler.transform(X_test)")
            code.append("X_train = pd.DataFrame(X_train, columns=X.columns)")
            code.append("X_test = pd.DataFrame(X_test, columns=X.columns)")
            code.append("")
            
        code.extend(self._get_model_train_code())
        code.append("")
        
        code.append("# Predictions")
        code.append("y_pred = model.predict(X_test)")
        code.append("try:")
        code.append("    y_prob = model.predict_proba(X_test)")
        code.append("except AttributeError:")
        code.append("    y_prob = None")
        code.append("")
        
        title = self.windowTitle()
        # HTML Report building
        code.append("# Format Output")
        code.append("html_output = []")
        code.append(f"html_output.append('<h3>{title}</h3>')")
        code.append(f"html_output.append('<p><b>Target:</b> {target}<br><b>Features:</b> {len(features)} selected<br><b>Test Size:</b> {test_size:.0%}</p>')")
        
        if self.chk_report.isChecked():
            code.append("report_dict = classification_report(y_test, y_pred, output_dict=True)")
            code.append("report_df = pd.DataFrame(report_dict).transpose().round(3)")
            code.append("html_output.append('<h4>Classification Report</h4>')")
            code.append("html_output.append(report_df.to_html(classes='table table-sm table-striped'))")
            
        code.append("")
        code.append("# Build plots_to_draw dynamically inside the generated script")
        code.append("plots_to_draw = []")
        if self.chk_cm.isChecked(): code.append("plots_to_draw.append('cm')")
        if self.chk_roc.isChecked(): code.append("if len(np.unique(y)) == 2: plots_to_draw.append('roc')")
        if self.chk_feat_imp.isChecked() and self._supports_feature_importance: code.append("plots_to_draw.append('feat_imp')")
        
        # Hook for extra plots from subclasses
        self._add_extra_plots_logic(code)
        
        code.append("if plots_to_draw:")
        code.append("    for p_type in plots_to_draw:")
        code.append("        fig, ax = plt.subplots(figsize=(8, 8))")
        
        first_p = True
        if self.chk_cm.isChecked():
            code.append("        if p_type == 'cm':")
            code.append("            cm = confusion_matrix(y_test, y_pred)")
            code.append("            classes = model.classes_")
            code.append("            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, xticklabels=classes, yticklabels=classes)")
            code.append("            ax.set_title('Confusion Matrix')")
            code.append("            ax.set_xlabel('Predicted')")
            code.append("            ax.set_ylabel('Actual')")
            first_p = False
        
        if self.chk_roc.isChecked():
            if_str = "if" if first_p else "elif"
            code.append(f"        {if_str} p_type == 'roc':")
            code.append("            classes = model.classes_")
            code.append("            pos_class = classes[1]")
            code.append("            y_test_bin = (y_test == pos_class).astype(int)")
            code.append("            fpr, tpr, _ = roc_curve(y_test_bin, y_prob[:, 1])")
            code.append("            roc_auc = auc(fpr, tpr)")
            code.append("            ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')")
            code.append("            ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')")
            code.append("            ax.set_xlim([0.0, 1.0])")
            code.append("            ax.set_ylim([0.0, 1.05])")
            code.append("            ax.set_xlabel('False Positive Rate')")
            code.append("            ax.set_ylabel('True Positive Rate')")
            code.append("            ax.set_title(f'ROC Curve (Positive: {pos_class})')")
            code.append("            ax.legend(loc='lower right')")
            first_p = False
        
        if self.chk_feat_imp.isChecked() and self._supports_feature_importance:
            if_str = "if" if first_p else "elif"
            code.append(f"        {if_str} p_type == 'feat_imp' and hasattr(model, 'feature_importances_'):")
            code.append("            importances = model.feature_importances_")
            code.append("            indices = np.argsort(importances)[::-1][:15]")
            code.append("            ax.bar(range(len(indices)), importances[indices], align='center')")
            code.append("            ax.set_xticks(range(len(indices)))")
            code.append("            ax.set_xticklabels([X.columns[i] for i in indices], rotation=45, ha='right')")
            code.append("            ax.set_title('Top Feature Importances')")
            first_p = False
            
        self._add_extra_plots_rendering(code)

        code.append("        plt.tight_layout()")
        code.append("        buf = io.BytesIO()")
        code.append("        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
        code.append("        buf.seek(0)")
        code.append("        img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
        code.append("        if \'register_figure\' in globals():")
        code.append("            register_figure(img_b64, fig)")
        code.append("        plt.close(fig)")
        code.append("        html_output.append(f'<div style=\"text-align:center; margin-top:20px;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>')")

        code.append("")
        code.append("if 'display_html' in globals():")
        code.append("    display_html('\\n'.join(html_output))")
        code.append("elif 'show_result' in globals():")
        code.append(f"    show_result('{title}', '\\n'.join(html_output))")
        code.append("else:")
        code.append("    print('\\n'.join(html_output))")
        code.append("")            
        return "\n".join(code)

class RandomForestDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Random Forest Classifier", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout):
        self.spin_estimators = QSpinBox()
        self.spin_estimators.setRange(10, 1000)
        self.spin_estimators.setValue(100)
        self.spin_estimators.setSingleStep(10)
        layout.addRow("N Estimators:", self.spin_estimators)
        # Criterion
        self.cmb_criterion = QComboBox()
        self.cmb_criterion.addItems(["gini", "entropy", "log_loss"])
        layout.addRow("Criterion:", self.cmb_criterion)
        # Max Depth
        self.chk_auto_depth = QCheckBox("Automatic (Unlimited)")
        self.chk_auto_depth.setChecked(True)
        self.spin_depth = QSpinBox()
        self.spin_depth.setRange(1, 100)
        self.spin_depth.setValue(10)
        self.spin_depth.setEnabled(False)
        self.chk_auto_depth.toggled.connect(self.spin_depth.setDisabled)
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(self.chk_auto_depth)
        depth_layout.addWidget(self.spin_depth)
        layout.addRow("Max Depth:", depth_layout)
        
    def _get_imports(self):
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.ensemble", "RandomForestClassifier", "cuml.ensemble")
        
    def _get_model_init_code(self):
        settings = SettingsManager()
        mode = settings.compute_mode
        n_jobs = 1
        if mode == ComputeMode.CPU_MULTI:
            n_jobs = -1
        depth = "None" if self.chk_auto_depth.isChecked() else self.spin_depth.value()
        return (f"model = RandomForestClassifier(\n"
                f"    n_estimators={self.spin_estimators.value()}, \n"
                f"    criterion='{self.cmb_criterion.currentText()}', \n"
                f"    max_depth={depth}, \n"
                f"    n_jobs={n_jobs}, \n"
                f"    random_state=42\n"
                f")")

class GradientBoostingDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Gradient Boosting Classifier", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout):
        self.spin_estimators = QSpinBox()
        self.spin_estimators.setRange(10, 1000)
        self.spin_estimators.setValue(100)
        layout.addRow("N Estimators (max_iter):", self.spin_estimators)
        
        self.spin_lr = QDoubleSpinBox()
        self.spin_lr.setRange(0.001, 1.0)
        self.spin_lr.setValue(0.1)
        self.spin_lr.setSingleStep(0.05)
        layout.addRow("Learning Rate:", self.spin_lr)

        self.spin_depth = QSpinBox()
        self.spin_depth.setRange(1, 100)
        self.spin_depth.setValue(3)
        layout.addRow("Max Depth:", self.spin_depth)
        
    def _get_imports(self):
        return ["from sklearn.ensemble import HistGradientBoostingClassifier"]
        
    def _get_model_init_code(self):
        return (f"model = HistGradientBoostingClassifier(\n"
                f"    max_iter={self.spin_estimators.value()}, \n"
                f"    learning_rate={self.spin_lr.value()}, \n"
                f"    max_depth={self.spin_depth.value()}, \n"
                f"    random_state=42\n"
                f")")

class DecisionTreeDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        # Initialize chk_tree BEFORE super().__init__ because super().__init__ 
        # calls build_options, which uses chk_tree.
        self.chk_tree = QCheckBox("Plot Tree Visualization")
        self.chk_tree.setChecked(False)
        
        super().__init__("Decision Tree Classifier", df, parent, supports_feature_importance=True)
        
    def build_options(self, layout):
        super().build_options(layout)
        # Find the Outputs group and add the checkbox
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if isinstance(item.widget(), QGroupBox) and item.widget().title() == "Outputs":
                item.widget().layout().addWidget(self.chk_tree)
                break
        
    def _build_hyperparameters(self, layout):
        # Criterion
        self.cmb_criterion = QComboBox()
        self.cmb_criterion.addItems(["gini", "entropy", "log_loss"])
        layout.addRow("Criterion:", self.cmb_criterion)

        # Max Depth
        self.chk_auto_depth = QCheckBox("Automatic (Unlimited)")
        self.chk_auto_depth.setChecked(True)
        self.spin_depth = QSpinBox()
        self.spin_depth.setRange(1, 100)
        self.spin_depth.setValue(10)
        self.spin_depth.setEnabled(False)
        self.chk_auto_depth.toggled.connect(self.spin_depth.setDisabled)
        
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(self.chk_auto_depth)
        depth_layout.addWidget(self.spin_depth)
        layout.addRow("Max Depth:", depth_layout)

        # Pruning
        self.chk_auto_ccp = QCheckBox("Optimize (CV)")
        self.chk_auto_ccp.setChecked(False)
        self.spin_ccp = QDoubleSpinBox()
        self.spin_ccp.setRange(0.0, 1.0)
        self.spin_ccp.setValue(0.0)
        self.spin_ccp.setSingleStep(0.01)
        self.spin_ccp.setDecimals(3)
        self.chk_auto_ccp.toggled.connect(self.spin_ccp.setDisabled)
        
        prune_layout = QHBoxLayout()
        prune_layout.addWidget(self.chk_auto_ccp)
        prune_layout.addWidget(self.spin_ccp)
        layout.addRow("Pruning (ccp_alpha):", prune_layout)

        # Min Samples Split
        self.spin_min_split = QSpinBox()
        self.spin_min_split.setRange(2, 100)
        self.spin_min_split.setValue(2)
        layout.addRow("Min Samples Split:", self.spin_min_split)
        
    def _get_imports(self):
        return ["from sklearn.tree import DecisionTreeClassifier, plot_tree"]
        
    def _add_extra_plots_logic(self, code):
        if self.chk_tree.isChecked():
            code.append("plots_to_draw.append('tree')")

    def _add_extra_plots_rendering(self, code):
        if self.chk_tree.isChecked():
            code.append("        # Tree Visualization")
            code.append("        elif p_type == 'tree':")
            code.append("            # Re-generate tree plot with custom size")
            code.append("            plt.close(fig)")
            code.append("            fig, ax = plt.subplots(figsize=(20, 10))")
            code.append("            plot_tree(model, feature_names=X.columns, class_names=[str(c) for c in model.classes_], filled=True, rounded=True, ax=ax)")
            code.append("            ax.set_title('Decision Tree Structure')")
            code.append("            plt.tight_layout()")
            code.append("            buf = io.BytesIO()")
            code.append("            fig.savefig(buf, format='png', dpi=200, bbox_inches='tight')")
            code.append("            buf.seek(0)")
            code.append("            img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
            code.append("            if \'register_figure\' in globals():")
            code.append("                register_figure(img_b64, fig)")
            code.append("            plt.close(fig)")
            code.append("            html_output.append(f'<div style=\"text-align:center; margin-top:20px;\"><img src=\"data:image/png;base64,{img_b64}\" style=\"width:100%; max-width:2000px; border:1px solid #E2E8F0; border-radius:4px;\"/></div>')")
            # Signal the loop to skip the default append logic
            code.append("            continue")
            
    def _get_model_init_code(self):
        depth = "None" if self.chk_auto_depth.isChecked() else self.spin_depth.value()
        return (f"model = DecisionTreeClassifier(\n"
                f"    criterion='{self.cmb_criterion.currentText()}', \n"
                f"    max_depth={depth}, \n"
                f"    ccp_alpha={self.spin_ccp.value()}, \n"
                f"    min_samples_split={self.spin_min_split.value()}, \n"
                f"    random_state=42\n"
                f")")

    def _get_model_train_code(self):
        if not self.chk_auto_ccp.isChecked():
            return super()._get_model_train_code()
            
        depth = "None" if self.chk_auto_depth.isChecked() else self.spin_depth.value()
        
        settings = SettingsManager()
        n_jobs = -1 if settings.compute_mode == ComputeMode.CPU_MULTI else 1
        
        code = [
            "# Optimize CCP Alpha via Cross-Validation",
            "from sklearn.model_selection import GridSearchCV",
            "if 'html_output' not in locals(): html_output = []",
            f"base_tree = DecisionTreeClassifier(criterion='{self.cmb_criterion.currentText()}', max_depth={depth}, min_samples_split={self.spin_min_split.value()}, random_state=42)",
            "",
            "# Compute pruning path to find candidate alphas",
            "path = base_tree.cost_complexity_pruning_path(X_train, y_train)",
            "ccp_alphas = path.ccp_alphas",
            "",
            "# Grid search over the candidates",
            f"grid_search = GridSearchCV(base_tree, param_grid={{'ccp_alpha': ccp_alphas}}, cv=5, scoring='f1_weighted', n_jobs={n_jobs})",
            "grid_search.fit(X_train, y_train)",
            "",
            "model = grid_search.best_estimator_",
            "optimal_alpha = grid_search.best_params_['ccp_alpha']",
            "print(f'Optimal ccp_alpha found: {optimal_alpha:.4f}')",
            "html_output.append(f'<p><b>Optimal ccp_alpha found via CV:</b> {optimal_alpha:.4f}</p>')"
        ]
        return code

class SVMDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Support Vector Machine (SVM)", df, parent, mandatory_scaling=True)
        
    def _build_hyperparameters(self, layout):
        self.cmb_kernel = QComboBox()
        self.cmb_kernel.addItems(["rbf", "linear", "poly", "sigmoid"])
        layout.addRow("Kernel:", self.cmb_kernel)
        
        self.spin_c = QDoubleSpinBox()
        self.spin_c.setRange(0.01, 1000.0)
        self.spin_c.setValue(1.0)
        layout.addRow("C (Regularization):", self.spin_c)

        # Gamma
        self.cmb_gamma = QComboBox()
        self.cmb_gamma.addItems(["scale", "auto"])
        layout.addRow("Gamma:", self.cmb_gamma)
        
    def _get_imports(self):
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.svm", "SVC", "cuml.svm")
        
    def _get_model_init_code(self):
        return (f"model = SVC(\n"
                f"    kernel='{self.cmb_kernel.currentText()}', \n"
                f"    C={self.spin_c.value()}, \n"
                f"    gamma='{self.cmb_gamma.currentText()}', \n"
                f"    probability=True, \n"
                f"    random_state=42\n"
                f")")

class KNNDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("K-Nearest Neighbors (KNN)", df, parent, mandatory_scaling=True)
        
    def _build_hyperparameters(self, layout):
        self.spin_neighbors = QSpinBox()
        self.spin_neighbors.setRange(1, 100)
        self.spin_neighbors.setValue(5)
        layout.addRow("N Neighbors:", self.spin_neighbors)
        
        self.cmb_weights = QComboBox()
        self.cmb_weights.addItems(["uniform", "distance"])
        layout.addRow("Weights:", self.cmb_weights)

        self.cmb_algorithm = QComboBox()
        self.cmb_algorithm.addItems(["auto", "ball_tree", "kd_tree", "brute"])
        layout.addRow("Algorithm:", self.cmb_algorithm)
        
    def _get_imports(self):
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.neighbors", "KNeighborsClassifier", "cuml.neighbors")
        
    def _get_model_init_code(self):
        settings = SettingsManager()
        mode = settings.compute_mode
        n_jobs = 1
        if mode == ComputeMode.CPU_MULTI:
            n_jobs = -1
            
        return (f"model = KNeighborsClassifier(\n"
                f"    n_neighbors={self.spin_neighbors.value()}, \n"
                f"    weights='{self.cmb_weights.currentText()}', \n"
                f"    algorithm='{self.cmb_algorithm.currentText()}', \n"
                f"    n_jobs={n_jobs}\n"
                f")")

class LDADialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Linear Discriminant Analysis (LDA)", df, parent)
        
    def _get_imports(self):
        return ["from sklearn.discriminant_analysis import LinearDiscriminantAnalysis"]
        
    def _get_model_init_code(self):
        return "model = LinearDiscriminantAnalysis()"

class QDADialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Quadratic Discriminant Analysis (QDA)", df, parent)
        
    def _get_imports(self):
        return ["from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis"]
        
    def _get_model_init_code(self):
        return "model = QuadraticDiscriminantAnalysis()"

class NaiveBayesDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Naive Bayes (Gaussian)", df, parent)
        
    def _get_imports(self):
        return ["from sklearn.naive_bayes import GaussianNB"]
        
    def _get_model_init_code(self):
        return "model = GaussianNB()"
