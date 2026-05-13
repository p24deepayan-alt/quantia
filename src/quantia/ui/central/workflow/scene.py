"""Graphics scene for workflow builder."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QLineF
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QMenu

from quantia.ui.central.workflow.items import NodeItem, PortItem, EdgeItem
from quantia.ui.central.workflow.nodes_logic import BaseLogicNode


class WorkflowScene(QGraphicsScene):
    """Manages the nodes and connections."""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        
        self.grid_size = 20
        self.grid_squares = 5
        
        self._color_light = QColor("#f0f0f0")
        self._color_dark = QColor("#e0e0e0")
        
        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(1)

        self._drawing_edge: EdgeItem | None = None
        self._start_port: PortItem | None = None

    def drawBackground(self, painter: QPainter, rect) -> None:
        """Draw a subtle grid background."""
        super().drawBackground(painter, rect)
        
        # Calculate grid lines
        left = int(rect.left())
        right = int(rect.right())
        top = int(rect.top())
        bottom = int(rect.bottom())
        
        first_left = left - (left % self.grid_size)
        first_top = top - (top % self.grid_size)
        
        # Draw vertical lines
        lines_light = []
        lines_dark = []
        
        for x in range(first_left, right, self.grid_size):
            if x % (self.grid_size * self.grid_squares) == 0:
                lines_dark.append(QLineF(x, top, x, bottom))
            else:
                lines_light.append(QLineF(x, top, x, bottom))
                
        # Draw horizontal lines
        for y in range(first_top, bottom, self.grid_size):
            if y % (self.grid_size * self.grid_squares) == 0:
                lines_dark.append(QLineF(left, y, right, y))
            else:
                lines_light.append(QLineF(left, y, right, y))
                
        # Batch draw for performance
        painter.setPen(self._pen_light)
        painter.drawLines(lines_light)
        
        painter.setPen(self._pen_dark)
        painter.drawLines(lines_dark)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle starting to draw a wire from a port."""
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        
        if event.button() == Qt.MouseButton.LeftButton and isinstance(item, PortItem):
            if item.is_output:
                self._start_port = item
                self._drawing_edge = EdgeItem(self._start_port)
                self._drawing_edge.set_dest_pos(event.scenePos())
                self.addItem(self._drawing_edge)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Update floating wire."""
        if self._drawing_edge and self._start_port:
            self._drawing_edge.set_dest_pos(event.scenePos())
            event.accept()
            return
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Finish wire drawing."""
        if self._drawing_edge and self._start_port:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            
            # Snap to an input port
            if isinstance(item, PortItem) and not item.is_output and item.node != self._start_port.node:
                self._drawing_edge.dest_port = item
                self._drawing_edge.update_positions()
                
                # Register edge to both ports
                self._start_port.add_edge(self._drawing_edge)
                item.add_edge(self._drawing_edge)
            else:
                # Cancel drawing
                self.removeItem(self._drawing_edge)
                
            self._drawing_edge = None
            self._start_port = None
            event.accept()
            return
            
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._delete_selected()
            event.accept()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Context menu to spawn nodes."""
        from quantia.ui.central.workflow.nodes_logic import (
            LoadCSVNode, CleanDataNode, ExportCSVNode,
            PCANode, LinearRegressionNode, SaveReportNode,
            TTestNode, DescriptiveStatsNode, CorrelationNode,
            LogisticRegressionNode, ChiSquareNode,
            RandomForestNode, KMeansNode,
            HistogramNode, BoxPlotNode, ScatterPlotNode,
            GradientBoostingNode, DecisionTreeNode, SVMNode, KNNNode,
            LDANode, QDANode, NaiveBayesNode,
            HierarchicalNode, DBSCANNode, GMMNode,
            DecisionTreeRegressorNode, RandomForestRegressorNode,
            BarChartNode, HeatmapNode, LineChartNode, ViolinPlotNode, QQPlotNode
        )
        
        menu = QMenu()
        
        # Submenus
        menu_io = menu.addMenu("I/O")
        menu_proc = menu.addMenu("Processing")
        menu_stats = menu.addMenu("Statistics")
        menu_ml = menu.addMenu("Machine Learning")
        menu_plots = menu.addMenu("Visualization")
        menu_rep = menu.addMenu("Reporting")
        
        # Machine Learning Submenus
        menu_reg = menu_ml.addMenu("Regression")
        menu_clf = menu_ml.addMenu("Classification")
        menu_clu = menu_ml.addMenu("Clustering")
        menu_ml.addAction("PCA").triggered.connect(lambda: self.addItem(PCANode(event.scenePos().x(), event.scenePos().y())))
        
        # I/O
        action_import = menu_io.addAction("Load CSV")
        action_export = menu_io.addAction("Export CSV")
        
        # Processing
        action_clean = menu_proc.addAction("Clean Data")
        
        # Statistics
        action_desc = menu_stats.addAction("Descriptive Stats")
        action_ttest = menu_stats.addAction("T-Test")
        action_corr = menu_stats.addAction("Correlation")
        action_chi = menu_stats.addAction("Chi-Square")
        
        # ML - Regression
        action_lin_reg = menu_reg.addAction("Linear Regression")
        action_dt_reg = menu_reg.addAction("Decision Tree Regressor")
        action_rf_reg = menu_reg.addAction("Random Forest Regressor")
        
        # ML - Classification
        action_log_reg = menu_clf.addAction("Logistic Regression")
        action_rf_clf = menu_clf.addAction("Random Forest")
        action_gb_clf = menu_clf.addAction("Gradient Boosting")
        action_dt_clf = menu_clf.addAction("Decision Tree")
        action_svm_clf = menu_clf.addAction("SVM")
        action_knn_clf = menu_clf.addAction("KNN")
        action_lda_clf = menu_clf.addAction("LDA")
        action_qda_clf = menu_clf.addAction("QDA")
        action_nb_clf = menu_clf.addAction("Naive Bayes")
        
        # ML - Clustering
        action_kmeans = menu_clu.addAction("K-Means")
        action_h_clu = menu_clu.addAction("Hierarchical")
        action_dbscan = menu_clu.addAction("DBSCAN")
        action_gmm = menu_clu.addAction("GMM")
        
        # Plots
        action_hist = menu_plots.addAction("Histogram")
        action_box = menu_plots.addAction("Box Plot")
        action_scatter = menu_plots.addAction("Scatter Plot")
        action_bar = menu_plots.addAction("Bar Chart")
        action_heatmap = menu_plots.addAction("Heatmap")
        action_line = menu_plots.addAction("Line Chart")
        action_violin = menu_plots.addAction("Violin Plot")
        action_qq = menu_plots.addAction("Q-Q Plot")
        
        # Reporting
        action_report = menu_rep.addAction("Save Report")
        
        menu.addSeparator()
        action_delete = menu.addAction("Delete Selected Nodes")
        
        action = menu.exec(event.screenPos())
        
        if action == action_import:
            self.addItem(LoadCSVNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_clean:
            self.addItem(CleanDataNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_export:
            self.addItem(ExportCSVNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_desc:
            self.addItem(DescriptiveStatsNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_ttest:
            self.addItem(TTestNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_corr:
            self.addItem(CorrelationNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_chi:
            self.addItem(ChiSquareNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_lin_reg:
            self.addItem(LinearRegressionNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_dt_reg:
            self.addItem(DecisionTreeRegressorNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_rf_reg:
            self.addItem(RandomForestRegressorNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_log_reg:
            self.addItem(LogisticRegressionNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_rf_clf:
            self.addItem(RandomForestNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_gb_clf:
            self.addItem(GradientBoostingNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_dt_clf:
            self.addItem(DecisionTreeNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_svm_clf:
            self.addItem(SVMNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_knn_clf:
            self.addItem(KNNNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_lda_clf:
            self.addItem(LDANode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_qda_clf:
            self.addItem(QDANode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_nb_clf:
            self.addItem(NaiveBayesNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_kmeans:
            self.addItem(KMeansNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_h_clu:
            self.addItem(HierarchicalNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_dbscan:
            self.addItem(DBSCANNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_gmm:
            self.addItem(GMMNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_hist:
            self.addItem(HistogramNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_box:
            self.addItem(BoxPlotNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_scatter:
            self.addItem(ScatterPlotNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_bar:
            self.addItem(BarChartNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_heatmap:
            self.addItem(HeatmapNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_line:
            self.addItem(LineChartNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_violin:
            self.addItem(ViolinPlotNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_qq:
            self.addItem(QQPlotNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_report:
            self.addItem(SaveReportNode(event.scenePos().x(), event.scenePos().y()))
        elif action == action_delete:
            self._delete_selected()

    def _delete_selected(self) -> None:
        """Delete all selected items, including their edges."""
        for item in self.selectedItems():
            if isinstance(item, BaseLogicNode):
                # Ensure data is cleared before removal
                item.clear_data()
                
                # Remove connected edges
                for edge in item.in_port.edges[:]:
                    edge.source_port.remove_edge(edge)
                    self.removeItem(edge)
                for edge in item.out_port.edges[:]:
                    if edge.dest_port:
                        edge.dest_port.remove_edge(edge)
                    self.removeItem(edge)
                self.removeItem(item)
            elif isinstance(item, EdgeItem):
                if item.source_port:
                    item.source_port.remove_edge(item)
                if item.dest_port:
                    item.dest_port.remove_edge(item)
                self.removeItem(item)

    def clear_all_data(self) -> None:
        """Clear cached DataFrames from all nodes in the scene."""
        for item in self.items():
            if isinstance(item, BaseLogicNode):
                item.clear_data()

    def serialize(self) -> dict:
        """Serialize the scene to a dictionary."""
        nodes_data = []
        edges_data = []
        
        for item in self.items():
            if isinstance(item, BaseLogicNode):
                nodes_data.append(item.to_dict())
                
            elif isinstance(item, EdgeItem):
                src_node = item.source_port.node if item.source_port else None
                dst_node = item.dest_port.node if item.dest_port else None
                if src_node and dst_node:
                    edges_data.append({
                        "source_id": src_node.id,
                        "dest_id": dst_node.id,
                    })
                    
        return {
            "nodes": nodes_data,
            "edges": edges_data
        }

    def deserialize(self, data: dict) -> None:
        """Load a scene from a dictionary."""
        self.clear()
        self._drawing_edge = None
        self._start_port = None
        
        from quantia.ui.central.workflow.nodes_logic import (
            LoadCSVNode, CleanDataNode, ExportCSVNode, 
            PCANode, LinearRegressionNode, SaveReportNode,
            TTestNode, DescriptiveStatsNode, CorrelationNode,
            LogisticRegressionNode, ChiSquareNode,
            RandomForestNode, KMeansNode,
            HistogramNode, BoxPlotNode, ScatterPlotNode,
            GradientBoostingNode, DecisionTreeNode, SVMNode, KNNNode,
            LDANode, QDANode, NaiveBayesNode,
            HierarchicalNode, DBSCANNode, GMMNode,
            DecisionTreeRegressorNode, RandomForestRegressorNode,
            BarChartNode, HeatmapNode, LineChartNode, ViolinPlotNode, QQPlotNode
        )
        node_classes = {
            "LoadCSVNode": LoadCSVNode,
            "CleanDataNode": CleanDataNode,
            "ExportCSVNode": ExportCSVNode,
            "PCANode": PCANode,
            "LinearRegressionNode": LinearRegressionNode,
            "SaveReportNode": SaveReportNode,
            "TTestNode": TTestNode,
            "DescriptiveStatsNode": DescriptiveStatsNode,
            "CorrelationNode": CorrelationNode,
            "LogisticRegressionNode": LogisticRegressionNode,
            "ChiSquareNode": ChiSquareNode,
            "RandomForestNode": RandomForestNode,
            "KMeansNode": KMeansNode,
            "HistogramNode": HistogramNode,
            "BoxPlotNode": BoxPlotNode,
            "ScatterPlotNode": ScatterPlotNode,
            "GradientBoostingNode": GradientBoostingNode,
            "DecisionTreeNode": DecisionTreeNode,
            "SVMNode": SVMNode,
            "KNNNode": KNNNode,
            "LDANode": LDANode,
            "QDANode": QDANode,
            "NaiveBayesNode": NaiveBayesNode,
            "HierarchicalNode": HierarchicalNode,
            "DBSCANNode": DBSCANNode,
            "GMMNode": GMMNode,
            "DecisionTreeRegressorNode": DecisionTreeRegressorNode,
            "RandomForestRegressorNode": RandomForestRegressorNode,
            "BarChartNode": BarChartNode,
            "HeatmapNode": HeatmapNode,
            "LineChartNode": LineChartNode,
            "ViolinPlotNode": ViolinPlotNode,
            "QQPlotNode": QQPlotNode
        }
        
        id_to_node = {}
        for n_data in data.get("nodes", []):
            n_type = n_data.get("type")
            if n_type in node_classes:
                node = node_classes[n_type](n_data["x"], n_data["y"])
                node.id = n_data["id"]
                node.from_dict(n_data)
                self.addItem(node)
                id_to_node[node.id] = node
                
        for e_data in data.get("edges", []):
            src_id = e_data.get("source_id")
            dst_id = e_data.get("dest_id")
            if src_id in id_to_node and dst_id in id_to_node:
                src_node = id_to_node[src_id]
                dst_node = id_to_node[dst_id]
                
                edge = EdgeItem(src_node.out_port, dst_node.in_port)
                self.addItem(edge)
                src_node.out_port.add_edge(edge)
                dst_node.in_port.add_edge(edge)
                edge.update_positions()
