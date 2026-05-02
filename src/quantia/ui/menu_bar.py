"""Menu bar for the Quantia main window.

Full menu structure from GUI.md §1.1:
File, Edit, Data, Statistics, Machine Learning, Visualize, Report, Help
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenuBar, QWidget, QMenu

from quantia.ui.icons import feather_icon


class QuantiaMenuBar(QMenuBar):
    """Application menu bar with the full Quantia menu structure."""

    # ── Signals ──────────────────────────────────────────────────────────
    # File
    import_csv = Signal()
    import_excel = Signal()
    import_json = Signal()
    import_parquet = Signal()
    export_data = Signal()
    exit_app = Signal()

    # Edit
    undo = Signal()
    redo = Signal()

    # Data
    clean_data = Signal()
    transform_data = Signal()
    type_convert = Signal()
    filter_data = Signal()
    merge_join = Signal()

    # Statistics
    descriptive_stats = Signal()
    ttest = Signal()
    anova = Signal()
    correlation = Signal()
    regression_linear = Signal()
    regression_logistic = Signal()
    chi_square = Signal()
    nonparametric = Signal()

    # ML Classification
    cls_random_forest = Signal()
    cls_gradient_boosting = Signal()
    cls_decision_tree = Signal()
    cls_svm = Signal()
    cls_knn = Signal()
    cls_lda = Signal()
    cls_qda = Signal()
    cls_naive_bayes = Signal()
    
    # ML Clustering
    clu_kmeans = Signal()
    clu_hierarchical = Signal()
    clu_dbscan = Signal()
    clu_gmm = Signal()

    # Visualize
    histogram = Signal()
    boxplot = Signal()
    scatter = Signal()
    violin = Signal()
    qqplot = Signal()
    line_chart = Signal()
    bar_chart = Signal()
    heatmap = Signal()

    # Report
    generate_report = Signal()
    export_script = Signal()

    # Help
    user_manual = Signal()
    guided_wizard = Signal()
    about = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        ic = "#2D3E50"  # icon colour for light theme
        self._build_file_menu(ic)
        self._build_edit_menu(ic)
        self._build_data_menu(ic)
        self._build_statistics_menu(ic)
        self._build_ml_menu(ic)
        self._build_visualize_menu(ic)
        self._build_report_menu(ic)
        self._build_help_menu(ic)

    # ── File ─────────────────────────────────────────────────────────────

    def _build_file_menu(self, ic: str) -> None:
        menu = self.addMenu("&File")

        import_menu = menu.addMenu("Import Data")
        import_menu.setIcon(feather_icon("download", ic, 14))
        import_menu.setProperty("icon_name", "download")
        self._add(import_menu, "CSV (.csv)", self.import_csv, "file-text", ic)
        self._add(import_menu, "Excel (.xls, .xlsx)", self.import_excel, "grid", ic)
        self._add(import_menu, "JSON (.json)", self.import_json, "file-text", ic)
        self._add(import_menu, "Parquet (.parquet)", self.import_parquet, "hard-drive", ic)

        self._add(menu, "Export Data…", self.export_data, "upload", ic)
        menu.addSeparator()
        self._add(menu, "Exit", self.exit_app, "log-out", ic, QKeySequence("Ctrl+Q"))

    # ── Edit ─────────────────────────────────────────────────────────────

    def _build_edit_menu(self, ic: str) -> None:
        menu = self.addMenu("&Edit")
        self._add(menu, "Undo", self.undo, "rotate-ccw", ic, QKeySequence.StandardKey.Undo)
        self._add(menu, "Redo", self.redo, "rotate-cw", ic, QKeySequence.StandardKey.Redo)

    # ── Data ─────────────────────────────────────────────────────────────

    def _build_data_menu(self, ic: str) -> None:
        menu = self.addMenu("&Data")
        self._add(menu, "Clean Data (Drop NA, Drop Cols, Impute)…", self.clean_data, "filter", ic)
        self._add(menu, "Transform Data (Math)…", self.transform_data, "sliders", ic)
        self._add(menu, "Type & String Conversion…", self.type_convert, "type", ic)
        self._add(menu, "Filter Data (Subset Rows)…", self.filter_data, "scissors", ic)
        menu.addSeparator()
        self._add(menu, "Merge / Join…", self.merge_join, "git-merge", ic)

    # ── Statistics ───────────────────────────────────────────────────────

    def _build_statistics_menu(self, ic: str) -> None:
        menu = self.addMenu("&Statistics")
        self._add(menu, "Descriptive Statistics…", self.descriptive_stats, "bar-chart-2", ic)
        menu.addSeparator()
        self._add(menu, "t-test…", self.ttest, "activity", ic)
        self._add(menu, "ANOVA…", self.anova, "activity", ic)
        self._add(menu, "Non-parametric Tests…", self.nonparametric, "activity", ic)
        menu.addSeparator()
        self._add(menu, "Correlation…", self.correlation, "trending-up", ic)
        self._add(menu, "Chi-square…", self.chi_square, "grid", ic)

    # ── Machine Learning ─────────────────────────────────────────────────

    def _build_ml_menu(self, ic: str) -> None:
        menu = self.addMenu("&Machine Learning")
        reg_menu = menu.addMenu("Regression")
        reg_menu.setIcon(feather_icon("trending-up", ic, 14))
        reg_menu.setProperty("icon_name", "trending-up")
        self._add(reg_menu, "Linear Regression…", self.regression_linear, "trending-up", ic)
        self._add(reg_menu, "Logistic Regression…", self.regression_logistic, "trending-up", ic)
        
        cls_menu = menu.addMenu("Classification")
        cls_menu.setIcon(feather_icon("cpu", ic, 14))
        cls_menu.setProperty("icon_name", "cpu")
        self._add(cls_menu, "Random Forest…", self.cls_random_forest, "cpu", ic)
        self._add(cls_menu, "Gradient Boosting…", self.cls_gradient_boosting, "cpu", ic)
        self._add(cls_menu, "Decision Tree…", self.cls_decision_tree, "cpu", ic)
        self._add(cls_menu, "Support Vector Machine (SVM)…", self.cls_svm, "cpu", ic)
        self._add(cls_menu, "K-Nearest Neighbors (KNN)…", self.cls_knn, "cpu", ic)
        self._add(cls_menu, "Linear Discriminant Analysis (LDA)…", self.cls_lda, "cpu", ic)
        self._add(cls_menu, "Quadratic Discriminant Analysis (QDA)…", self.cls_qda, "cpu", ic)
        self._add(cls_menu, "Naive Bayes…", self.cls_naive_bayes, "cpu", ic)

        clu_menu = menu.addMenu("Clustering")
        clu_menu.setIcon(feather_icon("share-2", ic, 14))
        clu_menu.setProperty("icon_name", "share-2")
        self._add(clu_menu, "K-Means…", self.clu_kmeans, "share-2", ic)
        self._add(clu_menu, "Hierarchical…", self.clu_hierarchical, "share-2", ic)
        self._add(clu_menu, "DBSCAN…", self.clu_dbscan, "share-2", ic)
        self._add(clu_menu, "Gaussian Mixture Model (GMM)…", self.clu_gmm, "share-2", ic)

    # ── Visualize ────────────────────────────────────────────────────────

    def _build_visualize_menu(self, ic: str) -> None:
        menu = self.addMenu("&Visualize")
        self._add(menu, "Histogram", self.histogram, "bar-chart-2", ic)
        self._add(menu, "Box Plot", self.boxplot, "minus-square", ic)
        self._add(menu, "Scatter Plot", self.scatter, "crosshair", ic)
        self._add(menu, "Violin Plot", self.violin, "activity", ic)
        self._add(menu, "Q-Q Plot", self.qqplot, "trending-up", ic)
        menu.addSeparator()
        self._add(menu, "Line Chart", self.line_chart, "trending-up", ic)
        self._add(menu, "Bar Chart", self.bar_chart, "bar-chart", ic)
        self._add(menu, "Heatmap", self.heatmap, "grid", ic)

    # ── Report ───────────────────────────────────────────────────────────

    def _build_report_menu(self, ic: str) -> None:
        menu = self.addMenu("&Report")
        self._add(menu, "Generate Report (HTML/PDF)…", self.generate_report, "file-text", ic)
        self._add(menu, "Export Script (.py)…", self.export_script, "code", ic)

    # ── Help ─────────────────────────────────────────────────────────────

    def _build_help_menu(self, ic: str) -> None:
        menu = self.addMenu("&Help")
        self._add(menu, "User Manual", self.user_manual, "book-open", ic)
        self._add(menu, "Guided Analysis Wizard…", self.guided_wizard, "help-circle", ic)
        menu.addSeparator()
        self._add(menu, "About Quantia", self.about, "info", ic)

    def refresh_icons(self, color: str) -> None:
        """Update all menu icons to a new colour."""
        # Update icons in all submenus
        for menu in self.findChildren(QMenu):
            # Check the menu's own icon (e.g. for Regression)
            icon_name = menu.property("icon_name")
            if icon_name:
                menu.setIcon(feather_icon(icon_name, color, 14))
                
            for action in menu.actions():
                name = action.property("icon_name")
                if name:
                    action.setIcon(feather_icon(name, color, 14))

    # ── Helper ───────────────────────────────────────────────────────────

    @staticmethod
    def _add(
        menu,
        text: str,
        signal: Signal,
        icon_name: str | None,
        icon_color: str,
        shortcut: QKeySequence | None = None,
    ) -> QAction:
        if icon_name:
            action = menu.addAction(feather_icon(icon_name, icon_color), text)
            action.setProperty("icon_name", icon_name)
        else:
            action = menu.addAction(text)
        action.triggered.connect(signal.emit)
        if shortcut is not None:
            action.setShortcut(shortcut)
        return action
