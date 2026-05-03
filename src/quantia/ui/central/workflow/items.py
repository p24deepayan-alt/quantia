"""Graphics items for the workflow builder."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QPainterPath, QFont
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsRectItem
)


class PortItem(QGraphicsEllipseItem):
    """A port for connecting nodes."""
    
    def __init__(self, parent: NodeItem, is_output: bool = False) -> None:
        super().__init__(-6, -6, 12, 12, parent)
        self.node = parent
        self.is_output = is_output
        self.edges = []
        
        self.setBrush(QBrush(QColor("#3B82F6")))
        self.setPen(QPen(QColor("#1E3A8A"), 1.5))
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def hoverEnterEvent(self, event) -> None:
        self.setBrush(QBrush(QColor("#60A5FA")))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setBrush(QBrush(QColor("#3B82F6")))
        super().hoverLeaveEvent(event)

    def add_edge(self, edge: EdgeItem) -> None:
        self.edges.append(edge)

    def remove_edge(self, edge: EdgeItem) -> None:
        if edge in self.edges:
            self.edges.remove(edge)

    def get_global_pos(self) -> QPointF:
        """Get the center of the port in scene coordinates."""
        return self.scenePos()


class EdgeItem(QGraphicsPathItem):
    """A wire connecting two ports."""
    
    def __init__(self, source_port: PortItem, dest_port: PortItem | None = None) -> None:
        super().__init__()
        self.source_port = source_port
        self.dest_port = dest_port
        self.source_pos = source_port.get_global_pos()
        self.dest_pos = self.source_pos
        
        # Style
        self.setZValue(-1)  # Behind nodes
        self._pen = QPen(QColor("#94A3B8"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        self._selected_pen = QPen(QColor("#3B82F6"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        self.setPen(self._pen)
        
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def set_dest_pos(self, pos: QPointF) -> None:
        """Update the floating end position while drawing."""
        self.dest_pos = pos
        self.update_path()

    def update_positions(self) -> None:
        """Update both ends when a connected node moves."""
        if self.source_port:
            self.source_pos = self.source_port.get_global_pos()
        if self.dest_port:
            self.dest_pos = self.dest_port.get_global_pos()
        self.update_path()

    def update_path(self) -> None:
        path = QPainterPath(self.source_pos)
        
        # Smooth bezier curve
        dx = self.dest_pos.x() - self.source_pos.x()
        
        # Increase curve tangency based on distance
        control_dist = max(abs(dx) * 0.5, 40)
        
        ctrl1 = QPointF(self.source_pos.x() + control_dist, self.source_pos.y())
        ctrl2 = QPointF(self.dest_pos.x() - control_dist, self.dest_pos.y())
        
        path.cubicTo(ctrl1, ctrl2, self.dest_pos)
        self.setPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.setPen(self._selected_pen if value else self._pen)
        return super().itemChange(change, value)


class NodeItem(QGraphicsRectItem):
    """A visual block in the workflow."""
    
    def __init__(self, title: str, x: float = 0, y: float = 0) -> None:
        super().__init__(0, 0, 160, 60)
        self.setPos(x, y)
        self.title_text = title
        
        # Allow dragging and selection
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        # Visuals
        self.setBrush(QBrush(QColor("#FFFFFF")))
        self.setPen(QPen(QColor("#CBD5E1"), 2))
        
        # Title text
        self.title_item = QGraphicsTextItem(title, self)
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_item.setFont(font)
        self.title_item.setDefaultTextColor(QColor("#1E293B"))
        self.title_item.setPos(10, 5)

        # Body text (optional subtitle/type)
        self.sub_item = QGraphicsTextItem("Node operation", self)
        sub_font = QFont("Segoe UI", 8)
        self.sub_item.setFont(sub_font)
        self.sub_item.setDefaultTextColor(QColor("#64748B"))
        self.sub_item.setPos(10, 30)

        # Ports
        self.in_port = PortItem(self, is_output=False)
        self.in_port.setPos(0, 30)
        
        self.out_port = PortItem(self, is_output=True)
        self.out_port.setPos(160, 30)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Tell ports to update edges
            for edge in self.in_port.edges:
                edge.update_positions()
            for edge in self.out_port.edges:
                edge.update_positions()
                
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # Highlight border if selected
            if value:
                self.setPen(QPen(QColor("#3B82F6"), 2))
            else:
                self.setPen(QPen(QColor("#CBD5E1"), 2))
                
        return super().itemChange(change, value)
