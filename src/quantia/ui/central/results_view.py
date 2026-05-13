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
        
        self._registered_figures = {}

    def register_figure(self, b64_str: str, fig: Any) -> None:
        """Store the generated matplotlib figure against its base64 signature."""
        self._registered_figures[b64_str] = fig

    def add_result(self, title: str, content: str | pd.DataFrame) -> None:
        """Add a new result tab. Content can be text or a DataFrame."""
        if isinstance(content, pd.DataFrame):
            widget = self._create_table_view(content)
            icon_name = "grid"
        else:
            text_str = content
            if "plotly.js" in text_str or "include_plotlyjs" in text_str or "plotly-graph-div" in text_str:
                try:
                    from PySide6.QtWebEngineWidgets import QWebEngineView
                    widget = self._create_web_view(text_str)
                except ImportError:
                    widget = self._create_text_view(text_str)
            else:
                widget = self._create_text_view(text_str)
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
            if widget is None:
                continue
            
            raw = widget.property("raw_content")
            
            if isinstance(widget, QTextBrowser):
                bg = palette["bg_card"]
                widget.setStyleSheet(f"QTextBrowser {{ background-color: {bg}; padding: 20px; border: none; border-radius: 8px; }}")
                # Re-render with new theme
                self._update_text_browser_content(widget, str(raw), theme)
            elif isinstance(widget, QTableView):
                bg = palette["bg_secondary"]
                widget.setStyleSheet(f"QTableView {{ background-color: {bg}; border: none; }}")
            elif widget.metaObject().className() == "QWebEngineView":
                self._update_web_view_content(widget, str(raw), theme)

    def set_icon_color(self, color: str) -> None:
        """Update the icon colour for toolbar and existing tabs."""
        self._chrome_icon_color = color
        
        # Update existing tabs
        for i in range(self._tabs.count()):
            widget = self._tabs.widget(i)
            if widget is None:
                continue
            
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
        setattr(table, "_shift_scroll_filter", filter_obj)
        
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
        
        browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        browser.customContextMenuRequested.connect(lambda pos, b=browser: self._show_context_menu(b, pos))
        
        self._update_text_browser_content(browser, text, theme)
        return browser

    def _create_web_view(self, text: str) -> QWidget:
        """Creates a QWebEngineView for interactive HTML content like Plotly."""
        from PySide6.QtWebEngineWidgets import QWebEngineView
        view = QWebEngineView()
        
        from PySide6.QtWidgets import QApplication
        from quantia.app import QuantiaApp
        app = QApplication.instance()
        theme = app.get_current_theme() if isinstance(app, QuantiaApp) else Theme.LIGHT
        
        self._update_web_view_content(view, text, theme)
        return view

    def _show_context_menu(self, browser: QTextBrowser, pos) -> None:
        """Handle custom context menu to allow popping up interactive figures for images."""
        from quantia.ui.central.interactive_plot import InteractivePlotDialog
        
        cursor = browser.cursorForPosition(pos)
        fmt = cursor.charFormat()
        
        if fmt.isImageFormat():
            src = fmt.toImageFormat().name()
            if src.startswith("data:image/png;base64,"):
                b64_str = src.replace("data:image/png;base64,", "")
                if b64_str in self._registered_figures:
                    menu = browser.createStandardContextMenu()
                    menu.addSeparator()
                    action = menu.addAction(feather_icon("external-link", self._chrome_icon_color, 14), "Open Plot")
                    if menu.exec(browser.mapToGlobal(pos)) == action:
                        try:
                            fig = self._registered_figures[b64_str]
                            import pickle
                            fig_copy = pickle.loads(pickle.dumps(fig))
                            dialog = InteractivePlotDialog(fig_copy, self)
                            dialog.show()
                        except Exception:
                            pass
                    return
        
        # Default fallback
        menu = browser.createStandardContextMenu()
        menu.exec(browser.mapToGlobal(pos))

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

    def _update_web_view_content(self, view: Any, text: str, theme: Theme) -> None:
        p = PALETTE[theme]
        base_css = f"""
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; color: {p['text_primary']}; background-color: {p['bg_card']}; line-height: 1.5; padding: 20px; margin: 0; }}
                h2, h3 {{ color: {p['accent']}; margin-top: 0; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: {p['bg_secondary']}; border-radius: 6px; overflow: hidden; }}
                th {{ padding: 10px 12px; font-size: 9pt; font-weight: 700; color: {p['text_secondary']}; border-bottom: 2px solid {p['border']}; text-align: left; background: {p['bg_secondary']}; }}
                td {{ padding: 8px 12px; border-bottom: 1px solid {p['border']}; font-family: 'Fira Code', 'Consolas', monospace; font-size: 10pt; color: {p['text_primary']}; }}
                .simpletable th {{ background: {p['bg_secondary']}; }}
                .highlight {{ color: {p['accent']}; font-weight: 700; }}
            </style>
        """
        html = f"<!DOCTYPE html><html><head>{base_css}</head><body>{text}</body></html>"
        view.setHtml(html)

    def _close_tab(self, index: int) -> None:
        widget = self._tabs.widget(index)
        if widget:
            # Prune figure cache if this was a text browser with images
            if isinstance(widget, QTextBrowser):
                doc = widget.document()
                for b64 in list(self._registered_figures.keys()):
                    if b64 in doc.toHtml():
                        del self._registered_figures[b64]
            
            widget.deleteLater()
        self._tabs.removeTab(index)

    def clear_all(self) -> None:
        # Properly delete all tab widgets to free C++ memory
        for i in range(self._tabs.count()):
            widget = self._tabs.widget(i)
            if widget:
                widget.deleteLater()
        
        self._tabs.clear()
        self._registered_figures.clear()

    def get_all_html(self) -> str:
        """Collect HTML content from all result tabs for report generation."""
        sections = []
        for i in range(self._tabs.count()):
            title = self._tabs.tabText(i)
            widget = self._tabs.widget(i)
            if widget is None:
                continue
                
            if isinstance(widget, QTextBrowser):
                html = widget.toHtml()
            elif isinstance(widget, QTableView):
                model = widget.model()
                if hasattr(model, 'get_dataframe'):
                    html = model.get_dataframe().to_html(classes='table table-sm table-striped')
                else:
                    html = "<p><i>Table data not available for export.</i></p>"
            elif widget.metaObject().className() == "QWebEngineView":
                raw = widget.property("raw_content")
                if raw is not None:
                    html = str(raw)
                else:
                    html = "<p><i>Interactive Plotly figures are embedded here.</i></p>"
            else:
                html = "<p><i>Content type not supported for export.</i></p>"
            sections.append(f"<div class='result-section'>\n<h3>{title}</h3>\n{html}\n</div>")
        return "\n".join(sections)
