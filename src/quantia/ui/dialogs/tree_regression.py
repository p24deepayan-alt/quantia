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
from quantia.core.settings import SettingsManager, ComputeMode
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
        
        self._add_extra_outputs(out_layout)

        out_layout.addWidget(QLabel("Plot Style:"))
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(STYLE_NAMES)
        self.cmb_style.setEnabled(True)
        out_layout.addWidget(self.cmb_style)
        
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)

    def _add_extra_outputs(self, layout: QVBoxLayout) -> None:
        """To be overridden by subclasses."""
        pass

    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        """To be overridden by subclasses."""
        pass
        
    def _get_imports(self) -> list[str]:
        """To be overridden by subclasses."""
        return []

    def _get_model_init_code(self) -> str:
        """To be overridden by subclasses."""
        return "model = None"

    def _add_extra_plots_logic(self, code: list[str]) -> None:
        """To be overridden by subclasses."""
        pass

    def _add_extra_plots_rendering(self, code: list[str]) -> None:
        """To be overridden by subclasses."""
        pass

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
            "from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error",
            f"features = {features}",
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
        
        code.append("")
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
        if self.chk_plots.isChecked(): code.append("plots_to_draw.append('actual_vs_pred')")
        if self.chk_plots.isChecked(): code.append("plots_to_draw.append('residuals')")
        if self.chk_feat_imp.isChecked() and self._supports_feature_importance: code.append("plots_to_draw.append('feat_imp')")
        self._add_extra_plots_logic(code)
        
        code.append("if plots_to_draw:")
        code.append("    for p_type in plots_to_draw:")
        code.append("        fig, ax = plt.subplots(figsize=(8, 8))")
        
        first_p = True
        if self.chk_plots.isChecked():
            code.append("        if p_type == 'actual_vs_pred':")
            code.append("            ax.scatter(y_test, y_pred, alpha=0.5)")
            code.append("            ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)")
            code.append("            ax.set_title('Actual vs Predicted')")
            code.append("            ax.set_xlabel('Actual')")
            code.append("            ax.set_ylabel('Predicted')")
            
            code.append("        elif p_type == 'residuals':")
            code.append("            residuals = y_test - y_pred")
            code.append("            ax.scatter(y_pred, residuals, alpha=0.5)")
            code.append("            ax.axhline(y=0, color='r', linestyle='--', lw=2)")
            code.append("            ax.set_title('Residuals Plot')")
            code.append("            ax.set_xlabel('Predicted')")
            code.append("            ax.set_ylabel('Residuals')")
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
        code.append("        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
        code.append("        buf.seek(0)")
        code.append("        img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
        code.append("        if \'register_figure\' in globals():")
        code.append("            register_figure(img_b64, fig)")
        code.append("        plt.close(fig)")
        code.append("        html_output.append(f'<div style=\"text-align:center; margin-top:20px;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>')")

        
        code.append("")
        code.append("if 'show_result' in globals():")
        code.append(f"    show_result('{title}', '\\n'.join(html_output))")
        code.append("else:")
        code.append(f"    print('{title}')")
        if self.chk_metrics.isChecked():
            code.append("    print(f'R2: {r2:.4f}, RMSE: {rmse:.4f}')")
            
        return "\n".join(code)


class DecisionTreeRegressorDialog(BaseTreeRegressionDialog):
    """Dialog for Decision Tree Regression."""
    
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Decision Tree Regression", df, parent)
        
    def _add_extra_outputs(self, layout: QVBoxLayout) -> None:
        self.chk_tree = QCheckBox("Plot Tree Visualization")
        self.chk_tree.setChecked(False)
        layout.addWidget(self.chk_tree)

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
        
        self.chk_optimize_ccp = QCheckBox("Optimize CCP Alpha (Auto-pruning)")
        self.chk_optimize_ccp.setChecked(False)
        layout.addRow(self.chk_optimize_ccp)
        
        self.spin_ccp_alpha = QDoubleSpinBox()
        self.spin_ccp_alpha.setRange(0.0, 10.0)
        self.spin_ccp_alpha.setDecimals(4)
        self.spin_ccp_alpha.setSingleStep(0.001)
        self.spin_ccp_alpha.setValue(0.0)
        layout.addRow("CCP Alpha:", self.spin_ccp_alpha)
        
        # Connect visibility
        self.chk_optimize_ccp.toggled.connect(lambda checked: self.spin_ccp_alpha.setEnabled(not checked))

    def _get_imports(self) -> list[str]:
        imports = ["from sklearn.tree import DecisionTreeRegressor, plot_tree"]
        if self.chk_optimize_ccp.isChecked():
            imports.append("from sklearn.model_selection import KFold")
        return imports
        
    def _get_model_init_code(self) -> str:
        depth = self.spin_max_depth.value()
        depth_str = f"max_depth={depth}" if depth > 0 else "max_depth=None"
        
        if self.chk_optimize_ccp.isChecked():
            # Optimization logic is complex, so we'll generate it differently or as a multi-step block
            return f"# Model initialized later after CCP optimization"
        
        return f"model = DecisionTreeRegressor(criterion='{self.cmb_criterion.currentText()}', {depth_str}, min_samples_split={self.spin_min_samples.value()}, ccp_alpha={self.spin_ccp_alpha.value()}, random_state=42)"

    def _add_extra_plots_logic(self, code: list[str]) -> None:
        if self.chk_tree.isChecked():
            code.append("plots_to_draw.append('tree')")

    def _add_extra_plots_rendering(self, code: list[str]) -> None:
        if self.chk_tree.isChecked():
            code.append("        elif p_type == 'tree':")
            code.append("            # Re-generate tree plot with custom size")
            code.append("            plt.close(fig)")
            code.append("            fig, ax = plt.subplots(figsize=(20, 10))")
            code.append("            plot_tree(model, feature_names=X.columns, filled=True, rounded=True, ax=ax)")
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
            code.append("            continue")

    def generate_code(self) -> str:
        if not self.chk_optimize_ccp.isChecked():
            return super().generate_code()
            
        # Custom code generation for CCP optimization
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
        depth = self.spin_max_depth.value()
        depth_str = f"max_depth={depth}" if depth > 0 else "max_depth=None"
        criterion = self.cmb_criterion.currentText()
        min_samples = self.spin_min_samples.value()
        
        settings = SettingsManager()
        n_jobs = -1 if settings.compute_mode == ComputeMode.CPU_MULTI else 1
        
        code = [
            f"# {self.windowTitle()} (with CCP Optimization): {target} ~ {', '.join(features)}",
            "import polars as pl",
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "import io",
            "import base64",
            "from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV",
            "from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error",
            "from sklearn.tree import DecisionTreeRegressor, plot_tree",
            f"features = {features}",
            ""
        ]
        
        # Data loading (consistent with base)
        code.append("if isinstance(df, pl.DataFrame):")
        code.append(f"    combined = df.select([{', '.join([f'\"{f}\"' for f in features + [target]])}]).drop_nulls()")
        code.append(f"    X = combined.select([{', '.join([f'\"{f}\"' for f in features])}]).to_pandas()")
        code.append(f"    y = combined.select('{target}').to_pandas().iloc[:, 0]")
        code.append("else:")
        code.append(f"    combined = df[[{', '.join([f'\"{f}\"' for f in features + [target]])}]].dropna()")
        code.append(f"    X = combined[[{', '.join([f'\"{f}\"' for f in features])}]]")
        code.append(f"    y = combined['{target}']")
        code.append("")
        code.append("X = pd.get_dummies(X, drop_first=True, dtype=float)")
        code.append(f"X_train, X_test, y_train, y_test = train_test_split(X, y, test_size={test_size}, random_state=42)")
        code.append("")
        
        if scale_data:
            code.append("from sklearn.preprocessing import StandardScaler")
            code.append("scaler = StandardScaler()")
            code.append("X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=X.columns)")
            code.append("X_test = pd.DataFrame(scaler.transform(X_test), columns=X.columns)")
            code.append("")

        code.append("# 1. Compute Pruning Path")
        code.append(f"base_tree = DecisionTreeRegressor(criterion='{criterion}', {depth_str}, min_samples_split={min_samples}, random_state=42)")
        code.append("path = base_tree.cost_complexity_pruning_path(X_train, y_train)")
        code.append("ccp_alphas = path.ccp_alphas")
        code.append("")
        
        code.append("# 2. Optimize CCP Alpha (Parallel)")
        code.append(f"grid_search = GridSearchCV(base_tree, param_grid={{'ccp_alpha': ccp_alphas}}, cv=5, n_jobs={n_jobs})")
        code.append("grid_search.fit(X_train, y_train)")
        code.append("")
        code.append("model = grid_search.best_estimator_")
        code.append("best_alpha = grid_search.best_params_['ccp_alpha']")
        code.append("")
        
        code.append("# 3. Evaluate and Output")
        code.append("y_pred = model.predict(X_test)")
        code.append("html_output = []")
        code.append(f"html_output.append('<h3>{self.windowTitle()}</h3>')")
        code.append(f"html_output.append(f'<p><b>Best CCP Alpha:</b> {{best_alpha:.6f}}<br><b>Features:</b> {len(features)} selected</p>')")
        
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

        if self.chk_plots.isChecked() or self.chk_feat_imp.isChecked() or self.chk_tree.isChecked():
            style_code = generate_style_code(self.cmb_style.currentText())
            code.extend([line for line in style_code.split("\n") if line.strip()])
            
            code.append("plots_to_draw = []")
            if self.chk_plots.isChecked(): code.append("plots_to_draw.append('actual_vs_pred')")
            if self.chk_plots.isChecked(): code.append("plots_to_draw.append('residuals')")
            if self.chk_feat_imp.isChecked(): code.append("plots_to_draw.append('feat_imp')")
            if self.chk_tree.isChecked(): code.append("plots_to_draw.append('tree')")
            
            code.append("if plots_to_draw:")
            code.append("    for p_type in plots_to_draw:")
            code.append("        fig, ax = plt.subplots(figsize=(8, 8))")
            
            if self.chk_plots.isChecked():
                code.append("        if p_type == 'actual_vs_pred':")
                code.append("            ax.scatter(y_test, y_pred, alpha=0.5)")
                code.append("            ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)")
                code.append("            ax.set_title('Actual vs Predicted')")
                code.append("            ax.set_xlabel('Actual')")
                code.append("            ax.set_ylabel('Predicted')")
                
                code.append("        elif p_type == 'residuals':")
                code.append("            residuals = y_test - y_pred")
                code.append("            ax.scatter(y_pred, residuals, alpha=0.5)")
                code.append("            ax.axhline(y=0, color='r', linestyle='--', lw=2)")
                code.append("            ax.set_title('Residuals Plot')")
                code.append("            ax.set_xlabel('Predicted')")
                code.append("            ax.set_ylabel('Residuals')")

            if self.chk_feat_imp.isChecked() and self._supports_feature_importance:
                code.append("        elif p_type == 'feat_imp' and hasattr(model, 'feature_importances_'):")
                code.append("            importances = model.feature_importances_")
                code.append("            indices = np.argsort(importances)[::-1][:15]")
                code.append("            ax.bar(range(len(indices)), importances[indices], align='center')")
                code.append("            ax.set_xticks(range(len(indices)))")
                code.append("            ax.set_xticklabels([X.columns[i] for i in indices], rotation=45, ha='right')")
                code.append("            ax.set_title('Top Feature Importances')")
                
            self._add_extra_plots_rendering(code)

            code.append("        plt.tight_layout()")
            code.append("        buf = io.BytesIO()")
            code.append("        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')")
            code.append("        buf.seek(0)")
            code.append("        img_b64 = base64.b64encode(buf.read()).decode('utf-8')")
            code.append("        if \'register_figure\' in globals():")
            code.append("            register_figure(img_b64, fig)")
            code.append("        plt.close(fig)")
            code.append("        html_output.append(f'<div style=\"text-align:center; margin-top:20px;\"><img src=\"data:image/png;base64,{img_b64}\" width=\"800\" height=\"800\" style=\"border:1px solid #E2E8F0; border-radius:4px;\"/></div>')")


        code.append("if 'show_result' in globals():")
        code.append(f"    show_result('{self.windowTitle()}', '\\n'.join(html_output))")
        code.append("else:")
        code.append(f"    print('{self.windowTitle()}')")
        if self.chk_metrics.isChecked():
            code.append("    print(f'R2: {r2:.4f}, RMSE: {rmse:.4f}')")
        return "\n".join(code)


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
        self.cmb_criterion.addItems(["squared_error", "friedman_mse", "absolute_error", "poisson"])
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
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.ensemble", "RandomForestRegressor", "cuml.ensemble")
        
    def _get_model_init_code(self) -> str:
        depth = self.spin_max_depth.value()
        depth_str = f"max_depth={depth}" if depth > 0 else "max_depth=None"
        return (f"model = RandomForestRegressor(n_estimators={self.spin_estimators.value()}, "
                f"criterion='{self.cmb_criterion.currentText()}', {depth_str}, "
                f"bootstrap={self.chk_bootstrap.isChecked()}, n_jobs=-1, random_state=42)")

class LinearRegressionMLDialog(BaseTreeRegressionDialog):
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Linear Regression (ML)", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        self.chk_fit_intercept = QCheckBox("Fit Intercept")
        self.chk_fit_intercept.setChecked(True)
        layout.addRow(self.chk_fit_intercept)
        
    def _get_imports(self) -> list[str]:
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.linear_model", "LinearRegression", "cuml.linear_model")
        
    def _get_model_init_code(self) -> str:
        return f"model = LinearRegression(fit_intercept={self.chk_fit_intercept.isChecked()})"
        
    def _add_extra_plots_rendering(self, code: list[str]) -> None:
        if self.chk_feat_imp.isChecked():
            code.append("        elif p_type == 'feat_imp' and hasattr(model, 'coef_'):")
            code.append("            importances = np.abs(model.coef_)")
            code.append("            indices = np.argsort(importances)[::-1][:15]")
            code.append("            ax.bar(range(len(indices)), importances[indices], align='center')")
            code.append("            ax.set_xticks(range(len(indices)))")
            code.append("            ax.set_xticklabels([X.columns[i] for i in indices], rotation=45, ha='right')")
            code.append("            ax.set_title('Coefficient Magnitude (Absolute)')")

class RidgeDialog(BaseTreeRegressionDialog):
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Ridge Regression", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0.001, 1000.0)
        self.spin_alpha.setValue(1.0)
        layout.addRow("Alpha (Regularization):", self.spin_alpha)
        
    def _get_imports(self) -> list[str]:
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.linear_model", "Ridge", "cuml.linear_model")
        
    def _get_model_init_code(self) -> str:
        return f"model = Ridge(alpha={self.spin_alpha.value()})"
        
    def _add_extra_plots_rendering(self, code: list[str]) -> None:
        LinearRegressionMLDialog._add_extra_plots_rendering(self, code)

class LassoDialog(BaseTreeRegressionDialog):
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("Lasso Regression", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0.001, 1000.0)
        self.spin_alpha.setValue(1.0)
        layout.addRow("Alpha (Regularization):", self.spin_alpha)
        
    def _get_imports(self) -> list[str]:
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.linear_model", "Lasso", "cuml.linear_model")
        
    def _get_model_init_code(self) -> str:
        return f"model = Lasso(alpha={self.spin_alpha.value()})"

    def _add_extra_plots_rendering(self, code: list[str]) -> None:
        LinearRegressionMLDialog._add_extra_plots_rendering(self, code)

class ElasticNetDialog(BaseTreeRegressionDialog):
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__("ElasticNet Regression", df, parent, supports_feature_importance=True)
        
    def _build_hyperparameters(self, layout: QFormLayout) -> None:
        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0.001, 1000.0)
        self.spin_alpha.setValue(1.0)
        layout.addRow("Alpha (Regularization):", self.spin_alpha)
        
        self.spin_l1_ratio = QDoubleSpinBox()
        self.spin_l1_ratio.setRange(0.0, 1.0)
        self.spin_l1_ratio.setValue(0.5)
        self.spin_l1_ratio.setSingleStep(0.1)
        layout.addRow("L1 Ratio:", self.spin_l1_ratio)
        
    def _get_imports(self) -> list[str]:
        from quantia.utils.codegen import get_gpu_import
        return get_gpu_import("sklearn.linear_model", "ElasticNet", "cuml.linear_model")
        
    def _get_model_init_code(self) -> str:
        return f"model = ElasticNet(alpha={self.spin_alpha.value()}, l1_ratio={self.spin_l1_ratio.value()})"

    def _add_extra_plots_rendering(self, code: list[str]) -> None:
        LinearRegressionMLDialog._add_extra_plots_rendering(self, code)
