"""Report Maker Tab (Canvas-Based Redesign)."""

from __future__ import annotations

import json
from typing import Iterable, List, Optional, Any
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGridLayout, QGroupBox, QLineEdit,
    QMessageBox, QScrollArea, QStackedWidget, QTextEdit, 
    QSpinBox, QFileDialog, QToolBar, QListWidget, QDoubleSpinBox, QSplitter, QMainWindow
)

from quantia.core.report.document import Document, Block, BlockType, Page, Binding, BindingKind, Point, Size, PageSize
from quantia.core.report.generator import ReportGenerator
from quantia.persistence.report.serializer import ReportSerializer
from quantia.ui.central.report_canvas.canvas import ReportCanvasScene, ReportCanvasView
from quantia.ui.central.report_canvas.items import BaseBlockItem, PlotBlockItem, TextBlockItem, TableBlockItem
from quantia.ui.icons import feather_icon


class ReportStudioWindow(QMainWindow):
    """Standalone native window for Report Studio."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quantia Report Studio")
        self.resize(1200, 800)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        from quantia.utils.resources import resource_path
        from PySide6.QtGui import QIcon
        icon_path = resource_path("reference/logo/Quantia_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self.report_maker = ReportMakerWidget(self)
        self.setCentralWidget(self.report_maker)
        
    def set_dataframe(self, df: Any) -> None:
        self.report_maker.set_dataframe(df)

    def refresh_theme(self, theme) -> None:
        self.report_maker.refresh_theme(theme)
        from quantia.theme.palette import get_stylesheet
        self.setStyleSheet(get_stylesheet(theme))


class ReportMakerWidget(QWidget):
    """Interactive canvas-based report editor."""

    code_generated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        from quantia.theme.palette import PALETTE, Theme
        app = QApplication.instance()
        self._theme = app.get_current_theme() if isinstance(app, QuantiaApp) else Theme.LIGHT
        self._icon_color = PALETTE[self._theme]["text_primary"]

        self._doc = Document()
        self._doc.pages.append(Page(index=0)) # start with 1 page
        self._df: Any = None
        self._columns: List[str] = []
        self._current_block: Optional[Block] = None
        self._active_page: int = 0
        self._active_tool: str = "select"
        
        self._setup_canvas()
        self._build_ui()

    def _setup_canvas(self) -> None:
        self.scene = ReportCanvasScene(self)
        self.scene.item_selected.connect(self._on_block_selected)
        self.scene.page_selected.connect(self._on_page_selected)
        self.scene.set_document(self._doc)
        self.view = ReportCanvasView(self.scene)

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Top Toolbar ---
        toolbar = QToolBar("DTP Tools")
        toolbar.setIconSize(QSize(16, 16))
        
        # File operations
        act_save = toolbar.addAction(feather_icon("save", self._icon_color, 14), "Save")
        act_save.triggered.connect(self._save_report)
        act_load = toolbar.addAction(feather_icon("folder", self._icon_color, 14), "Load")
        act_load.triggered.connect(self._load_report)
        toolbar.addSeparator()
        
        # Tools
        tool_group = QActionGroup(self)
        
        self.act_tool_select = QAction(feather_icon("mouse-pointer", self._icon_color, 14), "Select Tool", self)
        self.act_tool_select.setCheckable(True)
        self.act_tool_select.setChecked(True)
        tool_group.addAction(self.act_tool_select)
        toolbar.addAction(self.act_tool_select)
        
        self.act_tool_hand = QAction(feather_icon("hand", self._icon_color, 14), "Hand Tool", self)
        self.act_tool_hand.setCheckable(True)
        tool_group.addAction(self.act_tool_hand)
        toolbar.addAction(self.act_tool_hand)
        
        toolbar.addSeparator()
        
        # Insert blocks
        act_add_text = toolbar.addAction(feather_icon("type", self._icon_color, 14), "Insert Text")
        act_add_text.triggered.connect(lambda: self._add_block(Block(type=BlockType.TEXT)))
        
        act_add_plot = toolbar.addAction(feather_icon("bar-chart-2", self._icon_color, 14), "Insert Plot")
        act_add_plot.triggered.connect(lambda: self._add_block(Block(type=BlockType.BOUND_PLOT, binding=Binding(target_kind=BindingKind.PLOT, target_id="plot_1"))))
        
        act_add_table = toolbar.addAction(feather_icon("grid", self._icon_color, 14), "Insert Table")
        act_add_table.triggered.connect(lambda: self._add_block(Block(type=BlockType.BOUND_TABLE, binding=Binding(target_kind=BindingKind.TABLE, target_id="table_1"))))
        
        toolbar.addSeparator()
        
        # Z-Order
        act_front = toolbar.addAction(feather_icon("chevrons-up", self._icon_color, 14), "Bring to Front")
        act_front.triggered.connect(lambda: self._change_z_order(10))
        act_forward = toolbar.addAction(feather_icon("chevron-up", self._icon_color, 14), "Bring Forward")
        act_forward.triggered.connect(lambda: self._change_z_order(1))
        act_backward = toolbar.addAction(feather_icon("chevron-down", self._icon_color, 14), "Send Backward")
        act_backward.triggered.connect(lambda: self._change_z_order(-1))
        act_back = toolbar.addAction(feather_icon("chevrons-down", self._icon_color, 14), "Send to Back")
        act_back.triggered.connect(lambda: self._change_z_order(-10))
        
        toolbar.addSeparator()
        act_del = toolbar.addAction(feather_icon("trash-2", "#D32F2F", 14), "Delete")
        act_del.triggered.connect(self._delete_selected)
        
        toolbar.addSeparator()
        
        act_preview = toolbar.addAction(feather_icon("eye", self._icon_color, 14), "Preview HTML")
        act_preview.triggered.connect(self._on_preview)
        act_export = toolbar.addAction(feather_icon("file-text", "#FFFFFF", 14), "Export PDF")
        act_export.triggered.connect(self._on_export)
        
        main_layout.addWidget(toolbar)

        # Tool behavior
        tool_group.triggered.connect(self._on_tool_changed)

        # --- Middle Area ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Pages Panel
        left_panel = QWidget()
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(5, 5, 5, 5)
        
        self.list_pages = QListWidget()
        self.list_pages.addItem("Page 1")
        self.list_pages.setCurrentRow(0)
        self.list_pages.currentRowChanged.connect(self._on_page_list_changed)
        left_lay.addWidget(QLabel("Pages"))
        left_lay.addWidget(self.list_pages)
        
        btn_add_page = QPushButton("Add Page")
        btn_add_page.clicked.connect(self._add_page)
        left_lay.addWidget(btn_add_page)
        
        btn_del_page = QPushButton("Delete Page")
        btn_del_page.clicked.connect(self._delete_page)
        left_lay.addWidget(btn_del_page)
        
        # Doc settings
        doc_grp = QGroupBox("Document")
        dlay = QGridLayout()
        doc_grp.setLayout(dlay)
        dlay.addWidget(QLabel("Title:"), 0, 0)
        self.txt_rep_title = QLineEdit(self._doc.title)
        self.txt_rep_title.textChanged.connect(self._on_doc_changed)
        dlay.addWidget(self.txt_rep_title, 0, 1)

        dlay.addWidget(QLabel("Size:"), 1, 0)
        self.cmb_page_size = QComboBox()
        self.cmb_page_size.addItems(["A4", "Letter"])
        self.cmb_page_size.currentTextChanged.connect(self._on_doc_changed)
        dlay.addWidget(self.cmb_page_size, 1, 1)
        
        dlay.addWidget(QLabel("Orient:"), 2, 0)
        self.cmb_orient = QComboBox()
        self.cmb_orient.addItems(["portrait", "landscape"])
        self.cmb_orient.currentTextChanged.connect(self._on_doc_changed)
        dlay.addWidget(self.cmb_orient, 2, 1)
        left_lay.addWidget(doc_grp)
        
        splitter.addWidget(left_panel)
        
        # Center: Canvas
        center_panel = QWidget()
        center_lay = QVBoxLayout(center_panel)
        center_lay.setContentsMargins(0,0,0,0)
        center_lay.addWidget(self.view)
        splitter.addWidget(center_panel)
        
        # Right: Properties Panel
        right_panel = QWidget()
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(5,5,5,5)
        
        # Geometry
        geom_grp = QGroupBox("Geometry")
        glay = QGridLayout(geom_grp)
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-5000, 5000)
        self.spin_x.valueChanged.connect(self._on_geom_changed)
        glay.addWidget(QLabel("X:"), 0, 0)
        glay.addWidget(self.spin_x, 0, 1)
        
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-5000, 5000)
        self.spin_y.valueChanged.connect(self._on_geom_changed)
        glay.addWidget(QLabel("Y:"), 0, 2)
        glay.addWidget(self.spin_y, 0, 3)
        
        self.spin_w = QDoubleSpinBox()
        self.spin_w.setRange(10, 5000)
        self.spin_w.valueChanged.connect(self._on_geom_changed)
        glay.addWidget(QLabel("W:"), 1, 0)
        glay.addWidget(self.spin_w, 1, 1)
        
        self.spin_h = QDoubleSpinBox()
        self.spin_h.setRange(10, 5000)
        self.spin_h.valueChanged.connect(self._on_geom_changed)
        glay.addWidget(QLabel("H:"), 1, 2)
        glay.addWidget(self.spin_h, 1, 3)
        right_lay.addWidget(geom_grp)
        
        # Specific Properties
        self.prop_panel = QStackedWidget()
        
        # 0: Text
        self.text_editor = QWidget()
        tlay = QVBoxLayout(self.text_editor)
        tlay.setContentsMargins(0,0,0,0)
        tlay.addWidget(QLabel("Title:"))
        self.txt_block_title = QLineEdit()
        self.txt_block_title.textChanged.connect(self._update_current_block)
        tlay.addWidget(self.txt_block_title)
        
        font_lay = QHBoxLayout()
        self.cmb_font = QComboBox()
        self.cmb_font.addItems(["Segoe UI", "Arial", "Georgia", "Times New Roman", "Courier New"])
        self.cmb_font.currentTextChanged.connect(self._update_current_block)
        font_lay.addWidget(self.cmb_font)
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(6, 72)
        self.spin_font_size.setValue(10)
        self.spin_font_size.valueChanged.connect(self._update_current_block)
        font_lay.addWidget(self.spin_font_size)
        tlay.addLayout(font_lay)
        
        align_lay = QHBoxLayout()
        self.cmb_align = QComboBox()
        self.cmb_align.addItems(["Left", "Center", "Right"])
        self.cmb_align.currentTextChanged.connect(self._update_current_block)
        align_lay.addWidget(self.cmb_align)
        tlay.addLayout(align_lay)
        
        tlay.addWidget(QLabel("Content:"))
        self.txt_content = QTextEdit()
        self.txt_content.textChanged.connect(self._update_current_block)
        tlay.addWidget(self.txt_content)
        self.prop_panel.addWidget(self.text_editor)
        
        # 1: Plot
        self.plot_editor = QWidget()
        play = QGridLayout(self.plot_editor)
        play.setContentsMargins(0,0,0,0)
        play.addWidget(QLabel("Title:"), 0, 0)
        self.txt_plot_title = QLineEdit()
        self.txt_plot_title.textChanged.connect(self._update_current_block)
        play.addWidget(self.txt_plot_title, 0, 1)
        
        play.addWidget(QLabel("Plot Type:"), 1, 0)
        self.cmb_plot_type = QComboBox()
        self.cmb_plot_type.addItems(["Scatter", "Bar", "Line", "Histogram", "Box Plot", "Violin"])
        self.cmb_plot_type.currentTextChanged.connect(self._update_current_block)
        play.addWidget(self.cmb_plot_type, 1, 1)
        
        play.addWidget(QLabel("X Variable:"), 2, 0)
        self.cmb_x = QComboBox()
        self.cmb_x.currentTextChanged.connect(self._update_current_block)
        play.addWidget(self.cmb_x, 2, 1)
        
        play.addWidget(QLabel("Y Variable:"), 3, 0)
        self.cmb_y = QComboBox()
        self.cmb_y.currentTextChanged.connect(self._update_current_block)
        play.addWidget(self.cmb_y, 3, 1)
        
        play.addWidget(QLabel("Color By:"), 4, 0)
        self.cmb_hue = QComboBox()
        self.cmb_hue.currentTextChanged.connect(self._update_current_block)
        play.addWidget(self.cmb_hue, 4, 1)
        play.setRowStretch(5, 1)
        self.prop_panel.addWidget(self.plot_editor)
        
        # 2: Table
        self.table_editor = QWidget()
        tblay = QVBoxLayout(self.table_editor)
        tblay.setContentsMargins(0,0,0,0)
        tblay.addWidget(QLabel("Title:"))
        self.txt_table_title = QLineEdit()
        self.txt_table_title.textChanged.connect(self._update_current_block)
        tblay.addWidget(self.txt_table_title)
        tblay.addWidget(QLabel("Rows Limit:"))
        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(1, 1000)
        self.spin_limit.setValue(20)
        self.spin_limit.valueChanged.connect(self._update_current_block)
        tblay.addWidget(self.spin_limit)
        tblay.addStretch()
        self.prop_panel.addWidget(self.table_editor)
        
        # 3: Empty
        self.prop_panel.addWidget(QLabel("Select an object to edit properties."))
        
        right_lay.addWidget(self.prop_panel)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([150, 600, 250])
        main_layout.addWidget(splitter)
        
        self.prop_panel.setCurrentIndex(3)
        self._enable_geom(False)

    def _enable_geom(self, enable: bool) -> None:
        self.spin_x.setEnabled(enable)
        self.spin_y.setEnabled(enable)
        self.spin_w.setEnabled(enable)
        self.spin_h.setEnabled(enable)

    def _on_tool_changed(self, action: QAction) -> None:
        if action == self.act_tool_select:
            from PySide6.QtWidgets import QGraphicsView
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._active_tool = "select"
        elif action == self.act_tool_hand:
            from PySide6.QtWidgets import QGraphicsView
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self._active_tool = "hand"

    def set_dataframe(self, df: Any) -> None:
        self._df = df
        if hasattr(df, "columns"):
            self.update_columns(df.columns)

    def update_columns(self, columns: Iterable[str]) -> None:
        self._columns = list(columns)
        for cb in (self.cmb_x, self.cmb_y, self.cmb_hue):
            cb.blockSignals(True)
            cb.clear()
            cb.addItem("-- None --")
            cb.addItems(self._columns)
            cb.blockSignals(False)

    def refresh_theme(self, theme) -> None:
        from quantia.theme.palette import PALETTE
        self._icon_color = PALETTE[theme]["text_primary"]

    def _add_page(self) -> None:
        idx = len(self._doc.pages)
        self._doc.pages.append(Page(index=idx))
        self.list_pages.addItem(f"Page {idx + 1}")
        self.scene.set_document(self._doc)
        self._rebuild_scene_items()

    def _delete_page(self) -> None:
        if len(self._doc.pages) <= 1: return
        idx = self.list_pages.currentRow()
        if idx < 0: return
        
        # Remove page and blocks on this page
        self._doc.pages.pop(idx)
            
        # Re-index remaining pages
        for i, p in enumerate(self._doc.pages):
            p.index = i
                
        self.list_pages.takeItem(idx)
        
        # Rename list items
        for i in range(self.list_pages.count()):
            self.list_pages.item(i).setText(f"Page {i + 1}")
            
        self.scene.set_document(self._doc)
        self._rebuild_scene_items()

    def _on_page_list_changed(self, current_row: int) -> None:
        if current_row >= 0:
            self._active_page = current_row

    def _on_page_selected(self, page_idx: int) -> None:
        self.list_pages.setCurrentRow(page_idx)

    def _on_doc_changed(self) -> None:
        self._doc.title = self.txt_rep_title.text()
        size_name = self.cmb_page_size.currentText()
        if size_name == "A4":
            self._doc.page_size = PageSize("A4", 595.0, 842.0)
        else:
            self._doc.page_size = PageSize("Letter", 612.0, 792.0)
            
        self._doc.default_orientation = self.cmb_orient.currentText()
        self.scene.set_document(self._doc)
        self._rebuild_scene_items()

    def _add_block(self, block: Block) -> None:
        # Default positioning center of active page
        if 0 <= self._active_page < len(self.scene._page_items):
            pitem = self.scene._page_items[self._active_page]
            r = pitem.rect()
            block.position = Point(r.width() / 2 - block.size.width / 2, r.height() / 2 - block.size.height / 2)
            
        # Add to the current page in the domain model
        if 0 <= self._active_page < len(self._doc.pages):
            self._doc.pages[self._active_page].blocks.append(block)
            
        item = self._create_block_item(block)
        self.scene.add_block_item(item, self._active_page)
        item.setSelected(True)

    def _create_block_item(self, block: Block) -> BaseBlockItem:
        if block.type == BlockType.BOUND_PLOT:
            item = PlotBlockItem(block)
            if self._df is not None:
                self._render_block_preview(item)
        elif block.type == BlockType.TEXT:
            item = TextBlockItem(block)
        else:
            item = TableBlockItem(block)
            
        # Hook geometry changes
        item.geometry_changed.connect(self._sync_geom_to_ui)
        return item

    def _render_block_preview(self, item: PlotBlockItem) -> None:
        if self._df is None: return
        gen = ReportGenerator(self._doc, self._df)
        b64 = gen.render_block_plot(item.block)
        item.set_pixmap_from_b64(b64)

    def _on_block_selected(self, block: Block) -> None:
        self._current_block = block
        self._block_signals_blocked = True
        
        self._enable_geom(True)
        self._sync_geom_to_ui()
        
        if block.type == BlockType.TEXT:
            self.prop_panel.setCurrentIndex(0)
            self.txt_block_title.setText(block.content.get("title", ""))
            self.txt_content.setPlainText(block.content.get("text", ""))
            self.cmb_font.setCurrentText(block.content.get("font_family", "Segoe UI"))
            self.spin_font_size.setValue(block.content.get("font_size", 10))
            self.cmb_align.setCurrentText(block.content.get("alignment", "Left"))
        elif block.type == BlockType.BOUND_PLOT:
            self.prop_panel.setCurrentIndex(1)
            self.txt_plot_title.setText(block.content.get("title", ""))
            self.cmb_plot_type.setCurrentText(block.content.get("plot_type", "Scatter"))
            self.cmb_x.setCurrentText(block.content.get("x_var") or "-- None --")
            self.cmb_y.setCurrentText(block.content.get("y_var") or "-- None --")
            self.cmb_hue.setCurrentText(block.content.get("hue") or "-- None --")
        elif block.type == BlockType.BOUND_TABLE:
            self.prop_panel.setCurrentIndex(2)
            self.txt_table_title.setText(block.content.get("title", ""))
            self.spin_limit.setValue(block.content.get("rows_limit", 20))
        else:
            self.prop_panel.setCurrentIndex(3)
        self._block_signals_blocked = False

    def _sync_geom_to_ui(self) -> None:
        if not self._current_block: return
        if getattr(self, "_block_signals_blocked", False): return
        
        self._geom_signals_blocked = True
        self.spin_x.setValue(self._current_block.position.x)
        self.spin_y.setValue(self._current_block.position.y)
        self.spin_w.setValue(self._current_block.size.width)
        self.spin_h.setValue(self._current_block.size.height)
        self._geom_signals_blocked = False

    def _on_geom_changed(self) -> None:
        if getattr(self, "_geom_signals_blocked", False) or not self._current_block:
            return
            
        self._current_block.position.x = self.spin_x.value()
        self._current_block.position.y = self.spin_y.value()
        self._current_block.size.width = self.spin_w.value()
        self._current_block.size.height = self.spin_h.value()
        
        # update visual item
        for item in self.scene.selectedItems():
            if isinstance(item, BaseBlockItem) and item.block == self._current_block:
                item.setPos(self._current_block.position.x, self._current_block.position.y)
                item._rect.setWidth(self._current_block.size.width)
                item._rect.setHeight(self._current_block.size.height)
                item._update_handle_positions()
                if isinstance(item, PlotBlockItem):
                    self._render_block_preview(item)
                item.update()

    def _update_current_block(self) -> None:
        if getattr(self, "_block_signals_blocked", False) or not self._current_block:
            return
            
        block = self._current_block
        needs_render = False
        
        if block.type == BlockType.TEXT:
            block.content["title"] = self.txt_block_title.text()
            block.content["text"] = self.txt_content.toPlainText()
            block.content["font_family"] = self.cmb_font.currentText()
            block.content["font_size"] = self.spin_font_size.value()
            block.content["alignment"] = self.cmb_align.currentText()
        elif block.type == BlockType.BOUND_PLOT:
            block.content["title"] = self.txt_plot_title.text()
            block.content["plot_type"] = self.cmb_plot_type.currentText()
            x = self.cmb_x.currentText()
            y = self.cmb_y.currentText()
            hue = self.cmb_hue.currentText()
            block.content["x_var"] = None if x == "-- None --" else x
            block.content["y_var"] = None if y == "-- None --" else y
            block.content["hue"] = None if hue == "-- None --" else hue
            needs_render = True
        elif block.type == BlockType.BOUND_TABLE:
            block.content["title"] = self.txt_table_title.text()
            block.content["rows_limit"] = self.spin_limit.value()

        # Update visual item
        for item in self.scene.selectedItems():
            if isinstance(item, BaseBlockItem) and item.block == block:
                if needs_render and isinstance(item, PlotBlockItem):
                    self._render_block_preview(item)
                item.update()
                break

    def _change_z_order(self, delta: int) -> None:
        for item in self.scene.selectedItems():
            if isinstance(item, BaseBlockItem):
                item.setZValue(item.zValue() + delta)

    def _delete_selected(self) -> None:
        for item in self.scene.selectedItems():
            if isinstance(item, BaseBlockItem):
                for p in self._doc.pages:
                    if item.block in p.blocks:
                        p.blocks.remove(item.block)
                self.scene.remove_block_item(item)
        self.prop_panel.setCurrentIndex(3)
        self._enable_geom(False)

    def _save_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Report Studio Document", "", "Quantia Report (*.json)")
        if path:
            with open(path, "w") as f:
                f.write(ReportSerializer.to_json(self._doc))

    def _load_report(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Report Studio Document", "", "Quantia Report (*.json)")
        if path:
            try:
                with open(path, "r") as f:
                    self._doc = ReportSerializer.from_json(f.read())
                
                # Refresh UI
                self.txt_rep_title.setText(self._doc.title)
                self.cmb_page_size.setCurrentText(self._doc.page_size.name)
                self.cmb_orient.setCurrentText(self._doc.default_orientation)
                
                self.list_pages.clear()
                for i in range(len(self._doc.pages)):
                    self.list_pages.addItem(f"Page {i + 1}")
                    
                self.scene.set_document(self._doc)
                self._rebuild_scene_items()
                
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load report: {e}")

    def _rebuild_scene_items(self) -> None:
        self.scene.clear_blocks()
        for i, page in enumerate(self._doc.pages):
            for b in page.blocks:
                item = self._create_block_item(b)
                self.scene.add_block_item(item, i)

    def _on_preview(self) -> None:
        code = self.generate_code(preview=True)
        self.code_generated.emit(code)

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export to PDF", "", "PDF Files (*.pdf)")
        if path:
            code = self.generate_code(preview=False, pdf_path=path)
            self.code_generated.emit(code)

    def generate_code(self, preview: bool = True, pdf_path: Optional[str] = None) -> str:
        """Generate Python code to render the report."""
        config_json = ReportSerializer.to_json(self._doc).replace("'", "\\'")
        
        code = [
            f"# Generate Report Studio Document: {self._doc.title}",
            "from quantia.persistence.report.serializer import ReportSerializer",
            "from quantia.core.report.generator import ReportGenerator",
            "",
            f"config_json = '''{config_json}'''",
            "doc = ReportSerializer.from_json(config_json)",
            "gen = ReportGenerator(doc, df)",
            "html = gen.generate_html()",
            ""
        ]
        
        if preview:
            code.append("if 'display_html' in globals():")
            code.append("    display_html(html)")
            code.append("elif 'show_result' in globals():")
            code.append(f"    show_result('{self._doc.title}', html)")
        else:
            code.append("try:")
            code.append("    from weasyprint import HTML")
            code.append(f"    HTML(string=html).write_pdf(r'{pdf_path}')")
            code.append(f"    print(f'Report exported to: {pdf_path}')")
            code.append("except Exception as e:")
            code.append(f"    print(f'Error exporting PDF: {{e}}')")
            
        return "\n".join(code)
