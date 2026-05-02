import pandas as pd
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QListWidget, QAbstractItemView, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QFormLayout
)
from PySide6.QtCore import Qt
from .base import BaseAnalysisDialog

class BaseClassificationDialog(BaseAnalysisDialog):
    """Base dialog for classification models."""
    
    def __init__(self, title, df, parent=None, mandatory_scaling=False, supports_feature_importance=False):
        self._mandatory_scaling = mandatory_scaling
        self._supports_feature_importance = supports_feature_importance
        super().__init__(title, df, parent)
        
    def _build_selectors(self, layout):
        # Target Variable
        layout.addWidget(QLabel("Target Variable (Y):"))
        self.list_y = QListWidget()
        self.list_y.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_y.addItems(self.df.columns)
        layout.addWidget(self.list_y)
        
        # Features
        layout.addWidget(QLabel("Features (X):"))
        self.list_x = QListWidget()
        self.list_x.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_x.addItems(self.df.columns)
        layout.addWidget(self.list_x)
        
    def _build_options(self, layout):
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
        if self._mandatory_scaling:
            self.chk_scale.setChecked(True)
            self.chk_scale.setEnabled(False)
            self.chk_scale.setToolTip("Scaling is mandatory for this algorithm.")
        else:
            self.chk_scale.setChecked(False)
        prep_layout.addWidget(self.chk_scale)
        prep_group.setLayout(prep_layout)
        layout.addWidget(prep_group)
        
        # Hyperparameters Group (subclasses can populate this)
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
        self.chk_report = QCheckBox("Classification Report")
        self.chk_report.setChecked(True)
        out_layout.addWidget(self.chk_report)
        
        self.chk_cm = QCheckBox("Confusion Matrix")
        self.chk_cm.setChecked(True)
        out_layout.addWidget(self.chk_cm)
        
        self.chk_roc = QCheckBox("ROC Curve (Binary only)")
        self.chk_roc.setChecked(True)
        out_layout.addWidget(self.chk_roc)
        
        self.chk_feat_imp = QCheckBox("Feature Importance")
        self.chk_feat_imp.setChecked(True)
        if not self._supports_feature_importance:
            self.chk_feat_imp.setEnabled(False)
            self.chk_feat_imp.setChecked(False)
        out_layout.addWidget(self.chk_feat_imp)
        
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
        if not self.list_y.selectedItems() or not self.list_x.selectedItems():
            return "# Please select Target (Y) and at least one Feature (X)."
            
        target = self.list_y.selectedItems()[0].text()
        features = [item.text() for item in self.list_x.selectedItems()]
        test_size = self.spin_test_size.value() / 100.0
        scale_data = self.chk_scale.isChecked()
        
        feature_list_str = ", ".join(f"'{f}'" for f in features)
        
        imports = [
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "from sklearn.model_selection import train_test_split",
            "from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc"
        ]
        
        if scale_data:
            imports.append("from sklearn.preprocessing import StandardScaler")
            
        imports.extend(self._get_imports())
        
        code = imports + [""]
        code.append(f"# Prepare Data for {self.windowTitle()}")
        code.append(f"features = [{feature_list_str}]")
        code.append(f"target = '{target}'")
        code.append("X = df[features].copy()")
        code.append("y = df[target].copy()")
        code.append("")
        
        code.append("# Handle categorical features")
        code.append("X = pd.get_dummies(X, drop_first=True, dtype=float)")
        code.append("")
        
        code.append("# Train/Test Split")
        code.append(f"X_train, X_test, y_train, y_test = train_test_split(X, y, test_size={test_size}, random_state=42, stratify=y)")
        code.append("")
        
        if scale_data:
            code.append("# Scale Data")
            code.append("scaler = StandardScaler()")
            code.append("X_train = scaler.fit_transform(X_train)")
            code.append("X_test = scaler.transform(X_test)")
            code.append("X_train = pd.DataFrame(X_train, columns=X.columns) # Retain column names")
            code.append("X_test = pd.DataFrame(X_test, columns=X.columns)")
            code.append("")
            
        code.append("# Initialize and Train Model")
        code.append(self._get_model_init_code())
        code.append("model.fit(X_train, y_train)")
        code.append("")
        
        code.append("# Predictions")
        code.append("y_pred = model.predict(X_test)")
        code.append("try:")
        code.append("    y_prob = model.predict_proba(X_test)")
        code.append("except AttributeError:")
        code.append("    y_prob = None # Model doesn't support probability estimates")
        code.append("")
        
        # HTML Report building
        code.append("# Format Output")
        code.append("html_output = []")
        code.append(f"html_output.append('<h3>{self.windowTitle()}</h3>')")
        code.append(f"html_output.append('<p><b>Target:</b> {target}<br><b>Features:</b> {len(features)} selected<br><b>Test Size:</b> {test_size:.0%}</p>')")
        
        if self.chk_report.isChecked():
            code.append("report_dict = classification_report(y_test, y_pred, output_dict=True)")
            code.append("report_df = pd.DataFrame(report_dict).transpose().round(3)")
            code.append("html_output.append('<h4>Classification Report</h4>')")
            code.append("html_output.append(report_df.to_html(classes='table table-sm table-striped'))")
            
        code.append("display_html('\\n'.join(html_output))")
        code.append("")
        
        plots_to_draw = []
        if self.chk_cm.isChecked(): plots_to_draw.append("cm")
        if self.chk_roc.isChecked(): plots_to_draw.append("roc")
        if self.chk_feat_imp.isChecked() and self._supports_feature_importance: plots_to_draw.append("feat_imp")
        
        if plots_to_draw:
            code.append(f"fig, axes = plt.subplots(1, {len(plots_to_draw)}, figsize=({5 * len(plots_to_draw)}, 5))")
            code.append(f"if {len(plots_to_draw)} == 1: axes = [axes]")
            code.append("ax_idx = 0")
            code.append("")
            
            if self.chk_cm.isChecked():
                code.append("# Confusion Matrix")
                code.append("cm = confusion_matrix(y_test, y_pred)")
                code.append("sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[ax_idx])")
                code.append("axes[ax_idx].set_title('Confusion Matrix')")
                code.append("axes[ax_idx].set_xlabel('Predicted')")
                code.append("axes[ax_idx].set_ylabel('Actual')")
                code.append("ax_idx += 1")
                code.append("")
                
            if self.chk_roc.isChecked():
                code.append("# ROC Curve")
                code.append("if len(np.unique(y)) == 2 and y_prob is not None:")
                code.append("    # Convert y_test to binary if it's not already (for ROC)")
                code.append("    classes = model.classes_")
                code.append("    pos_class = classes[1] # Assume second class is positive")
                code.append("    y_test_bin = (y_test == pos_class).astype(int)")
                code.append("    fpr, tpr, _ = roc_curve(y_test_bin, y_prob[:, 1])")
                code.append("    roc_auc = auc(fpr, tpr)")
                code.append("    axes[ax_idx].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')")
                code.append("    axes[ax_idx].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')")
                code.append("    axes[ax_idx].set_xlim([0.0, 1.0])")
                code.append("    axes[ax_idx].set_ylim([0.0, 1.05])")
                code.append("    axes[ax_idx].set_xlabel('False Positive Rate')")
                code.append("    axes[ax_idx].set_ylabel('True Positive Rate')")
                code.append("    axes[ax_idx].set_title(f'ROC Curve (Positive: {pos_class})')")
                code.append("    axes[ax_idx].legend(loc='lower right')")
                code.append("else:")
                code.append("    axes[ax_idx].text(0.5, 0.5, 'ROC only supported\\nfor binary targets\\nwith probabilities', ha='center', va='center')")
                code.append("    axes[ax_idx].set_title('ROC Curve')")
                code.append("ax_idx += 1")
                code.append("")
                
            if self.chk_feat_imp.isChecked() and self._supports_feature_importance:
                code.append("# Feature Importance")
                code.append("if hasattr(model, 'feature_importances_'):")
                code.append("    importances = model.feature_importances_")
                code.append("    indices = np.argsort(importances)[::-1][:15] # Top 15")
                code.append("    axes[ax_idx].bar(range(len(indices)), importances[indices], align='center')")
                code.append("    axes[ax_idx].set_xticks(range(len(indices)))")
                code.append("    axes[ax_idx].set_xticklabels(X.columns[indices], rotation=45, ha='right')")
                code.append("    axes[ax_idx].set_title('Top Feature Importances')")
                code.append("else:")
                code.append("    axes[ax_idx].text(0.5, 0.5, 'Feature Importance\\nNot Available', ha='center', va='center')")
                code.append("ax_idx += 1")
                
            code.append("plt.tight_layout()")
            code.append("plt.show()")
            
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
        
    def _get_imports(self):
        return ["from sklearn.ensemble import RandomForestClassifier"]
        
    def _get_model_init_code(self):
        return f"model = RandomForestClassifier(n_estimators={self.spin_estimators.value()}, random_state=42)"

class GradientBoostingDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Gradient Boosting Classifier", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout):
        self.spin_estimators = QSpinBox()
        self.spin_estimators.setRange(10, 1000)
        self.spin_estimators.setValue(100)
        layout.addRow("N Estimators:", self.spin_estimators)
        
        self.spin_lr = QDoubleSpinBox()
        self.spin_lr.setRange(0.001, 1.0)
        self.spin_lr.setValue(0.1)
        self.spin_lr.setSingleStep(0.05)
        layout.addRow("Learning Rate:", self.spin_lr)
        
    def _get_imports(self):
        return ["from sklearn.ensemble import GradientBoostingClassifier"]
        
    def _get_model_init_code(self):
        return f"model = GradientBoostingClassifier(n_estimators={self.spin_estimators.value()}, learning_rate={self.spin_lr.value()}, random_state=42)"

class DecisionTreeDialog(BaseClassificationDialog):
    def __init__(self, df, parent=None):
        super().__init__("Decision Tree Classifier", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout):
        self.spin_depth = QSpinBox()
        self.spin_depth.setRange(0, 100) # 0 means None
        self.spin_depth.setValue(0)
        self.spin_depth.setSpecialValueText("None (Unlimited)")
        layout.addRow("Max Depth:", self.spin_depth)
        
    def _get_imports(self):
        return ["from sklearn.tree import DecisionTreeClassifier"]
        
    def _get_model_init_code(self):
        depth = self.spin_depth.value()
        depth_val = depth if depth > 0 else "None"
        return f"model = DecisionTreeClassifier(max_depth={depth_val}, random_state=42)"

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
        
    def _get_imports(self):
        return ["from sklearn.svm import SVC"]
        
    def _get_model_init_code(self):
        return f"model = SVC(kernel='{self.cmb_kernel.currentText()}', C={self.spin_c.value()}, probability=True, random_state=42)"

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
        
    def _get_imports(self):
        return ["from sklearn.neighbors import KNeighborsClassifier"]
        
    def _get_model_init_code(self):
        return f"model = KNeighborsClassifier(n_neighbors={self.spin_neighbors.value()}, weights='{self.cmb_weights.currentText()}')"

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
