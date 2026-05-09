import enum
from PySide6.QtCore import QSettings

class ComputeMode(enum.Enum):
    CPU_SINGLE = "cpu_single"
    CPU_MULTI = "cpu_multi"
    GPU = "gpu"

class SettingsManager:
    """Manages application settings using QSettings."""
    
    def __init__(self):
        self._settings = QSettings("QuantiaApp", "Quantia")
        
    @property
    def compute_mode(self) -> ComputeMode:
        mode_str = self._settings.value("compute_mode", ComputeMode.CPU_SINGLE.value)
        try:
            return ComputeMode(mode_str)
        except ValueError:
            return ComputeMode.CPU_SINGLE
            
    @compute_mode.setter
    def compute_mode(self, mode: ComputeMode):
        self._settings.setValue("compute_mode", mode.value)
