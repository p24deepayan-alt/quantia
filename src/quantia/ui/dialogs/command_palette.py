"""Command Palette — floating fuzzy search for application actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from quantia.ui.icons import feather_icon


class CommandPaletteDialog(QDialog):
    """Floating, frameless search dialog for running commands."""

    # Emitted when a command is selected
    command_triggered = Signal(str)  # command ID

    def __init__(self, commands: list[dict[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.all_commands = commands
        
        # Main container with shadow/rounded border via CSS
        self.container = QWidget()
        self.container.setObjectName("commandPalette")
        self.container.setStyleSheet("""
            QWidget#commandPalette {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QLineEdit {
                border: none;
                padding: 12px;
                font-size: 13pt;
                background: transparent;
                color: #1E293B;
            }
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px 8px;
                color: #475569;
            }
            QListWidget::item:selected {
                background-color: #F1F5F9;
                color: #6366F1;
                font-weight: 600;
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Search area
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 8, 12, 8)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(feather_icon("search", "#94A3B8", 20).pixmap(20, 20))
        search_layout.addWidget(icon_lbl)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command or variable...")
        self.search_input.textChanged.connect(self._filter_commands)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Divider
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #F1F5F9;")
        layout.addWidget(line)
        
        # Results list
        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(300)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        
        self.setFixedWidth(600)
        self._populate_list(self.all_commands)
        
        # Focus management
        self.search_input.installEventFilter(self)

    def _populate_list(self, items: list[dict[str, str]]) -> None:
        self.list_widget.clear()
        for item in items:
            list_item = QListWidgetItem(item["label"])
            list_item.setData(Qt.ItemDataRole.UserRole, item["id"])
            if "icon" in item:
                list_item.setIcon(feather_icon(item["icon"], "#64748B", 16))
            self.list_widget.addItem(list_item)
        
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter_commands(self, text: str) -> None:
        text = text.lower()
        filtered = [c for c in self.all_commands if text in c["label"].lower()]
        self._populate_list(filtered)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        cmd_id = item.data(Qt.ItemDataRole.UserRole)
        self.command_triggered.emit(cmd_id)
        self.accept()

    def eventFilter(self, obj, event):
        if obj == self.search_input and event.type() == Qt.EventType.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                self.list_widget.setCurrentRow((self.list_widget.currentRow() + 1) % self.list_widget.count())
                return True
            elif event.key() == Qt.Key.Key_Up:
                self.list_widget.setCurrentRow((self.list_widget.currentRow() - 1 + self.list_widget.count()) % self.list_widget.count())
                return True
            elif event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                if self.list_widget.currentItem():
                    self._on_item_clicked(self.list_widget.currentItem())
                return True
            elif event.key() == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(obj, event)
