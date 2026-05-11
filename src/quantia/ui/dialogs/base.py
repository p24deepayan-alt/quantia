"""Base class for all Quantia analysis dialogs.

Provides a consistent layout:
- Left: Variable selectors (drag & drop or arrow buttons)
- Right: Options/Settings specific to the test
- Bottom: Run, Cancel, Help buttons
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QSplitter,
)

from quantia.ui.icons import feather_icon


def _plotly_available() -> bool:
    """Check if plotly is importable."""
    try:
        import plotly  # noqa: F401
        return True
    except ImportError:
        return False


class BaseAnalysisDialog(QDialog):
    """Base dialog for statistical tests.

    Subclasses must implement `build_options()` to populate the right pane,
    and `generate_code()` to return the Python code string to execute.
    """

    # Emitted when Run is clicked. Contains the generated Python code.
    code_generated = Signal(str)

    def __init__(self, title: str, df: pd.DataFrame, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)
        self._df = df

        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        from quantia.theme.palette import PALETTE, Theme
        app = QApplication.instance()
        self._theme = app.get_current_theme() if isinstance(app, QuantiaApp) else Theme.LIGHT
        self._icon_color = PALETTE[self._theme]["text_primary"]

        layout = QVBoxLayout(self)

        # ── Splitter for Main Content ────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left pane: Variable selection
        self._left_pane = QWidget()
        left_layout = QVBoxLayout(self._left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_vars = QLabel("Available Variables:")
        lbl_vars.setStyleSheet("font-weight: 600;")
        left_layout.addWidget(lbl_vars)

        self.list_available = QListWidget()
        self.list_available.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._populate_variables()
        left_layout.addWidget(self.list_available)

        self._build_selectors(left_layout) # Subclasses add target lists here
        
        splitter.addWidget(self._left_pane)

        # Right pane: Options
        self._right_pane = QWidget()
        self._right_layout = QVBoxLayout(self._right_pane)
        self._right_layout.setContentsMargins(12, 0, 0, 0)
        
        lbl_options = QLabel("Options:")
        lbl_options.setStyleSheet("font-weight: 600;")
        self._right_layout.addWidget(lbl_options)
        
        self.build_options(self._right_layout)

        # Backend selector (only when plotly is installed)
        self._backend = "matplotlib"
        if _plotly_available():
            from PySide6.QtWidgets import QGroupBox, QComboBox
            group_backend = QGroupBox("Rendering Backend")
            l_backend = QVBoxLayout(group_backend)
            self.cmb_backend = QComboBox()
            self.cmb_backend.addItems(["Matplotlib", "Plotly"])
            self.cmb_backend.currentTextChanged.connect(self._on_backend_changed)
            l_backend.addWidget(self.cmb_backend)
            self._right_layout.addWidget(group_backend)

        self._right_layout.addStretch()

        splitter.addWidget(self._right_pane)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # ── Button Box ───────────────────────────────────────────────────
        self._button_box = QDialogButtonBox()
        
        self.btn_run = QPushButton("Run")
        self.btn_run.setObjectName("primaryButton") # Uses QSS primary styling
        self.btn_run.setIcon(feather_icon("play", "#FFFFFF", 14))
        self._button_box.addButton(self.btn_run, QDialogButtonBox.ButtonRole.AcceptRole)
        
        self.btn_cancel = QPushButton("Cancel")
        self._button_box.addButton(self.btn_cancel, QDialogButtonBox.ButtonRole.RejectRole)
        
        self.btn_help = QPushButton("Help")
        self.btn_help.setIcon(feather_icon("help-circle", self._icon_color, 14))
        self._button_box.addButton(self.btn_help, QDialogButtonBox.ButtonRole.HelpRole)

        self._button_box.accepted.connect(self._on_run)
        self._button_box.rejected.connect(self.reject)

        layout.addWidget(self._button_box)

    # ── Internal Helpers ─────────────────────────────────────────────────

    def _populate_variables(self) -> None:
        """Populate the 'Available Variables' list from the DataFrame."""
        for col in self._df.columns:
            item = QListWidgetItem(f"{col}")
            # Could add icon here based on dtype like in VariableListPanel
            self.list_available.addItem(item)

    def _create_selector_row(self, label_text: str, target_list: QListWidget, multi_select: bool = False) -> QWidget:
        """Helper to create a variable target list with Add/Remove buttons."""
        target_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection if multi_select else QListWidget.SelectionMode.SingleSelection
        )
        
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.addStretch()
        
        btn_add = QPushButton()
        btn_add.setIcon(feather_icon("chevron-right", self._icon_color, 16))
        btn_add.setToolTip(f"Add to {label_text}")
        btn_add.clicked.connect(lambda: self._move_items(self.list_available, target_list, multi_select))
        btn_layout.addWidget(btn_add)
        
        if multi_select:
            btn_add_all = QPushButton()
            btn_add_all.setIcon(feather_icon("chevrons-right", self._icon_color, 16))
            btn_add_all.setToolTip(f"Add ALL to {label_text}")
            btn_add_all.clicked.connect(lambda: self._move_all_items(self.list_available, target_list, multi_select))
            btn_layout.addWidget(btn_add_all)
        
        btn_remove = QPushButton()
        btn_remove.setIcon(feather_icon("chevron-left", self._icon_color, 16))
        btn_remove.setToolTip(f"Remove from {label_text}")
        btn_remove.clicked.connect(lambda: self._move_items(target_list, self.list_available, True))
        btn_layout.addWidget(btn_remove)

        if multi_select:
            btn_remove_all = QPushButton()
            btn_remove_all.setIcon(feather_icon("chevrons-left", self._icon_color, 16))
            btn_remove_all.setToolTip(f"Remove ALL from {label_text}")
            btn_remove_all.clicked.connect(lambda: self._move_all_items(target_list, self.list_available, True))
            btn_layout.addWidget(btn_remove_all)
        
        btn_layout.addStretch()
        h_layout.addLayout(btn_layout)

        # Target list
        target_container = QWidget()
        t_layout = QVBoxLayout(target_container)
        t_layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        t_layout.addWidget(lbl)
        t_layout.addWidget(target_list)
        
        h_layout.addWidget(target_container)
        return container

    def _move_items(self, source: QListWidget, dest: QListWidget, multi: bool) -> None:
        """Move selected items between two QListWidgets."""
        items = source.selectedItems()
        if not items:
            return
            
        if not multi and dest.count() >= 1:
            # If destination only allows 1, move the existing one back to source
            existing = dest.takeItem(0)
            source.addItem(existing)
            
        for item in items:
            row = source.row(item)
            source.takeItem(row)
            dest.addItem(item)

    def _move_all_items(self, source: QListWidget, dest: QListWidget, multi: bool) -> None:
        """Move all items between two QListWidgets."""
        if not multi and source.count() > 1:
            return
            
        if not multi and dest.count() >= 1:
            existing = dest.takeItem(0)
            source.addItem(existing)
            
        while source.count() > 0:
            item = source.takeItem(0)
            dest.addItem(item)

    def _on_run(self) -> None:
        """Triggered when Run is clicked. Generates code and emits."""
        code = self.generate_code()
        if code:
            self.code_generated.emit(code)
            self.accept()

    # ── Abstract Methods for Subclasses ──────────────────────────────────

    def _build_selectors(self, layout: QVBoxLayout) -> None:
        """Override to add target variable lists (e.g., 'Variables', 'Grouping')."""
        pass

    def build_options(self, layout: QVBoxLayout) -> None:
        """Override to add widgets to the right 'Options' pane."""
        pass

    def generate_code(self) -> str:
        """Override to return the generated Python code."""
        return ""

    def _on_backend_changed(self, text: str) -> None:
        """Called when the backend combo box changes."""
        self._backend = text.lower()

    def _is_plotly(self) -> bool:
        """Return True if the user selected Plotly backend."""
        return self._backend == "plotly"
