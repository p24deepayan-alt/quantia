from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QRadioButton, QButtonGroup, QPushButton, QLabel
)
from quantia.core.settings import SettingsManager, ComputeMode

class PreferencesDialog(QDialog):
    """Dialog for configuring application preferences."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(500, 400)
        self.settings_manager = SettingsManager()
        
        self._build_ui()
        self._load_settings()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add tabs
        self._build_general_tab()
        self._build_compute_tab()
        self._build_scripting_tab()
        self._build_appearance_tab()
        self._build_report_tab()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
    def _build_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("General settings placeholder"))
        layout.addStretch()
        self.tabs.addTab(widget, "General")
        
    def _build_compute_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.compute_group = QGroupBox("Compute Backend")
        comp_layout = QVBoxLayout(self.compute_group)
        
        self.btn_cpu_single = QRadioButton("CPU - single core")
        self.btn_cpu_multi = QRadioButton("CPU - Multi core")
        
        self.compute_btn_group = QButtonGroup(self)
        self.compute_btn_group.addButton(self.btn_cpu_single, 0)
        self.compute_btn_group.addButton(self.btn_cpu_multi, 1)
        
        comp_layout.addWidget(self.btn_cpu_single)
        comp_layout.addWidget(self.btn_cpu_multi)
        
        self.warning_label = QLabel("⚠️ Multi core will use more compute power and battery.")
        self.warning_label.setStyleSheet("color: #E65100; font-size: 9pt;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        comp_layout.addWidget(self.warning_label)
        
        self.btn_cpu_multi.toggled.connect(self.warning_label.setVisible)
        
        layout.addWidget(self.compute_group)
        layout.addStretch()
        
        self.tabs.addTab(widget, "Compute")
        
    def _build_scripting_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Scripting settings placeholder"))
        layout.addStretch()
        self.tabs.addTab(widget, "Scripting")
        
    def _build_appearance_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Appearance settings placeholder"))
        layout.addStretch()
        self.tabs.addTab(widget, "Appearance")
        
    def _build_report_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Report settings placeholder"))
        layout.addStretch()
        self.tabs.addTab(widget, "Report")
        
    def _load_settings(self):
        mode = self.settings_manager.compute_mode
        if mode == ComputeMode.CPU_SINGLE:
            self.btn_cpu_single.setChecked(True)
        elif mode == ComputeMode.CPU_MULTI:
            self.btn_cpu_multi.setChecked(True)
            
    def accept(self):
        # Save settings
        if self.btn_cpu_single.isChecked():
            self.settings_manager.compute_mode = ComputeMode.CPU_SINGLE
        elif self.btn_cpu_multi.isChecked():
            self.settings_manager.compute_mode = ComputeMode.CPU_MULTI
            
        super().accept()
