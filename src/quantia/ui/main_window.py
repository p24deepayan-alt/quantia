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
from PySide6.QtCore import Qt, QSize
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
from quantia.ui.menu_bar import QuantiaMenuBar
from quantia.ui.toolbar import QuantiaToolbar
from quantia.ui.status_bar import QuantiaStatusBar
from quantia.ui.panels.variable_list import VariableListPanel
from quantia.ui.panels.console import ConsolePanel
from quantia.ui.central.data_view import DataViewWidget
from quantia.ui.central.script_editor import ScriptEditorWidget
from quantia.ui.central.results_view import ResultsViewWidget
from quantia.ui.central.plot_view import PlotViewWidget
from quantia.ui.dialogs.descriptive import DescriptiveStatsDialog
from quantia.ui.dialogs.ttest import TTestDialog
from quantia.ui.dialogs.regression import LinearRegressionDialog
from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
from quantia.ui.dialogs.clean_data import CleanDataDialog
from quantia.ui.dialogs.transform import TransformDataDialog
from quantia.ui.dialogs.type_convert import TypeConvertDialog
from quantia.ui.dialogs.filter_data import FilterDataDialog
from quantia.ui.dialogs.merge_join import MergeJoinDialog
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
from quantia.ui.dialogs.clustering import (
    KMeansDialog, HierarchicalDialog, DBSCANDialog, GMMDialog
)
from quantia.ui.dialogs.report import ReportDialog
from quantia.ui.dialogs.help import UserManualDialog, GuidedWizardDialog


_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_LOGO_PATH = _PROJECT_ROOT / "reference" / "logo" / "69e99e05-da76-4624-b75e-3f64158aa657_removalai_preview.png"


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

        if _LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(_LOGO_PATH)))

        # ── Menu bar ─────────────────────────────────────────────────────
        self._menu_bar = QuantiaMenuBar(self)
        self.setMenuBar(self._menu_bar)

        # ── Toolbar ──────────────────────────────────────────────────────
        self._toolbar = QuantiaToolbar(self)
        self.addToolBar(self._toolbar)

        # ── Status bar ───────────────────────────────────────────────────
        self._status_bar = QuantiaStatusBar(self)
        self.setStatusBar(self._status_bar)

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

        # Workflow tab (placeholder)
        workflow_placeholder = QLabel("Workflow Builder — coming in Phase 5")
        workflow_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        workflow_placeholder.setStyleSheet("font-size: 14px; color: #6B7280;")
        self._tabs.addTab(workflow_placeholder, feather_icon("share-2", "#000000", 14), "Workflow")

        # Plots tab
        self._plot_view = PlotViewWidget()
        self._tabs.addTab(self._plot_view, feather_icon("pie-chart", "#000000", 14), "Plots")

        self.setCentralWidget(self._tabs)

        # ── Left dock: Variable List ─────────────────────────────────────
        self._variable_panel = VariableListPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._variable_panel)

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
        self._menu_bar.new_project.connect(self._new_project)
        self._menu_bar.open_project.connect(self._open_project)
        self._menu_bar.save_project.connect(self._save_project)
        self._menu_bar.save_as.connect(self._save_project_as)
        self._toolbar.new_project.connect(self._new_project)
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

        # Data menu signals
        self._menu_bar.clean_data.connect(self._show_clean_data)
        self._menu_bar.transform_data.connect(self._show_transform_data)
        self._menu_bar.type_convert.connect(self._show_type_convert)
        self._menu_bar.filter_data.connect(self._show_filter_data)
        self._menu_bar.merge_join.connect(self._show_merge_join)

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

    def _update_window_title(self) -> None:
        if self._current_project_path:
            name = Path(self._current_project_path).name
            self.setWindowTitle(f"Quantia — {name}")
        else:
            self.setWindowTitle("Quantia — Untitled")

    def _new_project(self) -> None:
        if not self._data_view.df.empty:
            ans = QMessageBox.question(
                self,
                "New Project",
                "Are you sure you want to start a new project? Unsaved changes will be lost.",
            )
            if ans != QMessageBox.StandardButton.Yes:
                return

        self._data_view.set_dataframe(pd.DataFrame())
        self._script_editor.set_text("# Quantia Analysis Script\n\nimport pandas as pd\nimport numpy as np\n\n# Data will be loaded from the project file\ndf = pd.DataFrame()\n")
        self._results_view.clear()
        self._plot_view.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._model_history.clear()
        self._variable_panel.populate([])
        self._console.clear()
        self._console.info("Started new project.")
        self._current_project_path = None
        self._update_window_title()

    def _save_project(self) -> None:
        if not self._current_project_path:
            self._save_project_as()
        else:
            self._write_project_file(self._current_project_path)

    def _save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "", "Quantia Project (*.quantia)"
        )
        if path:
            if not path.endswith(".quantia"):
                path += ".quantia"
            self._write_project_file(path)

    def _write_project_file(self, path: str) -> None:
        try:
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # Save Dataframe
                if not self._data_view.df.empty:
                    df_bytes = io.BytesIO()
                    self._data_view.df.to_parquet(df_bytes)
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

            self._current_project_path = path
            self._update_window_title()
            self._console.success(f"Project saved to {path}")
        except Exception as e:
            self._console.error(f"Failed to save project: {e}")
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
                    self._data_view.set_dataframe(df)
                    self._variable_panel.populate(df.columns.tolist())
                else:
                    self._data_view.set_dataframe(pd.DataFrame())
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
            self._console.success(f"Project loaded from {path}")
            
            # Automatically run the script to repopulate results and plots
            self._run_all_script()

        except Exception as e:
            self._console.error(f"Failed to open project: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to open project:\n{e}")

    # ── Data import ──────────────────────────────────────────────────────

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

            if ext == ".csv":
                df = pd.read_csv(path, low_memory=False)
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
            code_map = {
                ".csv": f"df = pd.read_csv(r'{path}', low_memory=False)",
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

                df = pd.read_csv(path, low_memory=False)
                self._data_view.load_dataframe(df)
                self._console.write_success(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
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
            "",
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
            self, "Export Script", "quantia_script.py", "Python Files (*.py)"
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

            "<p>Version 0.1.0 (Alpha)</p>"
            "<p>A fully offline, no-code statistical desktop application.</p>"
            "<p>Built with PySide6 (Qt6), pandas, numpy, scipy.</p>"
        )

    def _show_user_manual(self) -> None:
        dialog = UserManualDialog(self)
        dialog.exec()

    def _show_guided_wizard(self) -> None:
        dialog = GuidedWizardDialog(self)
        dialog.exec()
