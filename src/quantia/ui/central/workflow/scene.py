"""Graphics scene for workflow builder."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QMenu

from quantia.ui.central.workflow.items import NodeItem, PortItem, EdgeItem


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

    def contextMenuEvent(self, event) -> None:
        """Context menu to spawn nodes."""
        from quantia.ui.central.workflow.nodes_logic import LoadCSVNode, CleanDataNode, ExportCSVNode
        
        menu = QMenu()
        
        action_import = menu.addAction("Add Load CSV Node")
        action_clean = menu.addAction("Add Clean Data Node")
        action_export = menu.addAction("Add Export CSV Node")
        
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
