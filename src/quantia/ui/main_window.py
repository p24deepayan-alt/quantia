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
from PySide6.QtCore import Qt, QSize, QTimer
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
from quantia.ui.dialogs.descriptive import DescriptiveStatsDialog
from quantia.ui.dialogs.ttest import TTestDialog
from quantia.ui.dialogs.regression import LinearRegressionDialog
from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
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
from quantia.ui.dialogs.anova_models import AnovaModelComparisonDialog
from quantia.ui.dialogs.chi_square import ChiSquareDialog
from quantia.ui.dialogs.qqplot import QQPlotDialog
from quantia.ui.dialogs.nonparametric import NonParametricDialog
from quantia.ui.dialogs.classification import (
    RandomForestDialog, GradientBoostingDialog, DecisionTreeDialog,
    SVMDialog, KNNDialog, LDADialog, QDADialog, NaiveBayesDialog
)
from quantia.ui.dialogs.model_compare import ModelComparisonDialog
from quantia.ui.dialogs.clustering import (
    KMeansDialog, HierarchicalDialog, DBSCANDialog, GMMDialog
)
from quantia.ui.dialogs.pca import PCADialog
from quantia.ui.dialogs.report import ReportDialog
from quantia.ui.dialogs.help import UserManualDialog, GuidedWizardDialog


_ICON_PATH = resource_path("reference/logo/Quantia_icon.ico")


