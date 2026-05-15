"""Report Canvas View and Scene (DTP Style)."""

from __future__ import annotations

from typing import List, Optional, Any
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem

from quantia.core.report.document import Document, Block, Page
from quantia.ui.central.report_canvas.items import BaseBlockItem, PageItem

class ReportCanvasScene(QGraphicsScene):
    """Scene managing free-positioned report blocks on discrete pages."""
    
    item_selected = Signal(object) 
    page_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._doc = Document()
        self._page_items: List[PageItem] = []
        self._block_items: List[BaseBlockItem] = []
        self._setup_scene()

    def set_document(self, doc: Document) -> None:
        self._doc = doc
        self._update_pages()

    def add_block_item(self, item: BaseBlockItem, page_index: int) -> None:
        self._block_items.append(item)
        
        # Parent the block to the correct page
        if 0 <= page_index < len(self._page_items):
            item.setParentItem(self._page_items[page_index])
        else:
            self.addItem(item)
            
        item.selected.connect(self.item_selected.emit)

    def remove_block_item(self, item: BaseBlockItem) -> None:
        if item in self._block_items:
            self._block_items.remove(item)
            if item.scene() == self:
                self.removeItem(item)

    def clear_blocks(self) -> None:
        for item in self._block_items:
            if item.scene() == self:
                self.removeItem(item)
        self._block_items.clear()

    def relayout(self) -> None:
        for item in self._block_items:
            item.update()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        # Fill workspace background
        painter.fillRect(rect, QColor("#E0E3E5")) # Slightly darker gray for DTP feel
        
        # Draw faint grid
        grid_size = 20
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        painter.setPen(QPen(QColor("#D5D8DC"), 0.5))
        for x in range(left, int(rect.right()), grid_size):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()), grid_size):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def _setup_scene(self) -> None:
        self._update_pages()

    def _update_pages(self) -> None:
        for p in getattr(self, "_shadow_items", []):
            if p.scene() == self: self.removeItem(p)
        self._shadow_items = []

        for p in self._page_items:
            if p.scene() == self:
                self.removeItem(p)
        self._page_items.clear()
            
        width = self._doc.page_size.width_pt
        height = self._doc.page_size.height_pt
            
        if self._doc.default_orientation == "landscape":
            width, height = height, width
            
        spacing = 50
        num_pages = len(self._doc.pages) if self._doc.pages else 1
        
        for i in range(num_pages):
            y_offset = i * (height + spacing)
            # Create a dropshadow effect for the page
            shadow = QGraphicsRectItem(5, y_offset + 5, width, height)
            shadow.setBrush(QBrush(QColor(0, 0, 0, 30)))
            shadow.setPen(Qt.PenStyle.NoPen)
            shadow.setZValue(-101)
            self.addItem(shadow)
            self._shadow_items.append(shadow)
            
            page_item = PageItem(i, width, height)
            page_item.setPos(0, y_offset)
            self.addItem(page_item)
            self._page_items.append(page_item)
            
        total_height = num_pages * (height + spacing)
        self.setSceneRect(QRectF(-200, -200, width + 400, total_height + 400))

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if isinstance(item, PageItem):
            self.page_selected.emit(item.page_index)


class ReportCanvasView(QGraphicsView):
    """Interactive view for the report canvas."""

    def __init__(self, scene: ReportCanvasScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) 
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self._zoom = 1.0
        self._zoom_step = 1.1

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0: self.zoom_in()
            else: self.zoom_out()
        else:
            super().wheelEvent(event)

    def zoom_in(self) -> None:
        self.scale(self._zoom_step, self._zoom_step)
        self._zoom *= self._zoom_step

    def zoom_out(self) -> None:
        self.scale(1 / self._zoom_step, 1 / self._zoom_step)
        self._zoom /= self._zoom_step

    def reset_zoom(self) -> None:
        self.resetTransform()
        self._zoom = 1.0
