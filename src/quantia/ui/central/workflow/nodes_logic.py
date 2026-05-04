"""Logical wrappers for visual nodes."""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox
from quantia.utils.paths import get_exports_dir, get_quantia_root

from quantia.ui.central.workflow.items import NodeItem
from quantia.ui.dialogs.clean_data import CleanDataDialog


class BaseLogicNode(NodeItem):
    """A NodeItem that holds a DataFrame state and logic."""
    
    def __init__(self, title: str, x: float = 0, y: float = 0) -> None:
        super().__init__(title, x, y)
        self.output_df: pd.DataFrame | None = None
        self._code: str = ""
        
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        """Process inputs and set self.output_df and self._code."""
        pass
        
    def get_code(self) -> str:
        return self._code
        
    def configure(self) -> None:
        """Open a dialog to configure this node."""
        pass

    def mouseDoubleClickEvent(self, event) -> None:
        self.configure()
        event.accept()


class LoadCSVNode(BaseLogicNode):
    """Node that imports a CSV."""
    
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Load CSV", x, y)
        self.sub_item.setPlainText("No file selected")
        self.file_path: str = ""
        
        # Sources have no input port
        self.in_port.hide()
        
    def configure(self) -> None:
        path, _ = QFileDialog.getOpenFileName(None, "Select CSV", str(get_quantia_root()), "CSV Files (*.csv)")
        if path:
            self.file_path = path
            self.sub_item.setPlainText(path.split("/")[-1])
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not self.file_path:
            raise ValueError("No CSV file selected.")
            
        self.output_df = pd.read_csv(self.file_path)
        self._code = f"df = pd.read_csv('{self.file_path}')"


class CleanDataNode(BaseLogicNode):
    """Node that drops NAs or fills them."""
    
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Clean Data", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self.dialog_state = None
        self._configured_code = ""
        
    def configure(self) -> None:
        # We need the upstream df to configure properly
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
                    
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first to configure.")
            return
            
        df = input_dfs[0]
        dialog = CleanDataDialog(df)
        
        if dialog.exec():
            # We don't want it to emit to main window, we just want the code
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs:
            raise ValueError("Clean Data node requires an input.")
            
        df = input_dfs[0].copy()
        self.output_df = df.dropna()
        
        if self._configured_code:
            self._code = self._configured_code
        else:
            self._code = "df = df.dropna()"


class ExportCSVNode(BaseLogicNode):
    """Node that exports a CSV."""
    
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Export CSV", x, y)
        self.sub_item.setPlainText("No file selected")
        self.file_path: str = ""
        
        # Sinks have no output port
        self.out_port.hide()
        
    def configure(self) -> None:
        path, _ = QFileDialog.getSaveFileName(None, "Save CSV", str(get_exports_dir()), "CSV Files (*.csv)")
        if path:
            self.file_path = path
            self.sub_item.setPlainText(path.split("/")[-1])
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs:
            raise ValueError("Export CSV node requires an input.")
        if not self.file_path:
            raise ValueError("No save path selected.")
            
        df = input_dfs[0]
        df.to_csv(self.file_path, index=False)
        self._code = f"df.to_csv('{self.file_path}', index=False)"
