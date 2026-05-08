"""Graphics scene for workflow builder."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QMenu

from quantia.ui.central.workflow.items import NodeItem, PortItem, EdgeItem
from quantia.ui.central.workflow.nodes_logic import BaseLogicNode


class WorkflowScene(QGraphicsScene):
    """Manages the nodes and connections."""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.setBackgroundBrush(Qt.GlobalColor.white)
        
        self._drawing_edge: EdgeItem | None = None
        self._start_port: PortItem | None = None

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
        from quantia.ui.central.workflow.nodes_logic import LoadCSVNode, CleanDataNode, ExportCSVNode
        
        menu = QMenu()
        
        action_import = menu.addAction("Add Load CSV Node")
        action_clean = menu.addAction("Add Clean Data Node")
        action_export = menu.addAction("Add Export CSV Node")
        action_delete = menu.addAction("Delete Selected Nodes")
        
        action = menu.exec(event.screenPos())
        
        if action == action_import:
            node = LoadCSVNode(event.scenePos().x(), event.scenePos().y())
            self.addItem(node)
        elif action == action_clean:
            node = CleanDataNode(event.scenePos().x(), event.scenePos().y())
            self.addItem(node)
        elif action == action_export:
            node = ExportCSVNode(event.scenePos().x(), event.scenePos().y())
            self.addItem(node)
        elif action == action_delete:
            self._delete_selected()

    def _delete_selected(self) -> None:
        """Delete all selected items, including their edges."""
        for item in self.selectedItems():
            if isinstance(item, BaseLogicNode):
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
            PCANode, LinearRegressionNode, SaveReportNode
        )
        node_classes = {
            "LoadCSVNode": LoadCSVNode,
            "CleanDataNode": CleanDataNode,
            "ExportCSVNode": ExportCSVNode,
            "PCANode": PCANode,
            "LinearRegressionNode": LinearRegressionNode,
            "SaveReportNode": SaveReportNode
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
