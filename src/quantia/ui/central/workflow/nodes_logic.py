"""Logical wrappers for visual nodes."""

from __future__ import annotations

import pandas as pd
import polars as pl
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
        
    def clear_data(self) -> None:
        """Free memory by clearing the cached DataFrame."""
        self.output_df = None
        # We keep the _code so the node can still be inspected, 
        # but it would need to be re-run to get output_df back.

    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        """Process inputs and set self.output_df and self._code."""
        pass
        
    def get_code(self) -> str:
        return self._code
        
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "x": self.pos().x(),
            "y": self.pos().y()
        }

    def from_dict(self, data: dict) -> None:
        self.id = data.get("id", self.id)
        
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
        
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["file_path"] = self.file_path
        return data

    def from_dict(self, data: dict) -> None:
        super().from_dict(data)
        self.file_path = data.get("file_path", "")
        if self.file_path:
            self.sub_item.setPlainText(self.file_path.split("/")[-1])
            self._code = f"df = pd.read_csv('{self.file_path}')"
            
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
        
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["_configured_code"] = self._configured_code
        return data

    def from_dict(self, data: dict) -> None:
        super().from_dict(data)
        self._configured_code = data.get("_configured_code", "")
        if self._configured_code:
            self.sub_item.setPlainText("Configured")
            self._code = self._configured_code
            
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
            
    def run_logic(self, input_dfs: list[pd.DataFrame | pl.DataFrame]) -> None:
        if not input_dfs:
            raise ValueError("Clean Data node requires an input.")
            
        df = input_dfs[0]
        # Handle Polars vs Pandas copy/clone
        snapshot = df.clone() if isinstance(df, pl.DataFrame) else df.copy()
        
        if isinstance(snapshot, pl.DataFrame):
            self.output_df = snapshot.drop_nulls()
        else:
            self.output_df = snapshot.dropna()
        
        if self._configured_code:
            self._code = self._configured_code
        else:
            if isinstance(df, pl.DataFrame):
                self._code = "df = df.drop_nulls()"
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
        
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["file_path"] = self.file_path
        return data

    def from_dict(self, data: dict) -> None:
        super().from_dict(data)
        self.file_path = data.get("file_path", "")
        if self.file_path:
            self.sub_item.setPlainText(self.file_path.split("/")[-1])
            self._code = f"df.to_csv('{self.file_path}', index=False)"
            
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


from quantia.ui.dialogs.pca import PCADialog
from quantia.ui.dialogs.regression import LinearRegressionDialog
from quantia.ui.dialogs.ttest import TTestDialog
from quantia.ui.dialogs.descriptive import DescriptiveStatsDialog
from quantia.ui.dialogs.correlation import CorrelationDialog
from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
from quantia.ui.dialogs.chi_square import ChiSquareDialog
from quantia.ui.dialogs.classification import (
    RandomForestDialog, GradientBoostingDialog, DecisionTreeDialog,
    SVMDialog, KNNDialog, LDADialog, QDADialog, NaiveBayesDialog
)
from quantia.ui.dialogs.clustering import (
    KMeansDialog, HierarchicalDialog, DBSCANDialog, GMMDialog
)
from quantia.ui.dialogs.tree_regression import (
    DecisionTreeRegressorDialog, RandomForestRegressorDialog
)
from quantia.ui.dialogs.histogram import HistogramDialog
from quantia.ui.dialogs.boxplot import BoxPlotDialog
from quantia.ui.dialogs.scatter import ScatterPlotDialog
from quantia.ui.dialogs.barchart import BarChartDialog
from quantia.ui.dialogs.heatmap import HeatmapDialog
from quantia.ui.dialogs.linechart import LineChartDialog
from quantia.ui.dialogs.violinplot import ViolinPlotDialog
from quantia.ui.dialogs.qqplot import QQPlotDialog

