"""Tree-Based and Ensemble Regression Dialogs.

Provides Decision Tree and Random Forest Regressors with hyperparameter tuning
and diagnostic outputs (MSE, R2, Feature Importance, and plots).
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QListWidget, QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QFormLayout,
    QMessageBox
)
from PySide6.QtCore import Qt
import itertools

from quantia.ui.central.plot_styles import STYLE_NAMES, generate_style_code
from .base import BaseAnalysisDialog


class BaseTreeRegressionDialog(BaseAnalysisDialog):
    """Base dialog for tree-based regression models."""
    
    def __init__(self, title: str, df: pd.DataFrame, parent=None, supports_feature_importance: bool = True):
        self._supports_feature_importance = supports_feature_importance
        super().__init__(title, df, parent)
        
    def _build_selectors(self, layout: QVBoxLayout) -> None:
        """Add Dependent (Y) and Independent (X) variable selectors."""
        # Dependent Variable
        self.list_dependent = QListWidget()
        row_y = self._create_selector_row("Target Variable (Y):", self.list_dependent, multi_select=False)
        layout.addWidget(row_y)
        
        # Independent Variables
        self.list_independent = QListWidget()
        row_x = self._create_selector_row("Features (X):", self.list_independent, multi_select=True)
        layout.addWidget(row_x)
        
    def build_options(self, layout: QVBoxLayout) -> None:
        """Add validation, preprocessing, and model-specific hyperparameter options."""
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
        prep_layout.addWidget(self.chk_scale)
        prep_group.setLayout(prep_layout)
        layout.addWidget(prep_group)
        
        # Hyperparameters (implemented by subclasses)
        self.hp_group = QGroupBox("Hyperparameters")
        hp_layout = QFormLayout()
        self._build_hyperparameters(hp_layout)
        self.hp_group.setLayout(hp_layout)
        layout.addWidget(self.hp_group)

        # Outputs Group
        out_group = QGroupBox("Outputs")
        out_layout = QVBoxLayout()
        self.chk_metrics = QCheckBox("Regression Metrics (MSE, R\u00b2, MAE)")
        self.chk_metrics.setChecked(True)
        self.chk_plots = QCheckBox("Diagnostic Plots (Actual vs Predicted, Residuals)")
        self.chk_plots.setChecked(True)
        self.chk_feat_imp = QCheckBox("Feature Importance Plot")
        self.chk_feat_imp.setChecked(True)
        self.chk_feat_imp.setEnabled(self._supports_feature_importance)
        
        out_layout.addWidget(self.chk_metrics)
        out_layout.addWidget(self.chk_plots)
        out_layout.addWidget(self.chk_feat_imp)
        
        out_layout.addWidget(QLabel("Plot Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        self.cmb_style.setEnabled(True)
        out_layout.addWidget(self.cmb_style)
        
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)

    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        """To be overridden by subclasses."""
        pass
        
    def _get_imports(self) -> list[str]:
        """To be overridden by subclasses."""
        return []

    def _get_model_init_code(self) -> str:
        """To be overridden by subclasses."""
        return "model = None"

    def generate_code(self) -> str:
        """Generate Python code for the regression analysis."""
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
            f"# {self.windowTitle()}: {target} ~ {', '.join(features)}",
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "import io",
            "import base64",
            "from sklearn.model_selection import train_test_split",
            "from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error"
        ]
        code.extend(self._get_imports())
        code.append("")
        
        code.append("if isinstance(df, pl.DataFrame):")
        code.append(f"    combined = df.select([{', '.join([f'\"{f}\"' for f in features + [target]])}]).drop_nulls()")
        code.append(f"    X = combined.select([{', '.join([f'\"{f}\"' for f in features])}]).to_pandas()")
        code.append(f"    y = combined.select('{target}').to_pandas().iloc[:, 0]")
        code.append("else:")
        code.append(f"    combined = df[[{', '.join([f'\"{f}\"' for f in features + [target]])}]].dropna()")
        code.append(f"    X = combined[[{', '.join([f'\"{f}\"' for f in features])}]]")
        code.append(f"    y = combined['{target}']")
        code.append("")
        
        code.append("# Handle categorical features")
        code.append("X = pd.get_dummies(X, drop_first=True, dtype=float)")
        code.append("")
        
        code.append("# Train/Test Split")
        code.append(f"X_train, X_test, y_train, y_test = train_test_split(X, y, test_size={test_size}, random_state=42)")
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
            
        code.append("# Initialize and Train Model")
        code.append(self._get_model_init_code())
        code.append("model.fit(X_train, y_train)")
        code.append("")
        
        code.append("# Predictions")
        code.append("y_pred = model.predict(X_test)")
        code.append("")
        
        title = self.windowTitle()
        code.append("# Format Output")
        code.append("html_output = []")
        code.append(f"html_output.append('<h3>{title}</h3>')")
        code.append(f"html_output.append('<p><b>Target:</b> {target}<br><b>Features:</b> {len(features)} selected<br><b>Test Size:</b> {test_size:.0%}</p>')")
        
        if self.chk_metrics.isChecked():
            code.append("mse = mean_squared_error(y_test, y_pred)")
            code.append("rmse = np.sqrt(mse)")
            code.append("r2 = r2_score(y_test, y_pred)")
            code.append("mae = mean_absolute_error(y_test, y_pred)")
            
            code.append("metrics_html = f'''<table style=\"width:100%; margin-bottom:16px; border-collapse:collapse;\">")
            code.append("<tr>")
            code.append("  <td style=\"padding:10px; background:#F8FAFC; border:1px solid #F1F5F9; text-align:center;\"><div style=\"font-size:8pt; color:#94A3B8; font-weight:600;\">R-SQUARED</div><div style=\"font-size:13pt; font-weight:700;\">{r2:.4f}</div></td>")
            code.append("  <td style=\"padding:10px; background:#F8FAFC; border:1px solid #F1F5F9; text-align:center;\"><div style=\"font-size:8pt; color:#94A3B8; font-weight:600;\">RMSE</div><div style=\"font-size:13pt; font-weight:700;\">{rmse:.4f}</div></td>")
            code.append("  <td style=\"padding:10px; background:#F8FAFC; border:1px solid #F1F5F9; text-align:center;\"><div style=\"font-size:8pt; color:#94A3B8; font-weight:600;\">MAE</div><div style=\"font-size:13pt; font-weight:700;\">{mae:.4f}</div></td>")
            code.append("</tr></table>'''")
            code.append("html_output.append(metrics_html)")
            
        code.append("")
        if self.chk_plots.isChecked() or (self.chk_feat_imp.isChecked() and self._supports_feature_importance):
            style_code = generate_style_code(self.cmb_style.currentText())
            for line in style_code.split("\n"):
                if line.strip():
                    code.append(f"{line}")
            code.append("")

        code.append("plots_to_draw = []")
        if self.chk_plots.isChecked(): plots_to_draw.append("actual_vs_pred")
        if self.chk_plots.isChecked(): plots_to_draw.append("residuals")
        if self.chk_feat_imp.isChecked() and self._supports_feature_importance: plots_to_draw.append("feat_imp")
        
        code.append(f"plots_to_draw = {plots_to_draw}")
        code.append("if plots_to_draw:")
        code.append("    fig, axes = plt.subplots(1, len(plots_to_draw), figsize=(5 * len(plots_to_draw), 5))")
        code.append("    if len(plots_to_draw) == 1: axes = [axes]")
        code.append("    ax_idx = 0")
        code.append("")
        
        if self.chk_plots.isChecked():
            code.append("    # Actual vs Predicted")
            code.append("    if 'actual_vs_pred' in plots_to_draw:")
            code.append("        axes[ax_idx].scatter(y_test, y_pred, alpha=0.5)")
            code.append("        axes[ax_idx].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)")
            code.append("        axes[ax_idx].set_title('Actual vs Predicted')")
            code.append("        axes[ax_idx].set_xlabel('Actual')")
            code.append("        axes[ax_idx].set_ylabel('Predicted')")
            code.append("        ax_idx += 1")
            
            code.append("    # Residuals")
            code.append("    if 'residuals' in plots_to_draw:")
            code.append("        residuals = y_test - y_pred")
            code.append("        axes[ax_idx].scatter(y_pred, residuals, alpha=0.5)")
            code.append("        axes[ax_idx].axhline(y=0, color='r', linestyle='--', lw=2)")
            code.append("        axes[ax_idx].set_title('Residuals Plot')")
            code.append("        axes[ax_idx].set_xlabel('Predicted')")
            code.append("        axes[ax_idx].set_ylabel('Residuals')")
            code.append("        ax_idx += 1")

        if self.chk_feat_imp.isChecked() and self._supports_feature_importance:
            code.append("    # Feature Importance")
            code.append("    if 'feat_imp' in plots_to_draw and hasattr(model, 'feature_importances_'):")
            code.append("        importances = model.feature_importances_")
            code.append("        indices = np.argsort(importances)[::-1][:15]")
            code.append("        axes[ax_idx].bar(range(len(indices)), importances[indices], align='center')")
            code.append("        axes[ax_idx].set_xticks(range(len(indices)))")
            code.append("        axes[ax_idx].set_xticklabels([X.columns[i] for i in indices], rotation=45, ha='right')")
            code.append("        axes[ax_idx].set_title('Top Feature Importances')")
            code.append("        ax_idx += 1")
            
        code.append("    plt.tight_layout()")
        code.append("    buf = io.BytesIO()")
        code.append("    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')")
        code.append("    buf.seek(0)")
        code.append("    img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
        code.append("    plt.close()")
        code.append("    html_output.append(f'<div style=\"text-align:center; margin-top:20px;\"><img src=\"data:image/png;base64,{img_b64}\" style=\"max-width:100%; border:1px solid #E2E8F0; border-radius:4px;\"/></div>')")
        
        code.append("")
        code.append("if 'show_result' in globals():")
        code.append("    show_result(title, '\\n'.join(html_output))")
        code.append("else:")
        code.append("    print(title)")
        code.append("    if self.chk_metrics.isChecked():")
        code.append("        print(f'R2: {r2:.4f}, RMSE: {rmse:.4f}')")
            
        return "\n".join(code)


class DecisionTreeRegressorDialog(BaseTreeRegressionDialog):
    """Dialog for Decision Tree Regression."""
    
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Decision Tree Regression", df, parent)
        
    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        self.cmb_criterion = QComboBox()
        self.cmb_criterion.addItems(["squared_error", "friedman_mse", "absolute_error", "poisson"])
        layout.addRow("Criterion:", self.cmb_criterion)
        
        self.spin_max_depth = QSpinBox()
        self.spin_max_depth.setRange(0, 100)
        self.spin_max_depth.setValue(0)
        self.spin_max_depth.setSpecialValueText("None")
        layout.addRow("Max Depth:", self.spin_max_depth)
        
        self.spin_min_samples = QSpinBox()
        self.spin_min_samples.setRange(2, 100)
        self.spin_min_samples.setValue(2)
        layout.addRow("Min Samples Split:", self.spin_min_samples)
        
    def _get_imports(self) -> list[str]:
        return ["from sklearn.tree import DecisionTreeRegressor"]
        
    def _get_model_init_code(self) -> str:
        depth = self.spin_max_depth.value()
        depth_str = f"max_depth={depth}" if depth > 0 else "max_depth=None"
        return f"model = DecisionTreeRegressor(criterion='{self.cmb_criterion.currentText()}', {depth_str}, min_samples_split={self.spin_min_samples.value()}, random_state=42)"


class RandomForestRegressorDialog(BaseTreeRegressionDialog):
    """Dialog for Random Forest Regression."""
    
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Random Forest Regression", df, parent)
        
    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        self.spin_estimators = QSpinBox()
        self.spin_estimators.setRange(10, 1000)
        self.spin_estimators.setValue(100)
        self.spin_estimators.setSingleStep(10)
        layout.addRow("n_estimators:", self.spin_estimators)
        
        self.cmb_criterion = QComboBox()
        self.cmb_criterion.addItems(["squared_error", "absolute_error", "friedman_mse", "poisson"])
        layout.addRow("Criterion:", self.cmb_criterion)
        
        self.spin_max_depth = QSpinBox()
        self.spin_max_depth.setRange(0, 100)
        self.spin_max_depth.setValue(0)
        self.spin_max_depth.setSpecialValueText("None")
        layout.addRow("Max Depth:", self.spin_max_depth)
        
        self.chk_bootstrap = QCheckBox()
        self.chk_bootstrap.setChecked(True)
        layout.addRow("Bootstrap:", self.chk_bootstrap)
        
    def _get_imports(self) -> list[str]:
        return ["from sklearn.ensemble import RandomForestRegressor"]
        
    def _get_model_init_code(self) -> str:
        depth = self.spin_max_depth.value()
        depth_str = f"max_depth={depth}" if depth > 0 else "max_depth=None"
        return (f"model = RandomForestRegressor(n_estimators={self.spin_estimators.value()}, "
                f"criterion='{self.cmb_criterion.currentText()}', {depth_str}, "
                f"bootstrap={self.chk_bootstrap.isChecked()}, n_jobs=-1, random_state=42)")
