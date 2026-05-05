"""Model Comparison Dashboard Dialog.

Trains multiple classifiers simultaneously and presents a ranked metrics table
and a combined ROC curve plot.
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
    QGridLayout,
)

from quantia.ui.dialogs.base import BaseAnalysisDialog


class ModelComparisonDialog(BaseAnalysisDialog):
    """Dialog for comparing multiple classification models."""

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Compare Classification Models", df, parent)
        self.btn_help.clicked.connect(self._show_help)

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        self.list_dependent = QListWidget()
        row_y = self._create_selector_row("Target Variable (Y) [Binary]:", self.list_dependent, multi_select=False)
        layout.addWidget(row_y)

        self.list_independent = QListWidget()
        row_x = self._create_selector_row("Features (X):", self.list_independent, multi_select=True)
        layout.addWidget(row_x)

    def build_options(self, layout: QVBoxLayout) -> None:
        # Models
        group_models = QGroupBox("Models to Compare")
        grid_models = QGridLayout(group_models)
        
        self.chk_models = {
            "Random Forest": QCheckBox("Random Forest"),
            "Gradient Boosting": QCheckBox("Gradient Boosting"),
            "Decision Tree": QCheckBox("Decision Tree"),
            "SVM": QCheckBox("SVM (Linear)"),
            "KNN": QCheckBox("K-Nearest Neighbors"),
            "LDA": QCheckBox("LDA"),
            "QDA": QCheckBox("QDA"),
            "Naive Bayes": QCheckBox("Naive Bayes")
        }
        
        # Check all by default
        for chk in self.chk_models.values():
            chk.setChecked(True)
            
        row, col = 0, 0
        for name, chk in self.chk_models.items():
            grid_models.addWidget(chk, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        layout.addWidget(group_models)

        # Validation & Preprocessing
        group_val = QGroupBox("Validation & Preprocessing")
        l_val = QVBoxLayout(group_val)
        
        l_val.addWidget(QLabel("Test Set Size (%):"))
        self.spin_test_size = QSpinBox()
        self.spin_test_size.setRange(5, 95)
        self.spin_test_size.setValue(20)
        l_val.addWidget(self.spin_test_size)
        
        self.chk_scale = QCheckBox("Scale Data (StandardScaler)")
        self.chk_scale.setChecked(True)
        l_val.addWidget(self.chk_scale)
        
        layout.addWidget(group_val)

        # Outputs
        group_out = QGroupBox("Outputs")
        l_out = QVBoxLayout(group_out)
        
        self.chk_table = QCheckBox("Comparison Table (Accuracy, Precision, Recall, F1, AUC)")
        self.chk_table.setChecked(True)
        l_out.addWidget(self.chk_table)
        
        self.chk_roc = QCheckBox("ROC Overlay Plot")
        self.chk_roc.setChecked(True)
        l_out.addWidget(self.chk_roc)
        
        layout.addWidget(group_out)

    def generate_code(self) -> str:
        if self.list_dependent.count() == 0 or self.list_independent.count() == 0:
            QMessageBox.warning(self, "Missing Input", "Please select Target (Y) and at least one Feature (X).")
            return ""

        target = self.list_dependent.item(0).text()
        features = [self.list_independent.item(i).text() for i in range(self.list_independent.count())]
        test_size = self.spin_test_size.value() / 100.0
        
        selected_models = [name for name, chk in self.chk_models.items() if chk.isChecked()]
        if not selected_models:
            QMessageBox.warning(self, "Missing Input", "Please select at least one model to compare.")
            return ""

        feat_str = ", ".join(f"'{f}'" for f in features)

        code = [
            f"# Model Comparison Dashboard",
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "from sklearn.model_selection import train_test_split",
            "from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, roc_curve"
        ]

        if self.chk_scale.isChecked():
            code.append("from sklearn.preprocessing import StandardScaler")

        code.append("\n# Prepare Data")
        code.append(f"features = [{feat_str}]")
        code.append(f"target = '{target}'")
        code.append("X = df[features].copy()")
        code.append("y = df[target].copy()")
        
        code.append("\n# Handle categorical features")
        code.append("X = pd.get_dummies(X, drop_first=True, dtype=float)")
        
        code.append("\n# Check if binary classification (for AUC/ROC)")
        code.append("is_binary = len(np.unique(y.dropna())) == 2")
        
        code.append("\n# Train/Test Split")
        code.append(f"X_train, X_test, y_train, y_test = train_test_split(X, y, test_size={test_size}, random_state=42, stratify=y)")
        
        if self.chk_scale.isChecked():
            code.append("\n# Scale Data")
            code.append("scaler = StandardScaler()")
            code.append("X_train = scaler.fit_transform(X_train)")
            code.append("X_test = scaler.transform(X_test)")

        code.append("\n# Initialize Models")
        code.append("models = {}")
        if "Random Forest" in selected_models:
            code.append("from sklearn.ensemble import RandomForestClassifier")
            code.append("models['Random Forest'] = RandomForestClassifier(random_state=42)")
        if "Gradient Boosting" in selected_models:
            code.append("from sklearn.ensemble import GradientBoostingClassifier")
            code.append("models['Gradient Boosting'] = GradientBoostingClassifier(random_state=42)")
        if "Decision Tree" in selected_models:
            code.append("from sklearn.tree import DecisionTreeClassifier")
            code.append("models['Decision Tree'] = DecisionTreeClassifier(random_state=42)")
        if "SVM" in selected_models:
            code.append("from sklearn.svm import SVC")
            code.append("models['SVM (Linear)'] = SVC(kernel='linear', probability=True, random_state=42)")
        if "KNN" in selected_models:
            code.append("from sklearn.neighbors import KNeighborsClassifier")
            code.append("models['KNN'] = KNeighborsClassifier()")
        if "LDA" in selected_models:
            code.append("from sklearn.discriminant_analysis import LinearDiscriminantAnalysis")
            code.append("models['LDA'] = LinearDiscriminantAnalysis()")
        if "QDA" in selected_models:
            code.append("from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis")
            code.append("models['QDA'] = QuadraticDiscriminantAnalysis()")
        if "Naive Bayes" in selected_models:
            code.append("from sklearn.naive_bayes import GaussianNB")
            code.append("models['Naive Bayes'] = GaussianNB()")

        code.append("\n# Train and Evaluate")
        code.append("results = []")
        code.append("roc_data = {}")
        code.append("for name, model in models.items():")
        code.append("    model.fit(X_train, y_train)")
        code.append("    y_pred = model.predict(X_test)")
        code.append("    ")
        code.append("    row = {")
        code.append("        'Model': name,")
        code.append("        'Accuracy': accuracy_score(y_test, y_pred),")
        code.append("        'Precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),")
        code.append("        'Recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),")
        code.append("        'F1 Score': f1_score(y_test, y_pred, average='weighted', zero_division=0)")
        code.append("    }")
        code.append("    ")
        code.append("    if is_binary and hasattr(model, 'predict_proba'):")
        code.append("        try:")
        code.append("            y_prob = model.predict_proba(X_test)[:, 1]")
        code.append("            row['AUC'] = roc_auc_score(y_test, y_prob)")
        code.append("            fpr, tpr, _ = roc_curve(y_test, y_prob)")
        code.append("            roc_data[name] = (fpr, tpr, row['AUC'])")
        code.append("        except:")
        code.append("            row['AUC'] = np.nan")
        code.append("    else:")
        code.append("        row['AUC'] = np.nan")
        code.append("        ")
        code.append("    results.append(row)")

        code.append("\n# Create Comparison Table")
        code.append("comp_df = pd.DataFrame(results).set_index('Model')")
        code.append("if not is_binary:")
        code.append("    comp_df = comp_df.drop(columns=['AUC'], errors='ignore')")
        code.append("comp_df = comp_df.sort_values('F1 Score', ascending=False).round(4)")

        code.append("\n# Format Output")
        code.append("html_output = []")
        code.append("html_output.append('<h3>Model Comparison Dashboard</h3>')")
        code.append(f"html_output.append(f'<p><b>Target:</b> {{target}}<br><b>Features:</b> {{len(features)}} selected<br><b>Test Size:</b> {test_size:.0%}</p>')")
        show_table = self.chk_table.isChecked()
        code.append(f"if {show_table}:")
        code.append("    html_output.append('<h4>Ranked by F1 Score</h4>')")
        code.append("    html_output.append(comp_df.to_html(classes='table table-sm table-hover table-striped'))")
        code.append("if 'display_html' in globals():")
        code.append("    display_html('\\n'.join(html_output))")
        code.append("elif 'show_result' in globals():")
        code.append(f"    show_result('Model Comparison', '\\n'.join(html_output))")
        code.append("else:")
        code.append("    print('\\n'.join(html_output))")

        if self.chk_roc.isChecked():
            code.append("\n# ROC Overlay Plot")
            code.append("if is_binary and roc_data:")
            code.append("    plt.figure(figsize=(8, 6))")
            code.append("    for name, (fpr, tpr, auc) in roc_data.items():")
            code.append("        plt.plot(fpr, tpr, label=f'{name} (AUC = {auc:.3f})')")
            code.append("    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)")
            code.append("    plt.xlabel('False Positive Rate')")
            code.append("    plt.ylabel('True Positive Rate')")
            code.append("    plt.title('ROC Curve Comparison')")
            code.append("    plt.legend(loc='lower right')")
            code.append("    plt.tight_layout()")
            code.append("    plt.show()")
            code.append("elif not is_binary:")
            code.append("    print('\\nNote: ROC Curve overlay is only available for binary classification targets.')")

        return "\n".join(code)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help: Model Comparison Dashboard",
            "Trains multiple classification models simultaneously and ranks them by performance.\n\n"
            "This is useful for quickly identifying which algorithm works best for your dataset before diving into hyperparameter tuning."
        )