class PCANode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("PCA", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["_configured_code"] = self._configured_code
        return data

    def from_dict(self, data: dict) -> None:
        super().from_dict(data)
        self._configured_code = data.get("_configured_code", "")
        if self._configured_code:
            self.sub_item.setPlainText("Configured")
            self._code = self._configured_code
            
    def configure(self) -> None:
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
        dialog = PCADialog(df)
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs:
            raise ValueError("PCA node requires an input.")
            
        self.output_df = input_dfs[0] # pass through
        if self._configured_code:
            self._code = self._configured_code
        else:
            self._code = "# PCA not configured"

class LinearRegressionNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Linear Regression", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["_configured_code"] = self._configured_code
        return data

    def from_dict(self, data: dict) -> None:
        super().from_dict(data)
        self._configured_code = data.get("_configured_code", "")
        if self._configured_code:
            self.sub_item.setPlainText("Configured")
            self._code = self._configured_code
            
    def configure(self) -> None:
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
        dialog = LinearRegressionDialog(df)
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs:
            raise ValueError("Linear Regression node requires an input.")
            
        self.output_df = input_dfs[0] # pass through
        if self._configured_code:
            self._code = self._configured_code
        else:
            self._code = "# Linear Regression not configured"

class TTestNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("T-Test", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = TTestDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# T-Test not configured"

class DescriptiveStatsNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Descriptive Stats", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = DescriptiveStatsDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Descriptive Stats not configured"

class CorrelationNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Correlation", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = CorrelationDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Correlation not configured"

class LogisticRegressionNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Logistic Regression", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = LogisticRegressionDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Logistic Regression not configured"

class ChiSquareNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Chi-Square", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = ChiSquareDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Chi-Square not configured"

class RandomForestNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Random Forest", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = RandomForestDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Random Forest not configured"

class KMeansNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("K-Means", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = KMeansDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# K-Means not configured"

class HistogramNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Histogram", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = HistogramDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Histogram not configured"

class BoxPlotNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Box Plot", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = BoxPlotDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Box Plot not configured"

class ScatterPlotNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Scatter Plot", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = ScatterPlotDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Scatter Plot not configured"

class BarChartNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Bar Chart", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = BarChartDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Bar Chart not configured"

class HeatmapNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Heatmap", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = HeatmapDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Heatmap not configured"

class LineChartNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Line Chart", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = LineChartDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Line Chart not configured"

class ViolinPlotNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Violin Plot", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = ViolinPlotDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Violin Plot not configured"

class QQPlotNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Q-Q Plot", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = QQPlotDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Q-Q Plot not configured"

class GradientBoostingNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Gradient Boosting", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = GradientBoostingDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Gradient Boosting not configured"

class DecisionTreeNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Decision Tree", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = DecisionTreeDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Decision Tree not configured"

class SVMNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("SVM", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = SVMDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# SVM not configured"

class KNNNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("KNN", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = KNNDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# KNN not configured"

class LDANode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("LDA", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = LDADialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# LDA not configured"

class QDANode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("QDA", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = QDADialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# QDA not configured"

class NaiveBayesNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Naive Bayes", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = NaiveBayesDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Naive Bayes not configured"

class HierarchicalNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Hierarchical Clustering", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = HierarchicalDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Hierarchical not configured"

class DBSCANNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("DBSCAN", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = DBSCANDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# DBSCAN not configured"

class GMMNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("GMM", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = GMMDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# GMM not configured"

class DecisionTreeRegressorNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Decision Tree Regressor", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = DecisionTreeRegressorDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Decision Tree Regressor not configured"

class RandomForestRegressorNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Random Forest Regressor", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self._configured_code = ""
        
    def configure(self) -> None:
        input_dfs = []
        for edge in self.in_port.edges:
            if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                src_df = edge.source_port.node.output_df
                if src_df is not None:
                    input_dfs.append(src_df)
        if not input_dfs:
            QMessageBox.warning(None, "No Data", "Connect and run an upstream node first.")
            return
        dialog = RandomForestRegressorDialog(input_dfs[0])
        if dialog.exec():
            self._configured_code = dialog.generate_code()
            self.sub_item.setPlainText("Configured")
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs: raise ValueError("Requires input.")
        self.output_df = input_dfs[0]
        self._code = self._configured_code if self._configured_code else "# Random Forest Regressor not configured"

class SaveReportNode(BaseLogicNode):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__("Save Report", x, y)
        self.sub_item.setPlainText("Double-click to configure")
        self.file_path: str = ""
        self.out_port.hide()
        
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["file_path"] = self.file_path
        return data

    def from_dict(self, data: dict) -> None:
        super().from_dict(data)
        self.file_path = data.get("file_path", "")
        if self.file_path:
            self.sub_item.setPlainText(self.file_path.split("/")[-1])
            self._code = f"html = df.describe(include='all').T.to_html(classes='table table-striped')\\nwith open(r'{self.file_path}', 'w', encoding='utf-8') as f:\\n    f.write(html)"
            
    def configure(self) -> None:
        path, _ = QFileDialog.getSaveFileName(None, "Save Report", str(get_exports_dir()), "HTML Files (*.html)")
        if path:
            self.file_path = path
            self.sub_item.setPlainText(path.split("/")[-1])
            
    def run_logic(self, input_dfs: list[pd.DataFrame]) -> None:
        if not input_dfs:
            raise ValueError("Save Report node requires an input.")
        if not self.file_path:
            raise ValueError("No save path selected for report.")
            
        self.output_df = input_dfs[0]
        
        # Simple report generation code
        code = [
            f"# Save Summary Report to {self.file_path}",
            "import pandas as pd",
            "if isinstance(df, pd.DataFrame):",
            "    desc = df.describe(include='all').T.to_html(classes='table table-striped')",
            "else:",
            "    desc = df.to_pandas().describe(include='all').T.to_html(classes='table table-striped')",
            "",
            "html_content = f\"\"\"",
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset='utf-8'>",
            "    <style>",
            "        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; }",
            "        table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; }",
            "        th, td { text-align: left; padding: 5px 10px; border-bottom: 1px solid #E2E8F0; }",
            "        th { background: #F1F5F9; font-weight: 600; color: #475569; border-bottom: 2px solid #CBD5E1; }",
            "        tr:nth-child(even) { background: #F8FAFC; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <h1>Dataset Summary Report</h1>",
            "    {desc}",
            "</body>",
            "</html>",
            "\"\"\"",
            f"with open(r'{self.file_path}', 'w', encoding='utf-8') as f:",
            "    f.write(html_content)"
        ]
        self._code = "\n".join(code)
