"""Graphics view for workflow builder."""

from __future__ import annotations

import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QGraphicsView, QVBoxLayout, QWidget

from quantia.ui.central.workflow.scene import WorkflowScene


class WorkflowGraphicsView(QGraphicsView):
    """View managing pan, zoom, and background grid."""
    
    def __init__(self, scene: WorkflowScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Grid settings
        self.grid_size = 20
        self.grid_color = QColor("#E2E8F0")
        
        # Panning
        self._is_panning = False
        self._pan_start_pos = QPointF()

    def drawBackground(self, painter: QPainter, rect) -> None:
        """Draw a dot grid background."""
        super().drawBackground(painter, rect)
        
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % self.grid_size)
        first_top = top - (top % self.grid_size)

        painter.setPen(QPen(self.grid_color, 1))
        
        # Draw grid points
        for x in range(first_left, right, self.grid_size):
            for y in range(first_top, bottom, self.grid_size):
                painter.drawPoint(x, y)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in and out."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        
        # Save the scene pos
        old_pos = self.mapToScene(event.position().toPoint())
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)
        
        # Get the new position
        new_pos = self.mapToScene(event.position().toPoint())
        
        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Middle mouse to pan."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Update panning."""
        if self._is_panning:
            delta = event.position() - self._pan_start_pos
            self._pan_start_pos = event.position()
            
            # Map delta to scene coordinates
            # A simple translate is not enough, we need to scroll the bars
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            
            event.accept()
            return
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """End panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
            
        super().mouseReleaseEvent(event)


from quantia.ui.central.workflow.engine import WorkflowEngine
from PySide6.QtWidgets import QGraphicsView, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QMessageBox

class WorkflowTab(QWidget):
    """The main widget inserted into the central tabs."""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 10, 10, 10)
        
        self.btn_run = QPushButton("Run Workflow")
        self.btn_run.setToolTip("Execute the workflow and generate script")
        self.btn_run.clicked.connect(self._run_workflow)
        
        self.btn_clear = QPushButton("Clear Canvas")
        self.btn_clear.clicked.connect(self._clear_workflow)
        
        toolbar.addWidget(self.btn_run)
        toolbar.addWidget(self.btn_clear)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        self.scene = WorkflowScene(self)
        self.view = WorkflowGraphicsView(self.scene, self)
        
        layout.addWidget(self.view)

    def _run_workflow(self) -> None:
        engine = WorkflowEngine(self.scene)
        script = engine.run()
        
        if script.startswith("# Error"):
            QMessageBox.critical(self, "Workflow Error", script)
            return
            
        # Send the script to the main window's script editor
        main_win = self.window()
        print(f"DEBUG: main_win type: {type(main_win)}")
        if hasattr(main_win, "_script_editor"):
            editor = main_win._script_editor
            print(f"DEBUG: editor type: {type(editor)}")
            print(f"DEBUG: editor has append_code: {hasattr(editor, 'append_code')}")
            print(f"DEBUG: editor has append_text: {hasattr(editor, 'append_text')}")
            editor.append_code(script)
            QMessageBox.information(self, "Success", "Workflow executed successfully. Check the Script Editor tab.")
            
    def refresh_theme(self, theme: Any) -> None:
        """Update colors for the current theme."""
        from quantia.theme.palette import Theme, PALETTE
        p = PALETTE[theme]
        
        # Update grid colors on the view
        self.view.grid_color = QColor(p["border"])
        
        # Update scene background
        self.scene.setBackgroundBrush(QColor(p["surface_primary"]))
        
        # Force a redraw on the view
        self.view.viewport().update()

    def _clear_workflow(self) -> None:
        self.scene.clear()
        self.scene._drawing_edge = None
        self.scene._start_port = None
