"""Results View widget.

Provides a tabbed interface for viewing outputs of statistical tests,
supporting both rich text strings and pandas DataFrames.
"""

from __future__ import annotations

import pandas as pd
from typing import Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QTableView,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from quantia.core.data_model import PandasTableModel
from quantia.theme.palette import PALETTE, Theme
from quantia.ui.central.data_view import ShiftScrollFilter
from quantia.ui.icons import feather_icon


class ResultsViewWidget(QWidget):
    """Container for analysis results. Each result opens in a new tab."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("resultsView")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar above tabs
        toolbar = QWidget()
        h_layout = QHBoxLayout(toolbar)
        h_layout.setContentsMargins(8, 4, 8, 4)
        
        self._btn_clear = QPushButton("Clear All Results")
        self._btn_clear.setIcon(feather_icon("trash-2", "#D32F2F", 14))
        self._btn_clear.clicked.connect(self.clear_all)
        h_layout.addStretch()
        h_layout.addWidget(self._btn_clear)
        layout.addWidget(toolbar)
        
        self._chrome_icon_color = "#2D3E50"

        # Tabs container
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        layout.addWidget(self._tabs)

    def add_result(self, title: str, content: str | pd.DataFrame) -> None:
        """Add a new result tab. Content can be text or a DataFrame."""
        if isinstance(content, pd.DataFrame):
            widget = self._create_table_view(content)
            icon_name = "grid"
        else:
            widget = self._create_text_view(str(content))
            icon_name = "file-text"

        # Store the original content for theme refreshing
        widget.setProperty("raw_content", content)

        idx = self._tabs.addTab(widget, feather_icon(icon_name, self._chrome_icon_color, 14), title)
        self._tabs.setCurrentIndex(idx)

    def refresh_theme(self) -> None:
        """Update the icon colour for toolbar and existing tabs."""
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        from quantia.theme.palette import PALETTE, Theme
        
        app = QApplication.instance()
        if not isinstance(app, QuantiaApp): return
        
        theme = app.get_current_theme()
        palette = PALETTE[theme]
        color = palette["text_primary"]
        
        self.set_icon_color(color)
        
        # Update existing tabs content and background
        for i in range(self._tabs.count()):
            widget = self._tabs.widget(i)
            raw = widget.property("raw_content")
            
            if isinstance(widget, QTextBrowser):
                bg = palette["bg_card"]
                widget.setStyleSheet(f"QTextBrowser {{ background-color: {bg}; padding: 20px; border: none; border-radius: 8px; }}")
                # Re-render with new theme
                self._update_text_browser_content(widget, str(raw), theme)
            elif isinstance(widget, QTableView):
                bg = palette["bg_secondary"]
                widget.setStyleSheet(f"QTableView {{ background-color: {bg}; border: none; }}")

    def set_icon_color(self, color: str) -> None:
        """Update the icon colour for toolbar and existing tabs."""
        self._chrome_icon_color = color
        
        # Update existing tabs
        for i in range(self._tabs.count()):
            widget = self._tabs.widget(i)
            if isinstance(widget, QTableView):
                icon_name = "grid"
            else:
                icon_name = "file-text"
            self._tabs.setTabIcon(i, feather_icon(icon_name, color, 14))

    def _create_table_view(self, df: pd.DataFrame) -> QTableView:
        """Creates a readonly table view for a DataFrame."""
        table = QTableView()
        model = PandasTableModel()
        model.set_dataframe(df)
        table.setModel(model)
        
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.horizontalHeader().setStretchLastSection(True)

        filter_obj = ShiftScrollFilter(table)
        table.viewport().installEventFilter(filter_obj)
        table._shift_scroll_filter = filter_obj
        
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        app = QApplication.instance()
        theme = app.get_current_theme() if isinstance(app, QuantiaApp) else Theme.LIGHT
        bg = PALETTE[theme]["bg_secondary"]
        table.setStyleSheet(f"QTableView {{ background-color: {bg}; border: none; }}")
        return table

    def _create_text_view(self, text: str) -> QTextBrowser:
        """Creates a readonly text view for strings (like summaries)."""
        browser = QTextBrowser()
        
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        app = QApplication.instance()
        theme = app.get_current_theme() if isinstance(app, QuantiaApp) else Theme.LIGHT
        bg = PALETTE[theme]["bg_card"]
        
        browser.setStyleSheet(f"QTextBrowser {{ background-color: {bg}; padding: 20px; border: none; border-radius: 8px; }}")
        self._update_text_browser_content(browser, text, theme)
        return browser

    def _update_text_browser_content(self, browser: QTextBrowser, text: str, theme: Theme) -> None:
        """Render content into the browser with theme-aware CSS."""
        p = PALETTE[theme]
        
        if "<table" in text.lower() or "<html" in text.lower() or "<div" in text.lower():
            # Premium Card Styling
            base_css = f"""<style>
                body {{ font-family: 'Segoe UI', sans-serif; color: {p['text_primary']}; background: transparent; line-height: 1.5; }}
                h2, h3 {{ color: {p['accent']}; margin-top: 0; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: {p['bg_secondary']}; border-radius: 6px; overflow: hidden; }}
                th {{ padding: 10px 12px; font-size: 9pt; font-weight: 700; color: {p['text_secondary']}; border-bottom: 2px solid {p['border']}; text-align: left; background: {p['bg_secondary']}; }}
                td {{ padding: 8px 12px; border-bottom: 1px solid {p['border']}; font-family: 'Fira Code', 'Consolas', monospace; font-size: 10pt; color: {p['text_primary']}; }}
                .simpletable th {{ background: {p['bg_secondary']}; }}
                .highlight {{ color: {p['accent']}; font-weight: 700; }}
            </style>"""
            browser.setHtml(base_css + text)
        else:
            font = QFont("Fira Code", 10)
            if font.family() != "Fira Code": font = QFont("Consolas", 10)
            browser.setFont(font)
            browser.setPlainText(text)

    def _close_tab(self, index: int) -> None:
        self._tabs.removeTab(index)

    def clear_all(self) -> None:
        self._tabs.clear()

    def get_all_html(self) -> str:
        """Collect HTML content from all result tabs for report generation."""
        sections = []
        for i in range(self._tabs.count()):
            title = self._tabs.tabText(i)
            widget = self._tabs.widget(i)
            if isinstance(widget, QTextBrowser):
                html = widget.toHtml()
            elif isinstance(widget, QTableView):
                model = widget.model()
                if hasattr(model, 'get_dataframe'):
                    html = model.get_dataframe().to_html(classes='table table-sm table-striped')
                else:
                    html = "<p><i>Table data not available for export.</i></p>"
            else:
                html = "<p><i>Content type not supported for export.</i></p>"
            sections.append(f"<div class='result-section'>\n<h3>{title}</h3>\n{html}\n</div>")
        return "\n".join(sections)
