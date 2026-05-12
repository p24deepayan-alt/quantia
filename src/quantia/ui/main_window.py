"""Main Window — the Quantia application shell.

Layout inspired by:
- MS Excel: menu bar + toolbar + central data grid + status bar
- VBA Editor: left dock (variable list), bottom dock (console), tabbed central area
- Antigravity/VS Code: clean panel borders, dark theme support

All docks are rearrangeable. Central area uses QTabWidget for
Data View | Script Editor | Workflow | Plots tabs.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
import zipfile
import io

import pandas as pd
import polars as pl
from PySide6.QtCore import Qt, QSize, QTimer, QThreadPool
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QWidget,
    QLabel,
)

from quantia.theme.palette import Theme, get_stylesheet
from quantia.ui.icons import feather_icon
from quantia.utils.paths import get_exports_dir, get_workspaces_dir, get_quantia_root, get_scripts_dir
from quantia.utils.resources import resource_path
from quantia.utils.gpu import is_nvidia_gpu_available, get_gpu_info, get_cuda_version
from quantia.ui.menu_bar import QuantiaMenuBar
from quantia.ui.toolbar import QuantiaToolbar
from quantia.ui.status_bar import QuantiaStatusBar
from quantia.ui.panels.variable_list import VariableListPanel
from quantia.ui.panels.console import ConsolePanel
from quantia.ui.central.data_view import DataViewWidget
from quantia.ui.central.script_editor import ScriptEditorWidget
from quantia.ui.central.results_view import ResultsViewWidget
from quantia.ui.central.plot_view import PlotViewWidget
from quantia.ui.central.workflow import WorkflowTab
from quantia.utils.worker import ScriptWorker

# Dialogs
from quantia.ui.dialogs.descriptive import DescriptiveStatsDialog
from quantia.ui.dialogs.ttest import TTestDialog
from quantia.ui.dialogs.regression import LinearRegressionDialog
from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
from quantia.ui.dialogs.tree_regression import (
    RandomForestRegressorDialog, DecisionTreeRegressorDialog,
    LinearRegressionMLDialog, RidgeDialog, LassoDialog, ElasticNetDialog
)
from quantia.ui.dialogs.clean_data import CleanDataDialog
from quantia.ui.dialogs.transform import TransformDataDialog
from quantia.ui.dialogs.type_convert import TypeConvertDialog
from quantia.ui.dialogs.filter_data import FilterDataDialog
from quantia.ui.dialogs.merge_join import MergeJoinDialog
from quantia.ui.dialogs.text_extract import TextExtractDialog
from quantia.ui.dialogs.string_format import StringFormatDialog
from quantia.ui.dialogs.find_replace import FindReplaceDialog
from quantia.ui.dialogs.concat_cols import ConcatColsDialog
from quantia.ui.dialogs.if_else import IfElseDialog
from quantia.ui.dialogs.pivot_table import PivotTableDialog
from quantia.ui.dialogs.histogram import HistogramDialog
from quantia.ui.dialogs.scatter import ScatterPlotDialog
from quantia.ui.dialogs.boxplot import BoxPlotDialog
from quantia.ui.dialogs.barchart import BarChartDialog
from quantia.ui.dialogs.violinplot import ViolinPlotDialog
from quantia.ui.dialogs.linechart import LineChartDialog
from quantia.ui.dialogs.heatmap import HeatmapDialog
from quantia.ui.dialogs.correlation import CorrelationDialog
from quantia.ui.central.dashboard_tab import DashboardTabWidget
from quantia.ui.dialogs.anova_models import AnovaModelComparisonDialog
from quantia.ui.dialogs.chi_square import ChiSquareDialog
from quantia.ui.dialogs.qqplot import QQPlotDialog
from quantia.ui.dialogs.nonparametric import NonParametricDialog
from quantia.ui.dialogs.classification import (
    RandomForestDialog, GradientBoostingDialog, DecisionTreeDialog,
    SVMDialog, KNNDialog, LDADialog, QDADialog, NaiveBayesDialog,
    LogisticRegressionMLDialog
)
from quantia.ui.dialogs.model_compare import ModelComparisonDialog
from quantia.ui.dialogs.clustering import (
    KMeansDialog, HierarchicalDialog, DBSCANDialog, GMMDialog
)
from quantia.ui.dialogs.pca import PCADialog
from quantia.ui.dialogs.report import ReportDialog
from quantia.ui.dialogs.help import UserManualDialog, GuidedWizardDialog
from quantia.ui.dialogs.preferences import PreferencesDialog
from quantia.core.workspace import Workspace


_ICON_PATH = resource_path("reference/logo/Quantia_icon.ico")


class MainWindow(QMainWindow):
    """Quantia main application window."""

    def __init__(self) -> None:
        super().__init__()
        self._threadpool = QThreadPool.globalInstance()

        # ── Workspace ───────────────────────────────────────────────────
        self.workspace = Workspace(max_history=50)
        self._model_history = []

        # ── Window setup ─────────────────────────────────────────────────
        self._current_project_path: str | None = None
        self._update_window_title()
        self.setMinimumSize(1024, 700)
        self.resize(1400, 900)

        if _ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(_ICON_PATH)))

        # ── Menu bar ─────────────────────────────────────────────────────
        self._menu_bar = QuantiaMenuBar(self)
        self.setMenuBar(self._menu_bar)

        # ── Toolbar ──────────────────────────────────────────────────────
        self._toolbar = QuantiaToolbar(self)
        self._toolbar.toggle_theme.connect(self._toggle_theme)
        self.addToolBar(self._toolbar)

        self._status_bar = QuantiaStatusBar(self)
        self.setStatusBar(self._status_bar)
        
        # Initialize compute mode from settings
        from quantia.core.settings import SettingsManager, ComputeMode
        settings = SettingsManager()
        mode_text = "CPU - single core" if settings.compute_mode == ComputeMode.CPU_SINGLE else "CPU - Multi core"
        if settings.compute_mode == ComputeMode.GPU:
            mode_text = "GPU Acceleration"
        self._status_bar.set_compute_mode(mode_text)

        # ── Central tab widget ───────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.South)
        self._tabs.setDocumentMode(True)

        # Data View tab
        self._data_view = DataViewWidget()
        self._tabs.addTab(self._data_view, feather_icon("grid", "#000000", 14), "Data View")

        # Script Editor tab
        self._script_editor = ScriptEditorWidget()
        self._tabs.addTab(self._script_editor, feather_icon("code", "#000000", 14), "Script Editor")

        # Results tab
        self._results_view = ResultsViewWidget()
        self._tabs.addTab(self._results_view, feather_icon("list", "#000000", 14), "Results")

        # Workflow tab
        self._workflow_view = WorkflowTab()
        self._tabs.addTab(self._workflow_view, feather_icon("share-2", "#000000", 14), "Workflow")

        # Plots tab
        self._plot_view = PlotViewWidget()
        self._tabs.addTab(self._plot_view, feather_icon("pie-chart", "#000000", 14), "Plots")

        # Dashboard tab
        self._dashboard_tab = DashboardTabWidget()
        self._tabs.addTab(self._dashboard_tab, feather_icon("layout", "#000000", 14), "Dashboard Builder")

        self.setCentralWidget(self._tabs)
        

        # ── Left dock: Variable List ─────────────────────────────────────
        self._variable_panel = VariableListPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._variable_panel)

        # ── Auto-save Heartbeat ──────────────────────────────────────────
        self._init_autosave()

        # ── Bottom dock: Console ─────────────────────────────────────────
        self._console = ConsolePanel(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._console)

        # ── Connect signals ──────────────────────────────────────────────
        self._connect_signals()

        # ── Apply light theme ─────────────────────────────────────────
        qss = get_stylesheet(Theme.LIGHT)
        self.setStyleSheet(qss)

    # ── Signal connections ───────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # Menu bar
        self._menu_bar.open_project.connect(self._open_project)
        self._menu_bar.save_project.connect(self._save_project)
        self._menu_bar.save_as.connect(self._save_project_as)
        self._toolbar.open_project.connect(self._open_project)
        self._toolbar.save_project.connect(self._save_project)

        self._menu_bar.import_csv.connect(self._import_csv)
        self._menu_bar.import_excel.connect(self._import_excel)
        self._menu_bar.import_json.connect(self._import_json)
        self._menu_bar.import_parquet.connect(self._import_parquet)
        self._menu_bar.exit_app.connect(self.close)
        self._menu_bar.about.connect(self._show_about)
        self._menu_bar.user_manual.connect(self._show_user_manual)
        self._menu_bar.guided_wizard.connect(self._show_guided_wizard)

        # Undo / Redo
        self._menu_bar.undo.connect(self._undo)
        self._menu_bar.redo.connect(self._redo)
        self._menu_bar.preferences.connect(self._show_preferences)
        self._toolbar.undo_action.connect(self._undo)
        self._toolbar.redo_action.connect(self._redo)
        self._toolbar.preferences.connect(self._show_preferences)

        # Statistics
        self._menu_bar.descriptive_stats.connect(self._show_descriptive_stats)
        self._menu_bar.ttest.connect(self._show_ttest)
        self._menu_bar.anova.connect(self._show_anova)
        self._menu_bar.chi_square.connect(self._show_chi_square)
        self._menu_bar.nonparametric.connect(self._show_nonparametric)
        self._menu_bar.correlation.connect(self._show_correlation)
        
        # Regression
        self._menu_bar.regression_linear.connect(self._show_linear_regression)
        self._menu_bar.regression_linear_ml.connect(self._show_linear_regression_ml)
        self._menu_bar.regression_logistic.connect(self._show_logistic_regression)
        self._menu_bar.regression_ridge.connect(self._show_reg_ridge)
        self._menu_bar.regression_lasso.connect(self._show_reg_lasso)
        self._menu_bar.regression_elasticnet.connect(self._show_reg_elasticnet)
        self._menu_bar.regression_random_forest.connect(self._show_reg_random_forest)
        self._menu_bar.regression_decision_tree.connect(self._show_reg_decision_tree)
        
        # ML Classification
        self._menu_bar.model_compare.connect(self._show_model_compare)
        self._menu_bar.cls_logistic.connect(self._show_cls_logistic_ml)
        self._menu_bar.cls_random_forest.connect(self._show_cls_random_forest)
        self._menu_bar.cls_gradient_boosting.connect(self._show_cls_gradient_boosting)
        self._menu_bar.cls_decision_tree.connect(self._show_cls_decision_tree)
        self._menu_bar.cls_svm.connect(self._show_cls_svm)
        self._menu_bar.cls_knn.connect(self._show_cls_knn)
        self._menu_bar.cls_lda.connect(self._show_cls_lda)
        self._menu_bar.cls_qda.connect(self._show_cls_qda)
        self._menu_bar.cls_naive_bayes.connect(self._show_cls_naive_bayes)
        
        # ML Clustering
        self._menu_bar.clu_kmeans.connect(self._show_clu_kmeans)
        self._menu_bar.clu_hierarchical.connect(self._show_clu_hierarchical)
        self._menu_bar.clu_dbscan.connect(self._show_clu_dbscan)
        self._menu_bar.clu_gmm.connect(self._show_clu_gmm)
        self._menu_bar.pca.connect(self._show_pca)

        # Data menu signals
        self._menu_bar.clean_data.connect(self._show_clean_data)
        self._menu_bar.transform_data.connect(self._show_transform_data)
        self._menu_bar.type_convert.connect(self._show_type_convert)
        self._menu_bar.filter_data.connect(self._show_filter_data)
        self._menu_bar.merge_join.connect(self._show_merge_join)
        self._menu_bar.text_extract.connect(self._show_text_extract)
        self._menu_bar.string_format.connect(self._show_string_format)
        self._menu_bar.find_replace.connect(self._show_find_replace)
        self._menu_bar.concat_cols.connect(self._show_concat_cols)
        self._menu_bar.if_else.connect(self._show_if_else)
        self._menu_bar.pivot_table.connect(self._show_pivot_table)

        # Visualize menu signals
        self._menu_bar.histogram.connect(self._show_histogram)
        self._menu_bar.scatter.connect(self._show_scatter)
        self._menu_bar.boxplot.connect(self._show_boxplot)
        self._menu_bar.bar_chart.connect(self._show_barchart)
        self._menu_bar.violin.connect(self._show_violin)
        self._menu_bar.line_chart.connect(self._show_linechart)
        self._menu_bar.qqplot.connect(self._show_qqplot)
        self._menu_bar.heatmap.connect(self._show_heatmap)
        
        self._menu_bar.pairplot.connect(self._show_pairplot)
        self._menu_bar.stripplot.connect(self._show_stripplot)
        self._menu_bar.ridgeplot.connect(self._show_ridgeplot)
        self._menu_bar.density2d.connect(self._show_density2d)
        self._menu_bar.piechart.connect(self._show_piechart)
        self._menu_bar.treemap.connect(self._show_treemap)

        # Export / Report signals
        self._menu_bar.export_data.connect(self._export_data)
        self._menu_bar.export_script.connect(self._export_script)
        self._menu_bar.generate_report.connect(self._generate_report)
        self._menu_bar.toggle_theme.connect(self._toggle_theme)

        # Dashboard tab
        self._dashboard_tab.code_generated.connect(self._handle_generated_code)

        # Toolbar
        self._toolbar.import_data.connect(self._import_any)
        self._toolbar.run_script.connect(self._run_all_script)

        # Data view → variable list & status bar
        self._data_view.data_loaded.connect(self._on_data_loaded)

        # Variable list signals
        self._variable_panel.variable_selected.connect(self._on_variable_selected)

        # Script editor signals
        self._script_editor.run_code.connect(self._execute_code)
        self._script_editor.run_selection.connect(self._execute_code)

    # ── Project Management ───────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        """Switch between Light and Dark modes and refresh all components."""
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        from quantia.theme.palette import PALETTE
        
        app = QApplication.instance()
        if not isinstance(app, QuantiaApp):
            return
            
        new_theme = app.toggle_theme()
        palette = PALETTE[new_theme]
        text_color = palette["text_primary"]
        
        # 1. Update toolbar, menu bar and panels
        self._toolbar.refresh_icons(text_color)
        self._menu_bar.refresh_icons(text_color)
        self._variable_panel.refresh_theme(new_theme)
        self._plot_view.refresh_theme(new_theme)
        self._dashboard_tab.refresh_theme(new_theme)
        
        # 2. Update Central Tabs Icons
        self._tabs.setTabIcon(0, feather_icon("grid", text_color, 14))
        self._tabs.setTabIcon(1, feather_icon("code", text_color, 14))
        self._tabs.setTabIcon(2, feather_icon("list", text_color, 14))
        self._tabs.setTabIcon(3, feather_icon("share-2", text_color, 14))
        self._tabs.setTabIcon(4, feather_icon("pie-chart", text_color, 14))
        self._tabs.setTabIcon(5, feather_icon("layout", text_color, 14))

        # 3. Update Matplotlib global style
        import matplotlib.pyplot as plt
        if new_theme == Theme.DARK:
            plt.style.use('dark_background')
        else:
            plt.style.use('default')
            
        # 4. Update Views & Editors
        self._results_view.refresh_theme()
        self._data_view.refresh_theme()
        self._script_editor.refresh_theme(new_theme)
        if hasattr(self._workflow_view, "refresh_theme"):
            self._workflow_view.refresh_theme(new_theme)
        if hasattr(self._console, "refresh_theme"):
            self._console.refresh_theme(new_theme)
            
        # 5. Explicitly update window stylesheet to force refresh
        self.setStyleSheet(get_stylesheet(new_theme))
        self._status_bar.showMessage(f"Switched to {new_theme.value} mode", 3000)

    def _update_window_title(self) -> None:
        if self._current_project_path:
            name = Path(self._current_project_path).name
            self.setWindowTitle(f"Quantia — {name}")
        else:
            self.setWindowTitle("Quantia — Untitled")

    def _save_project(self) -> None:
        if not self._current_project_path:
            self._save_project_as()
        else:
            self._write_project_file(self._current_project_path)

    def _init_autosave(self) -> None:
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._auto_save_heartbeat)
        self._autosave_timer.start(300000) # 5 mins

    def _auto_save_heartbeat(self) -> None:
        if len(self._data_view.model.dataframe) == 0:
            return
        temp_path = get_workspaces_dir() / ".temp.quantia"
        try:
            self._write_project_file(str(temp_path), is_autosave=True)
            self._status_bar.showMessage("Auto-saved workspace", 2000)
        except Exception:
            pass

    def _save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", str(get_workspaces_dir()), "Quantia Project (*.quantia)"
        )
        if path:
            if not path.endswith(".quantia"):
                path += ".quantia"
            self._write_project_file(path)

    def _write_project_file(self, path: str, is_autosave: bool = False) -> None:
        try:
            self.workspace.set_dataframe(self._data_view.get_dataframe())
            self.workspace.script = self._script_editor.get_text()
            if not self._current_project_path and not is_autosave:
                self.workspace.metadata["name"] = Path(path).stem
            self.workspace.save(path)
            if not is_autosave:
                self._current_project_path = path
                self._update_window_title()
                self._console.write_success(f"Project saved to {path}")
        except Exception as e:
            self._console.write_error(f"Failed to save project: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save project:\n{e}")

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Quantia Project (*.quantia)"
        )
        if not path:
            return
        try:
            self.workspace = Workspace.load(path)
            self._data_view.load_dataframe(self.workspace.dataframe)
            self._script_editor.set_text(self.workspace.script)
            self._current_project_path = path
            self._update_window_title()
            self._results_view.clear_all()
            self._plot_view.clear_all()
            self._model_history.clear()
            self._console.write_success(f"Project loaded from {path}")
            self._run_all_script()
        except Exception as e:
            self._console.write_error(f"Failed to open project: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to open project:\n{e}")

    # ── Data import ──────────────────────────────────────────────────────

    def _robust_read_csv(self, path: str) -> tuple[pl.DataFrame, str | None]:
        null_vals = ["NA", "N/A", "null", "NULL", "NaN", "nan", "None", "", " ", "-"]
        try:
            return pl.read_csv(path, infer_schema_length=10000, truncate_ragged_lines=True, ignore_errors=False, null_values=null_vals), None
        except Exception:
            pass
        try:
            with open(path, 'rb') as f: content = f.read().decode('cp1252').encode('utf-8')
            return pl.read_csv(content, infer_schema_length=10000, truncate_ragged_lines=True, ignore_errors=False, null_values=null_vals), 'cp1252'
        except Exception:
            pass
        try:
            import charset_normalizer
            with open(path, 'rb') as f: raw_data = f.read(1024 * 1024)
            res = charset_normalizer.from_bytes(raw_data).best()
            if not res or not res.encoding: raise ValueError("No encoding detected")
            with open(path, 'rb') as f: content = f.read().decode(res.encoding).encode('utf-8')
            return pl.read_csv(content, infer_schema_length=10000, truncate_ragged_lines=True, ignore_errors=False, null_values=null_vals), res.encoding
        except Exception:
            with open(path, 'rb') as f: content = f.read().decode('latin1').encode('utf-8')
            return pl.read_csv(content, infer_schema_length=10000, truncate_ragged_lines=True, ignore_errors=True, null_values=null_vals), "latin1"

    def _import_any(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Data", "", "All Supported (*.csv *.xlsx *.xls *.json *.parquet);;All Files (*)")
        if not path: return
        ext = Path(path).suffix.lower()
        try:
            from PySide6.QtWidgets import QApplication
            self._snapshot_for_undo()
            self._status_bar.show_progress(0, 0, "Loading data...")
            QApplication.processEvents()
            used_encoding = None
            if ext == ".csv": df, used_encoding = self._robust_read_csv(path)
            elif ext in (".xlsx", ".xls"): df = pl.from_pandas(pd.read_excel(path))
            elif ext == ".json": df = pl.read_json(path)
            elif ext == ".parquet": df = pl.read_parquet(path)
            else: return
            self._data_view.load_dataframe(df)
            self._console.write_success(f"Loaded {len(df):,} rows from {Path(path).name}")
            self._script_editor.append_code(f"df = pl.read_csv(r'{path}')")
        except Exception as e: self._console.write_error(f"Import failed: {e}")
        finally: self._status_bar.hide_progress()

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path: return
        try:
            self._status_bar.show_progress(0, 0, "Loading CSV...")
            df, enc = self._robust_read_csv(path)
            self._data_view.load_dataframe(df)
            self._script_editor.append_code(f"df = pl.read_csv(r'{path}')")
        except Exception as e: self._console.write_error(str(e))
        finally: self._status_bar.hide_progress()

    def _import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Excel", "", "Excel Files (*.xlsx *.xls);;All Files (*)")
        if not path: return
        try:
            df = pl.from_pandas(pd.read_excel(path))
            self._data_view.load_dataframe(df)
            self._script_editor.append_code(f"df = pl.from_pandas(pd.read_excel(r'{path}'))")
        except Exception as e: self._console.write_error(str(e))

    def _import_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json);;All Files (*)")
        if not path: return
        try:
            df = pl.read_json(path)
            self._data_view.load_dataframe(df)
            self._script_editor.append_code(f"df = pl.read_json(r'{path}')")
        except Exception as e: self._console.write_error(str(e))

    def _import_parquet(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Parquet", "", "Parquet Files (*.parquet);;All Files (*)")
        if not path: return
        try:
            df = pl.read_parquet(path)
            self._data_view.load_dataframe(df)
            self._script_editor.append_code(f"df = pl.read_parquet(r'{path}')")
        except Exception as e: self._console.write_error(str(e))

    # ── Data Callbacks ───────────────────────────────────────────────────

    def _on_data_loaded(self, df: pd.DataFrame | pl.DataFrame) -> None:
        self._status_bar.set_dataset_info(len(df), len(df.columns))
        col_info = self._data_view.model.column_info()
        self._variable_panel.set_variables(col_info)
        self._dashboard_tab.update_columns(df.columns)

    def _on_variable_selected(self, var_name: str) -> None:
        df = self._data_view.get_dataframe()
        if var_name in df.columns:
            self._console.write_info(f"── {var_name} ──")
            series = df.get_column(var_name) if isinstance(df, pl.DataFrame) else df[var_name]
            self._console.write(str(series.describe()))

    def _snapshot_for_undo(self) -> None:
        df = self._data_view.get_dataframe()
        if len(df) > 0: self.workspace.push_undo_state(df)

    def _undo(self) -> None:
        self.workspace.set_dataframe(self._data_view.get_dataframe())
        prev = self.workspace.undo()
        if prev is not None: self._data_view.load_dataframe(prev)

    def _redo(self) -> None:
        self.workspace.set_dataframe(self._data_view.get_dataframe())
        nxt = self.workspace.redo()
        if nxt is not None: self._data_view.load_dataframe(nxt)

    # ── Script Execution ─────────────────────────────────────────────────

    def _run_all_script(self) -> None:
        code = self._script_editor.editor.get_all_text()
        if code.strip(): self._execute_code(code)

    def _execute_code(self, code: str) -> None:
        import numpy as np; import scipy; import matplotlib
        matplotlib.use('Agg')
        namespace = {"pd": pd, "pl": pl, "np": np, "scipy": scipy, "df": self._data_view.get_dataframe()}
        self._snapshot_for_undo()
        self._status_bar.show_progress(0, 0, "Executing...")
        worker = ScriptWorker(code, namespace)
        worker.signals.result.connect(lambda d: self._console.write(d["stdout"]))
        worker.signals.error.connect(lambda e: self._console.write_error(str(e[1])))
        worker.signals.finished.connect(lambda: self._status_bar.hide_progress())
        worker.signals.display_result.connect(lambda t, c: (self._results_view.add_result(t, c), self._tabs.setCurrentIndex(2)))
        worker.signals.display_plot.connect(lambda t, f: (self._plot_view.add_plot(t, f), self._tabs.setCurrentIndex(4)))
        worker.signals.display_plotly.connect(lambda t, h: (self._plot_view.add_plotly_plot(t, h), self._tabs.setCurrentIndex(4)))
        worker.signals.register_figure.connect(self._results_view.register_figure)
        self._threadpool.start(worker)

    def _handle_generated_code(self, code: str) -> None:
        self._script_editor.append_code("\n" + code)
        self._execute_code(code)

    # ── Dialog Helpers ───────────────────────────────────────────────────

    def _show_data_dialog(self, dialog_class) -> None:
        df = self._data_view.get_dataframe()
        if len(df) == 0:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return
        dialog = dialog_class(df, self)
        if hasattr(dialog, "load_history"):
            dialog.load_history(self._script_editor.editor.get_all_text(), getattr(self, "_model_history", []))
        dialog.code_generated.connect(self._handle_generated_code)
        dialog.exec()

    # ── Handlers ─────────────────────────────────────────────────────────

    def _show_descriptive_stats(self) -> None: self._show_data_dialog(DescriptiveStatsDialog)
    def _show_ttest(self) -> None: self._show_data_dialog(TTestDialog)
    def _show_anova(self) -> None: self._show_data_dialog(AnovaModelComparisonDialog)
    def _show_chi_square(self) -> None: self._show_data_dialog(ChiSquareDialog)
    def _show_nonparametric(self) -> None: self._show_data_dialog(NonParametricDialog)
    def _show_correlation(self) -> None: self._show_data_dialog(CorrelationDialog)
    
    def _show_linear_regression(self) -> None: self._show_data_dialog(LinearRegressionDialog)
    def _show_linear_regression_ml(self) -> None: self._show_data_dialog(LinearRegressionMLDialog)
    def _show_logistic_regression(self) -> None: self._show_data_dialog(LogisticRegressionDialog)
    def _show_reg_ridge(self) -> None: self._show_data_dialog(RidgeDialog)
    def _show_reg_lasso(self) -> None: self._show_data_dialog(LassoDialog)
    def _show_reg_elasticnet(self) -> None: self._show_data_dialog(ElasticNetDialog)
    def _show_reg_random_forest(self) -> None: self._show_data_dialog(RandomForestRegressorDialog)
    def _show_reg_decision_tree(self) -> None: self._show_data_dialog(DecisionTreeRegressorDialog)

    def _show_clean_data(self) -> None: self._show_data_dialog(CleanDataDialog)
    def _show_transform_data(self) -> None: self._show_data_dialog(TransformDataDialog)
    def _show_type_convert(self) -> None: self._show_data_dialog(TypeConvertDialog)
    def _show_filter_data(self) -> None: self._show_data_dialog(FilterDataDialog)
    def _show_merge_join(self) -> None: self._show_data_dialog(MergeJoinDialog)
    def _show_text_extract(self) -> None: self._show_data_dialog(TextExtractDialog)
    def _show_string_format(self) -> None: self._show_data_dialog(StringFormatDialog)
    def _show_find_replace(self) -> None: self._show_data_dialog(FindReplaceDialog)
    def _show_concat_cols(self) -> None: self._show_data_dialog(ConcatColsDialog)
    def _show_if_else(self) -> None: self._show_data_dialog(IfElseDialog)
    def _show_pivot_table(self) -> None: self._show_data_dialog(PivotTableDialog)

    def _show_histogram(self) -> None: self._show_data_dialog(HistogramDialog)
    def _show_scatter(self) -> None: self._show_data_dialog(ScatterPlotDialog)
    def _show_boxplot(self) -> None: self._show_data_dialog(BoxPlotDialog)
    def _show_barchart(self) -> None: self._show_data_dialog(BarChartDialog)
    def _show_violin(self) -> None: self._show_data_dialog(ViolinPlotDialog)
    def _show_linechart(self) -> None: self._show_data_dialog(LineChartDialog)
    def _show_heatmap(self) -> None: self._show_data_dialog(HeatmapDialog)
    def _show_qqplot(self) -> None: self._show_data_dialog(QQPlotDialog)

    def _show_pairplot(self) -> None: 
        from quantia.ui.dialogs.pairplot import PairPlotDialog
        self._show_data_dialog(PairPlotDialog)
    def _show_stripplot(self) -> None: 
        from quantia.ui.dialogs.stripplot import StripPlotDialog
        self._show_data_dialog(StripPlotDialog)
    def _show_ridgeplot(self) -> None: 
        from quantia.ui.dialogs.ridgeplot import RidgePlotDialog
        self._show_data_dialog(RidgePlotDialog)
    def _show_density2d(self) -> None: 
        from quantia.ui.dialogs.density2d import Density2DPlotDialog
        self._show_data_dialog(Density2DPlotDialog)
    def _show_piechart(self) -> None: 
        from quantia.ui.dialogs.piechart import PieChartDialog
        self._show_data_dialog(PieChartDialog)
    def _show_treemap(self) -> None: 
        from quantia.ui.dialogs.treemap import TreemapDialog
        self._show_data_dialog(TreemapDialog)

    def _show_model_compare(self) -> None: self._show_data_dialog(ModelComparisonDialog)
    def _show_cls_logistic_ml(self) -> None: self._show_data_dialog(LogisticRegressionMLDialog)
    def _show_cls_random_forest(self) -> None: self._show_data_dialog(RandomForestDialog)
    def _show_cls_gradient_boosting(self) -> None: self._show_data_dialog(GradientBoostingDialog)
    def _show_cls_decision_tree(self) -> None: self._show_data_dialog(DecisionTreeDialog)
    def _show_cls_svm(self) -> None: self._show_data_dialog(SVMDialog)
    def _show_cls_knn(self) -> None: self._show_data_dialog(KNNDialog)
    def _show_cls_lda(self) -> None: self._show_data_dialog(LDADialog)
    def _show_cls_qda(self) -> None: self._show_data_dialog(QDADialog)
    def _show_cls_naive_bayes(self) -> None: self._show_data_dialog(NaiveBayesDialog)

    def _show_clu_kmeans(self) -> None: self._show_data_dialog(KMeansDialog)
    def _show_clu_hierarchical(self) -> None: self._show_data_dialog(HierarchicalDialog)
    def _show_clu_dbscan(self) -> None: self._show_data_dialog(DBSCANDialog)
    def _show_clu_gmm(self) -> None: self._show_data_dialog(GMMDialog)
    def _show_pca(self) -> None: self._show_data_dialog(PCADialog)

    # ── Export & Report ──────────────────────────────────────────────────

    def _export_data(self) -> None:
        df = self._data_view.get_dataframe()
        if len(df) == 0: return
        path, _ = QFileDialog.getSaveFileName(self, "Export Data", str(get_exports_dir()), "CSV (*.csv);;Excel (*.xlsx);;JSON (*.json);;Parquet (*.parquet)")
        if not path: return
        ext = Path(path).suffix.lower()
        try:
            if isinstance(df, pl.DataFrame):
                if ext == ".csv": df.write_csv(path)
                elif ext == ".xlsx": df.to_pandas().to_excel(path, index=False)
                elif ext == ".json": df.write_json(path)
                elif ext == ".parquet": df.write_parquet(path)
            else:
                if ext == ".csv": df.to_csv(path, index=False)
                elif ext == ".xlsx": df.to_excel(path, index=False)
                elif ext == ".json": df.to_json(path, orient="records", indent=2)
                elif ext == ".parquet": df.to_parquet(path, index=False)
            self._console.write_success(f"Exported to {Path(path).name}")
        except Exception as e: QMessageBox.critical(self, "Export Failed", str(e))

    def _export_script(self) -> None:
        script = self._script_editor.editor.get_all_text()
        if not script.strip(): return
        path, _ = QFileDialog.getSaveFileName(self, "Export Script", str(get_scripts_dir()), "Python Files (*.py)")
        if path: Path(path).write_text(script, encoding="utf-8")

    def _generate_report(self) -> None:
        from quantia.ui.dialogs.report import ReportDialog
        dialog = ReportDialog(self._data_view.get_dataframe(), self._script_editor.editor.get_all_text(), self._results_view.get_all_html(), self._plot_view.get_all_html(), self)
        dialog.exec()

    def _show_preferences(self) -> None:
        if PreferencesDialog(self).exec():
            from quantia.core.settings import SettingsManager, ComputeMode
            settings = SettingsManager()
            mode = "CPU - single core" if settings.compute_mode == ComputeMode.CPU_SINGLE else ("CPU - Multi core" if settings.compute_mode == ComputeMode.CPU_MULTI else "GPU Acceleration")
            self._status_bar.set_compute_mode(mode)

    def _show_about(self) -> None:
        QMessageBox.about(self, "About Quantia", f"<h2>Quantia</h2><p>Version 0.9.0-beta</p><p>Built with PySide6, pandas, numpy, scipy.</p><p style='color:#64748B; font-size:9pt;'>GPU: {get_gpu_info()} (CUDA {get_cuda_version()})</p>")

    def _show_user_manual(self) -> None: UserManualDialog(self).exec()
    def _show_guided_wizard(self) -> None: GuidedWizardDialog(self).exec()