class MainWindow(QMainWindow):
    """Quantia main application window."""

    def __init__(self) -> None:
        super().__init__()


        # ── Undo / Redo stacks (max 4 snapshots) ────────────────────────
        self._undo_stack: deque[pd.DataFrame] = deque(maxlen=1)
        self._redo_stack: deque[pd.DataFrame] = deque(maxlen=1)
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
        
        # GPU Detection (Phase 1)
        if is_nvidia_gpu_available():
            self._status_bar.set_gpu_status(get_gpu_info())
        else:
            self._status_bar.set_gpu_status("None")

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

        self._plot_view = PlotViewWidget()
        self._tabs.addTab(self._plot_view, feather_icon("pie-chart", "#000000", 14), "Plots")

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
        self._toolbar.undo_action.connect(self._undo)
        self._toolbar.redo_action.connect(self._redo)

        self._menu_bar.descriptive_stats.connect(self._show_descriptive_stats)
        self._menu_bar.ttest.connect(self._show_ttest)
        self._menu_bar.anova.connect(self._show_anova)
        self._menu_bar.chi_square.connect(self._show_chi_square)
        self._menu_bar.nonparametric.connect(self._show_nonparametric)
        self._menu_bar.correlation.connect(self._show_correlation)
        self._menu_bar.regression_linear.connect(self._show_linear_regression)
        self._menu_bar.regression_logistic.connect(self._show_logistic_regression)
        
        # ML Classification
        self._menu_bar.model_compare.connect(self._show_model_compare)
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

        # Export / Report signals
        self._menu_bar.export_data.connect(self._export_data)
        self._menu_bar.export_script.connect(self._export_script)
        self._menu_bar.generate_report.connect(self._generate_report)
        self._menu_bar.toggle_theme.connect(self._toggle_theme)

        # Statistics menu signals
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
        
        # 2. Update Central Tabs Icons
        self._tabs.setTabIcon(0, feather_icon("grid", text_color, 14))
        self._tabs.setTabIcon(1, feather_icon("code", text_color, 14))
        self._tabs.setTabIcon(2, feather_icon("list", text_color, 14))
        self._tabs.setTabIcon(3, feather_icon("share-2", text_color, 14))
        self._tabs.setTabIcon(4, feather_icon("pie-chart", text_color, 14))

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
        
        # 6. Success message
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
        """Initialize the background auto-save timer."""
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._auto_save_heartbeat)
        # 5 minutes = 300,000 ms. Set to 1 minute for testing/quick protection?
        # Let's stick to 5 mins as per plan.
        self._autosave_timer.start(300000)

    def _auto_save_heartbeat(self) -> None:
        """Silently save the current state to a temporary file."""
        if self._data_view.model.dataframe.empty:
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
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # Save Dataframe
                if not self._data_view.model.dataframe.empty:
                    df_bytes = io.BytesIO()
                    self._data_view.model.dataframe.to_parquet(df_bytes)
                    zf.writestr("data.parquet", df_bytes.getvalue())
                
                # Save Script
                script_text = self._script_editor.get_text()
                zf.writestr("script.py", script_text)

                # Save Undo stack
                for i, df in enumerate(self._undo_stack):
                    df_bytes = io.BytesIO()
                    df.to_parquet(df_bytes)
                    zf.writestr(f"undo_{i}.parquet", df_bytes.getvalue())

                # Save Redo stack
                for i, df in enumerate(self._redo_stack):
                    df_bytes = io.BytesIO()
                    df.to_parquet(df_bytes)
                    zf.writestr(f"redo_{i}.parquet", df_bytes.getvalue())

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
            with zipfile.ZipFile(path, "r") as zf:
                # Load Dataframe
                if "data.parquet" in zf.namelist():
                    df_bytes = io.BytesIO(zf.read("data.parquet"))
                    df = pd.read_parquet(df_bytes)
                    self._data_view.load_dataframe(df)
                    self._variable_panel.populate(df.columns.tolist())
                else:
                    self._data_view.load_dataframe(pd.DataFrame())
                    self._variable_panel.populate([])

                # Load Script
                if "script.py" in zf.namelist():
                    script_text = zf.read("script.py").decode("utf-8")
                    self._script_editor.set_text(script_text)

                # Load Undo stack
                self._undo_stack.clear()
                undo_files = [n for n in zf.namelist() if n.startswith("undo_") and n.endswith(".parquet")]
                undo_files.sort()  # Should preserve order since names are like undo_0.parquet
                for n in undo_files:
                    df_bytes = io.BytesIO(zf.read(n))
                    self._undo_stack.append(pd.read_parquet(df_bytes))

                # Load Redo stack
                self._redo_stack.clear()
                redo_files = [n for n in zf.namelist() if n.startswith("redo_") and n.endswith(".parquet")]
                redo_files.sort()
                for n in redo_files:
                    df_bytes = io.BytesIO(zf.read(n))
                    self._redo_stack.append(pd.read_parquet(df_bytes))

            self._current_project_path = path
            self._update_window_title()
            
            # Clear outputs and auto-run
            self._results_view.clear()
            self._plot_view.clear()
            self._model_history.clear()
            self._console.write_success(f"Project loaded from {path}")
            
            # Automatically run the script to repopulate results and plots
            self._run_all_script()

        except Exception as e:
            self._console.write_error(f"Failed to open project: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to open project:\n{e}")

    # ── Data import ──────────────────────────────────────────────────────

    def _robust_read_csv(self, path: str) -> tuple[pd.DataFrame, str | None]:
        """Attempt to read a CSV with smart default fallbacks before AI detection."""
        # 1. Try standard utf-8
        try:
            df = pd.read_csv(path, encoding='utf-8', low_memory=False)
            return df, None
        except UnicodeDecodeError:
            pass

        # 2. Try cp1252 (Windows-1252) - fixes 99% of western datasets with ™, ½, etc.
        try:
            df = pd.read_csv(path, encoding='cp1252', low_memory=False)
            self._console.write_info("Loaded successfully using 'cp1252' smart fallback.")
            return df, 'cp1252'
        except UnicodeDecodeError:
            pass
            
        # 3. Fallback to AI Guesser for Asian scripts, UTF-16, etc.
        self._console.write_info("Smart fallbacks failed, running automatic encoding detection...")
        try:
            import charset_normalizer
            
            # Read a sample of the file to guess encoding
            with open(path, 'rb') as f:
                # Read first 1MB to guess
                raw_data = f.read(1024 * 1024)
            
            result = charset_normalizer.from_bytes(raw_data).best()
            if not result or not result.encoding:
                raise ValueError("Could not detect file encoding automatically.")
            
            detected_encoding = result.encoding
            self._console.write_info(f"Detected encoding: '{detected_encoding}' (Language: {result.language}).")
            
            df = pd.read_csv(path, encoding=detected_encoding, low_memory=False)
            return df, detected_encoding
            
        except Exception as e:
            # 4. Absolute last resort: latin1 mathematically cannot fail decoding
            self._console.write_warning(f"Detection failed ({e}). Forcing 'latin1' absolute fallback.")
            df = pd.read_csv(path, encoding="latin1", low_memory=False)
            return df, "latin1"

    def _import_any(self) -> None:
        """Open file dialog for any supported format."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "All Supported (*.csv *.xlsx *.xls *.json *.parquet);;"
            "CSV Files (*.csv);;"
            "Excel Files (*.xlsx *.xls);;"
            "JSON Files (*.json);;"
            "Parquet Files (*.parquet);;"
            "All Files (*)",
        )
        if not path:
            return

        self._console.write_command(f"import_data('{path}')")
        ext = Path(path).suffix.lower()

        try:
            from PySide6.QtWidgets import QApplication
            self._snapshot_for_undo()
            self._status_bar.show_progress(0, 0, "Loading data...")
            QApplication.processEvents()

            used_encoding = None
            if ext == ".csv":
                df, used_encoding = self._robust_read_csv(path)
            elif ext in (".xlsx", ".xls"):
                df = pd.read_excel(path)
            elif ext == ".json":
                df = pd.read_json(path)
            elif ext == ".parquet":
                df = pd.read_parquet(path)
            else:
                self._console.write_error(f"Unsupported format: {ext}")
                self._status_bar.hide_progress()
                return

            self._data_view.load_dataframe(df)
            self._console.write_success(f"Loaded {len(df):,} rows × {len(df.columns)} columns from {Path(path).name}")

            # Generate code in script editor
            csv_code = f"df = pd.read_csv(r'{path}', low_memory=False)"
            if used_encoding:
                csv_code = f"df = pd.read_csv(r'{path}', encoding='{used_encoding}', low_memory=False)"
                
            code_map = {
                ".csv": csv_code,
                ".xlsx": f"df = pd.read_excel(r'{path}')",
                ".xls": f"df = pd.read_excel(r'{path}')",
                ".json": f"df = pd.read_json(r'{path}')",
                ".parquet": f"df = pd.read_parquet(r'{path}')",
            }
            self._script_editor.append_code(code_map.get(ext, f"# import: {path}"))
        except Exception as e:
            self._console.write_error(f"Import failed: {e}")
        finally:
            self._status_bar.hide_progress()

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv);;All Files (*)")
        if path:
            self._console.write_command(f"pd.read_csv('{path}')")
            try:
                from PySide6.QtWidgets import QApplication
                self._status_bar.show_progress(0, 0, "Loading CSV...")
                QApplication.processEvents()

                df, used_encoding = self._robust_read_csv(path)
                self._data_view.load_dataframe(df)
                self._console.write_success(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
                
                # Append to script manually since _import_any handles its own
                if used_encoding:
                    self._script_editor.append_code(f"df = pd.read_csv(r'{path}', encoding='{used_encoding}', low_memory=False)")
                else:
                    self._script_editor.append_code(f"df = pd.read_csv(r'{path}', low_memory=False)")
                    
            except Exception as e:
                self._console.write_error(str(e))
            finally:
                self._status_bar.hide_progress()

    def _import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Excel", "", "Excel Files (*.xlsx *.xls);;All Files (*)")
        if path:
            self._console.write_command(f"pd.read_excel('{path}')")
            try:
                from PySide6.QtWidgets import QApplication
                self._status_bar.show_progress(0, 0, "Loading Excel...")
                QApplication.processEvents()

                df = pd.read_excel(path)
                self._data_view.load_dataframe(df)
                self._console.write_success(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
            except Exception as e:
                self._console.write_error(str(e))
            finally:
                self._status_bar.hide_progress()

    def _import_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json);;All Files (*)")
        if path:
            self._console.write_command(f"pd.read_json('{path}')")
            try:
                from PySide6.QtWidgets import QApplication
                self._status_bar.show_progress(0, 0, "Loading JSON...")
                QApplication.processEvents()

                df = pd.read_json(path)
                self._data_view.load_dataframe(df)
                self._console.write_success(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
            except Exception as e:
                self._console.write_error(str(e))
            finally:
                self._status_bar.hide_progress()

    def _import_parquet(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Parquet", "", "Parquet Files (*.parquet);;All Files (*)")
        if path:
            self._console.write_command(f"pd.read_parquet('{path}')")
            try:
                from PySide6.QtWidgets import QApplication
                self._status_bar.show_progress(0, 0, "Loading Parquet...")
                QApplication.processEvents()

                df = pd.read_parquet(path)
                self._data_view.load_dataframe(df)
                self._console.write_success(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
            except Exception as e:
                self._console.write_error(str(e))
            finally:
                self._status_bar.hide_progress()

    # ── Data loaded callback ─────────────────────────────────────────────

    def _snapshot_for_undo(self) -> None:
        """Save current DataFrame to undo stack before a mutation."""
        df = self._data_view.get_dataframe()
        if not df.empty:
            self._undo_stack.append(df.copy())
            self._redo_stack.clear()

    def _undo(self) -> None:
        """Restore the previous DataFrame state."""
        if not self._undo_stack:
            self._console.write_warning("Nothing to undo.")
            return
        # Push current state to redo
        current = self._data_view.get_dataframe()
        if not current.empty:
            self._redo_stack.append(current.copy())
        prev = self._undo_stack.pop()
        self._data_view.load_dataframe(prev)
        self._console.write_info("Undo")

    def _redo(self) -> None:
        """Re-apply the previously undone DataFrame state."""
        if not self._redo_stack:
            self._console.write_warning("Nothing to redo.")
            return
        # Push current state to undo
        current = self._data_view.get_dataframe()
        if not current.empty:
            self._undo_stack.append(current.copy())
        nxt = self._redo_stack.pop()
        self._data_view.load_dataframe(nxt)
        self._console.write_info("Redo")

    def _on_data_loaded(self, df: pd.DataFrame) -> None:
        """Update variable list and status bar when data is loaded."""
        self._status_bar.set_dataset_info(len(df), len(df.columns))
        col_info = self._data_view.model.column_info()
        self._variable_panel.set_variables(col_info)

    def _on_variable_selected(self, var_name: str) -> None:
        """Log variable selection to console."""
        df = self._data_view.get_dataframe()
        if var_name in df.columns:
            series = df[var_name]
            self._console.write_info(f"── {var_name} ──")
            self._console.write(str(series.describe()))



    # ── Script execution ─────────────────────────────────────────────────

    def _run_all_script(self) -> None:
        """Run the entire script editor contents."""
        code = self._script_editor.editor.get_all_text()
        if code.strip():
            self._execute_code(code)

    def _execute_code(self, code: str) -> None:
        """Execute Python code and show output in console."""
        import io
        import contextlib

        self._console.write_command(code.strip().split('\n')[0][:80])

        def _show_result(title: str, content) -> None:
            self._results_view.add_result(title, content)
            self._tabs.setCurrentIndex(2) # Auto switch to Results tab

        def _show_plot(title: str, fig) -> None:
            self._plot_view.add_plot(title, fig)
            self._tabs.setCurrentIndex(4) # Auto switch to Plots tab

        # Build a namespace with the current dataframe available
        import numpy as np
        import scipy.stats
        
        namespace = {
            "pd": pd,
            "np": np,
            "scipy": scipy,
            "df": self._data_view.get_dataframe(),
            "show_result": _show_result,
            "show_plot": _show_plot,
        }

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            from PySide6.QtWidgets import QApplication
            self._snapshot_for_undo()
            self._status_bar.show_progress(0, 0, "Executing script...")
            QApplication.processEvents()

            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                exec(code, namespace)

            output = stdout_capture.getvalue()
            if output:
                self._console.write(output.rstrip())

            errors = stderr_capture.getvalue()
            if errors:
                self._console.write_warning(errors.rstrip())

            # If df was reassigned or modified in the script, update the data view
            if "df" in namespace and isinstance(namespace["df"], pd.DataFrame):
                self._data_view.load_dataframe(namespace["df"])
                self._console.write_success("Data updated")

            # Extract any statistical models created
            for key, val in namespace.items():
                if hasattr(val, "model") and hasattr(val.model, "endog_names") and hasattr(val.model, "exog_names"):
                    model = val.model
                    y_name = model.endog_names
                    x_names = model.exog_names if isinstance(model.exog_names, list) else [model.exog_names]
                    x_names = [x for x in x_names if x != 'const']
                    model_info = (y_name, x_names)
                    if model_info not in self._model_history:
                        self._model_history.append(model_info)
                        self._console.write_success(f"Model saved to history: {y_name} ~ {', '.join(x_names)}")

        except Exception as e:
            self._console.write_error(str(e))
        finally:
            self._status_bar.hide_progress()

    # ── Data Dialogs ─────────────────────────────────────────────────────

    def _show_data_dialog(self, dialog_class) -> None:
        if self._data_view.get_dataframe().empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return

        dialog = dialog_class(self._data_view.get_dataframe(), self)
        
        if hasattr(dialog, "load_history"):
            dialog.load_history(self._script_editor.editor.get_all_text(), getattr(self, "_model_history", []))
        
        def handle_code(code: str) -> None:
            self._script_editor.append_code("\n" + code)
            self._execute_code(code)
            
        dialog.code_generated.connect(handle_code)
        dialog.exec()

    def _show_clean_data(self) -> None:
        self._show_data_dialog(CleanDataDialog)

    def _show_transform_data(self) -> None:
        self._show_data_dialog(TransformDataDialog)

    def _show_type_convert(self) -> None:
        self._show_data_dialog(TypeConvertDialog)

    def _show_filter_data(self) -> None:
        self._show_data_dialog(FilterDataDialog)

    def _show_merge_join(self) -> None:
        self._show_data_dialog(MergeJoinDialog)

    def _show_text_extract(self) -> None:
        self._show_data_dialog(TextExtractDialog)

    def _show_string_format(self) -> None:
        self._show_data_dialog(StringFormatDialog)

    def _show_find_replace(self) -> None:
        self._show_data_dialog(FindReplaceDialog)

    def _show_concat_cols(self) -> None:
        self._show_data_dialog(ConcatColsDialog)

    def _show_if_else(self) -> None:
        self._show_data_dialog(IfElseDialog)

    def _show_pivot_table(self) -> None:
        self._show_data_dialog(PivotTableDialog)

    # ── Statistics Dialogs ───────────────────────────────────────────────

    def _show_descriptive_stats(self) -> None:
        if self._data_view.get_dataframe().empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return

        dialog = DescriptiveStatsDialog(self._data_view.get_dataframe(), self)
        
        def handle_code(code: str) -> None:
            self._script_editor.append_code("\n" + code)
            self._execute_code(code)
            
        dialog.code_generated.connect(handle_code)
        dialog.exec()

    def _show_ttest(self) -> None:
        if self._data_view.get_dataframe().empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return

        dialog = TTestDialog(self._data_view.get_dataframe(), self)
        
        def handle_code(code: str) -> None:
            self._script_editor.append_code("\n" + code)
            self._execute_code(code)
            
        dialog.code_generated.connect(handle_code)
        dialog.exec()

    def _show_anova(self) -> None:
        self._show_data_dialog(AnovaModelComparisonDialog)

    def _show_chi_square(self) -> None:
        self._show_data_dialog(ChiSquareDialog)

    def _show_nonparametric(self) -> None:
        self._show_data_dialog(NonParametricDialog)

    def _show_correlation(self) -> None:
        self._show_data_dialog(CorrelationDialog)

    def _show_linear_regression(self) -> None:
        if self._data_view.get_dataframe().empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return

        dialog = LinearRegressionDialog(self._data_view.get_dataframe(), self)
        
        def handle_code(code: str) -> None:
            self._script_editor.append_code("\n" + code)
            self._execute_code(code)
            
        dialog.code_generated.connect(handle_code)
        dialog.exec()

    def _show_logistic_regression(self) -> None:
        if self._data_view.get_dataframe().empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return

        dialog = LogisticRegressionDialog(self._data_view.get_dataframe(), self)
        
        def handle_code(code: str) -> None:
            self._script_editor.append_code("\n" + code)
            self._execute_code(code)
            
        dialog.code_generated.connect(handle_code)
        dialog.exec()

    def _show_logistic_regression(self) -> None:
        if self._data_view.get_dataframe().empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return

        dialog = LogisticRegressionDialog(self._data_view.get_dataframe(), self)
        
        def handle_code(code: str) -> None:
            self._script_editor.append_code("\n" + code)
            self._execute_code(code)
            
        dialog.code_generated.connect(handle_code)
        dialog.exec()

    # ── Visualize Dialogs ────────────────────────────────────────────────

    def _show_histogram(self) -> None:
        self._show_data_dialog(HistogramDialog)

    def _show_scatter(self) -> None:
        self._show_data_dialog(ScatterPlotDialog)

    def _show_boxplot(self) -> None:
        self._show_data_dialog(BoxPlotDialog)

    def _show_barchart(self) -> None:
        self._show_data_dialog(BarChartDialog)

    def _show_violin(self) -> None:
        self._show_data_dialog(ViolinPlotDialog)

    def _show_linechart(self) -> None:
        self._show_data_dialog(LineChartDialog)

    def _show_heatmap(self) -> None:
        self._show_data_dialog(HeatmapDialog)

    def _show_chi_square(self) -> None:
        self._show_data_dialog(ChiSquareDialog)

    def _show_qqplot(self) -> None:
        self._show_data_dialog(QQPlotDialog)
        
    def _show_nonparametric(self) -> None:
        self._show_data_dialog(NonParametricDialog)

    # ── ML Classification Handlers ──────────────────────────────────────────
    
    def _show_model_compare(self) -> None:
        self._show_data_dialog(ModelComparisonDialog)

    def _show_cls_random_forest(self) -> None:
        self._show_data_dialog(RandomForestDialog)

    def _show_cls_gradient_boosting(self) -> None:
        self._show_data_dialog(GradientBoostingDialog)

    def _show_cls_decision_tree(self) -> None:
        self._show_data_dialog(DecisionTreeDialog)

    def _show_cls_svm(self) -> None:
        self._show_data_dialog(SVMDialog)

    def _show_cls_knn(self) -> None:
        self._show_data_dialog(KNNDialog)

    def _show_cls_lda(self) -> None:
        self._show_data_dialog(LDADialog)

    def _show_cls_qda(self) -> None:
        self._show_data_dialog(QDADialog)

    def _show_cls_naive_bayes(self) -> None:
        self._show_data_dialog(NaiveBayesDialog)

    # ── ML Clustering Handlers ──────────────────────────────────────────────
    
    def _show_clu_kmeans(self) -> None:
        self._show_data_dialog(KMeansDialog)

    def _show_clu_hierarchical(self) -> None:
        self._show_data_dialog(HierarchicalDialog)

    def _show_clu_dbscan(self) -> None:
        self._show_data_dialog(DBSCANDialog)

    def _show_clu_gmm(self) -> None:
        self._show_data_dialog(GMMDialog)

    def _show_pca(self) -> None:
        self._show_data_dialog(PCADialog)

    # ── Export & Report ──────────────────────────────────────────────────

    def _export_data(self) -> None:
        """Export the current dataset to CSV, Excel, JSON, or Parquet."""
        df = self._data_view.get_dataframe()
        if df.empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return

        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            str(get_exports_dir()),
            "CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json);;Parquet Files (*.parquet)",
        )
        if not path:
            return

        try:
            from PySide6.QtWidgets import QApplication
            self._status_bar.show_progress(0, 0, "Exporting data...")
            QApplication.processEvents()

            ext = Path(path).suffix.lower()
            if ext == ".csv":
                df.to_csv(path, index=False)
            elif ext == ".xlsx":
                df.to_excel(path, index=False)
            elif ext == ".json":
                df.to_json(path, orient="records", indent=2)
            elif ext == ".parquet":
                df.to_parquet(path, index=False)
            else:
                QMessageBox.warning(self, "Unsupported", f"Unsupported format: {ext}")
                return

            self._console.write_success(f"Exported {len(df):,} rows to {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
        finally:
            self._status_bar.hide_progress()

    def _export_script(self) -> None:
        """Export the script editor contents to a .py file."""
        script = self._script_editor.editor.get_all_text()
        if not script.strip():
            QMessageBox.warning(self, "Empty Script", "The script editor is empty.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Script", str(get_scripts_dir()), "Python Files (*.py)"
        )
        if not path:
            return

        try:
            Path(path).write_text(script, encoding="utf-8")
            self._console.write_success(f"Script saved to {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))

    def _generate_report(self) -> None:
        """Open the Report Generation dialog."""
        df = self._data_view.get_dataframe()
        script = self._script_editor.editor.get_all_text()
        results_html = self._results_view.get_all_html()

        dialog = ReportDialog(df, script, results_html, self)
        dialog.exec()

    # ── About dialog ─────────────────────────────────────────────────────

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Quantia",
            "<h2>Quantia</h2>"

            "<p>Version 0.1.1</p>"
            "<p>A fully offline, no-code statistical desktop application.</p>"
            "<p>Built with PySide6 (Qt6), pandas, numpy, scipy.</p>"
            f"<p style='color:#64748B; font-size:9pt;'>GPU: {get_gpu_info()} (CUDA {get_cuda_version()})</p>"
        )

    def _show_user_manual(self) -> None:
        dialog = UserManualDialog(self)
        dialog.exec()

    def _show_guided_wizard(self) -> None:
        dialog = GuidedWizardDialog(self)
        dialog.exec()
