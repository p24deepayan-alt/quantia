"""Visual items for the Report Canvas (DTP Style)."""

from __future__ import annotations

import base64
from typing import Optional, TYPE_CHECKING, List, Any
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPixmap, QImage, QFont, QCursor
from PySide6.QtWidgets import (
    QGraphicsObject, QGraphicsItem, QStyleOptionGraphicsItem, QWidget,
    QGraphicsSceneMouseEvent, QGraphicsRectItem
)

if TYPE_CHECKING:
    from quantia.core.report.document import Block, BlockType


class PageItem(QGraphicsRectItem):
    """Represents a single physical page sheet."""
    def __init__(self, page_index: int, width: float, height: float, parent=None):
        super().__init__(0, 0, width, height, parent)
        self.page_index = page_index
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setPen(QPen(QColor("#B2BABB"), 1))
        self.setZValue(-100)


class ResizeHandle(QGraphicsRectItem):
    """Small handle for resizing a block."""
    def __init__(self, pos_name: str, parent: BaseBlockItem) -> None:
        super().__init__(-4, -4, 8, 8, parent)
        self.pos_name = pos_name
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setPen(QPen(QColor("#3498DB"), 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Set cursor based on position
        if pos_name in ("n", "s"): self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif pos_name in ("e", "w"): self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif pos_name in ("nw", "se"): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else: self.setCursor(Qt.CursorShape.SizeBDiagCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        parent = self.parentItem()
        if not isinstance(parent, BaseBlockItem): return
        
        delta = event.pos() - event.lastPos()
        rect = parent.boundingRect()
        
        if "e" in self.pos_name: rect.setRight(rect.right() + delta.x())
        if "w" in self.pos_name: rect.setLeft(rect.left() + delta.x())
        if "s" in self.pos_name: rect.setBottom(rect.bottom() + delta.y())
        if "n" in self.pos_name: rect.setTop(rect.top() + delta.y())
        
        # Ensure minimum size
        if rect.width() < 50: return
        if rect.height() < 30: return
        
        parent.set_geometry(rect)


class BaseBlockItem(QGraphicsObject):
    """Base class for all visual report blocks (Free Position)."""
    
    selected = Signal(object) # Emits self.block
    geometry_changed = Signal()

    def __init__(self, block: Block, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.block = block
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                     QGraphicsItem.GraphicsItemFlag.ItemIsFocusable |
                     QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                     QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self._rect = QRectF(0, 0, block.size.width, block.size.height)
        self.setPos(block.position.x, block.position.y)
        self.setZValue(block.z_order)
        self._hovered = False
        self._handles: List[ResizeHandle] = []
        self._setup_handles()

    def _setup_handles(self) -> None:
        for pos in ["nw", "n", "ne", "e", "se", "s", "sw", "w"]:
            h = ResizeHandle(pos, self)
            h.setVisible(False)
            self._handles.append(h)
        self._update_handle_positions()

    def _update_handle_positions(self) -> None:
        r = self._rect
        positions = {
            "nw": r.topLeft(), "n": QPointF(r.center().x(), r.top()), "ne": r.topRight(),
            "e": QPointF(r.right(), r.center().y()), "se": r.bottomRight(),
            "s": QPointF(r.center().x(), r.bottom()), "sw": r.bottomLeft(),
            "w": QPointF(r.left(), r.center().y())
        }
        for h in self._handles:
            h.setPos(positions[h.pos_name])

    def boundingRect(self) -> QRectF:
        # Include handle size in bounding rect to prevent artifacts
        return self._rect.adjusted(-5, -5, 5, 5)

    def set_geometry(self, rect: QRectF) -> None:
        self.prepareGeometryChange()
        # If we moved the top-left, we must adjust the item's scene position
        tl = rect.topLeft()
        if not tl.isNull():
            self.setPos(self.pos() + tl)
            rect.translate(-tl.x(), -tl.y())
            
        self._rect = rect
        self.block.size.width = rect.width()
        self.block.size.height = rect.height()
        self.block.position.x = self.x()
        self.block.position.y = self.y()
        self._update_handle_positions()
        self.geometry_changed.emit()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.block.position.x = value.x()
            self.block.position.y = value.y()
            self.geometry_changed.emit()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            for h in self._handles: h.setVisible(bool(value))
        elif change == QGraphicsItem.GraphicsItemChange.ItemZValueChange:
            self.block.z_order = value
        return super().itemChange(change, value)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        if self.isSelected() or self._hovered:
            pen = QPen(QColor("#3498DB"), 1)
            if self._hovered and not self.isSelected():
                pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self._rect)

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.selected.emit(self.block)
        super().mousePressEvent(event)


class PlotBlockItem(BaseBlockItem):
    """DTP-style Plot item."""
    def __init__(self, block: Block, parent: QGraphicsItem | None = None) -> None:
        super().__init__(block, parent)
        self._pixmap: Optional[QPixmap] = None

    def set_pixmap_from_b64(self, b64_data: str) -> None:
        if not b64_data:
            self._pixmap = None
            self.update()
            return
        img_data = base64.b64decode(b64_data)
        image = QImage.fromData(img_data)
        self._pixmap = QPixmap.fromImage(image)
        self.update()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        super().paint(painter, option, widget)
        r = self._rect
        if self._pixmap and not self._pixmap.isNull():
            painter.drawPixmap(r.toRect(), self._pixmap)
        else:
            painter.setBrush(QBrush(QColor("#F9F9F9")))
            painter.setPen(QPen(QColor("#DDDDDD"), 1))
            painter.drawRect(r)
            painter.setPen(QPen(QColor("#999999")))
            painter.drawText(r, Qt.AlignmentFlag.AlignCenter, f"Bound Plot\n(ID: {self.block.binding.target_id if self.block.binding else 'None'})")


class TextBlockItem(BaseBlockItem):
    """DTP-style Text item."""
    def __init__(self, block: Block, parent: QGraphicsItem | None = None) -> None:
        super().__init__(block, parent)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        super().paint(painter, option, widget)
        r = self._rect
        
        title = self.block.content.get("title", "")
        content = self.block.content.get("text", "")
        
        y = 10
        if title:
            title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
            painter.setFont(title_font)
            painter.setPen(QColor("#2C3E50"))
            painter.drawText(r.adjusted(10, y, -10, 0), Qt.TextFlag.TextSingleLine, title)
            y += 30
            
        content_font = QFont("Segoe UI", 10)
        painter.setFont(content_font)
        painter.setPen(QColor("#34495E"))
        painter.drawText(r.adjusted(10, y, -10, -10), Qt.TextFlag.TextWordWrap, content or "Double click to edit text...")


class TableBlockItem(BaseBlockItem):
    """DTP-style Table item."""
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        super().paint(painter, option, widget)
        r = self._rect
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(QColor("#DDDDDD"), 1))
        painter.drawRect(r)
        painter.setPen(QPen(QColor("#7F8C8D")))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(r.adjusted(10, 10, -10, -10), Qt.AlignmentFlag.AlignTop, f"Bound Table\nStyle: {self.block.content.get('table_style_id', 'Default')}")
