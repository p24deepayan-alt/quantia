"""Script Editor — VBA Editor-inspired Python code editor.

Central tab widget providing a full code editing experience:
- Line number gutter (like VBA's left margin)
- Python syntax highlighting (keywords, strings, comments, numbers)
- Run selection (Ctrl+Enter), Run all (F5)
- Fira Code / Cascadia Code / Consolas font
- Auto-generated code from GUI actions appears here
"""

from __future__ import annotations

import re
from typing import Any

from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
    QKeySequence,
    QShortcut,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFileDialog,
)

from quantia.ui.icons import feather_icon
from quantia.utils.paths import get_scripts_dir


# ─── Python Syntax Highlighting ──────────────────────────────────────────────


_KEYWORDS = [
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
]

_BUILTINS = [
    "print", "len", "range", "int", "float", "str", "list", "dict",
    "set", "tuple", "type", "isinstance", "enumerate", "zip", "map",
    "filter", "sorted", "reversed", "sum", "min", "max", "abs", "round",
    "open", "input", "super", "property", "staticmethod", "classmethod",
]


def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    if italic:
        f.setFontItalic(True)
    return f


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code."""

    def __init__(self, document: QTextDocument, dark: bool = False) -> None:
        super().__init__(document)
        self._dark = dark
        self._rules: list[tuple[re.Pattern, QTextCharFormat]] = []
        self._build_rules()

    def set_dark_mode(self, dark: bool) -> None:
        """Update colors for dark or light mode and re-highlight."""
        self._dark = dark
        self._rules = []  # Clear old rules
        self._build_rules()
        self.rehighlight()

    def _build_rules(self) -> None:
        if self._dark:
            kw_color = "#C792EA"       # purple — keywords
            builtin_color = "#82AAFF"  # blue — builtins
            string_color = "#C3E88D"   # green — strings
            comment_color = "#6B7280"  # grey — comments
            number_color = "#F78C6C"   # orange — numbers
            decorator_color = "#FFCB6B"  # yellow — decorators
            self_color = "#FF5370"     # red — self
            func_color = "#82AAFF"     # blue — function defs
        else:
            kw_color = "#7B1FA2"       # purple
            builtin_color = "#1565C0"  # blue
            string_color = "#2E7D32"   # green
            comment_color = "#6B7280"  # grey
            number_color = "#E65100"   # orange
            decorator_color = "#F57F17" # yellow-orange
            self_color = "#C62828"     # red
            func_color = "#1565C0"     # blue

        # Keywords
        kw_pattern = r"\b(" + "|".join(_KEYWORDS) + r")\b"
        self._rules.append((re.compile(kw_pattern), _fmt(kw_color, bold=True)))

        # Builtins
        bi_pattern = r"\b(" + "|".join(_BUILTINS) + r")\b"
        self._rules.append((re.compile(bi_pattern), _fmt(builtin_color)))

        # self / cls
        self._rules.append((re.compile(r"\bself\b"), _fmt(self_color, italic=True)))
        self._rules.append((re.compile(r"\bcls\b"), _fmt(self_color, italic=True)))

        # Decorators
        self._rules.append((re.compile(r"@\w+"), _fmt(decorator_color)))

        # Numbers (int, float, hex, octal, binary)
        self._rules.append((re.compile(r"\b\d+\.?\d*([eE][+-]?\d+)?\b"), _fmt(number_color)))
        self._rules.append((re.compile(r"\b0[xXoObB][0-9a-fA-F]+\b"), _fmt(number_color)))

        # Function/class definitions
        self._rules.append((re.compile(r"(?<=\bdef\s)\w+"), _fmt(func_color, bold=True)))
        self._rules.append((re.compile(r"(?<=\bclass\s)\w+"), _fmt(func_color, bold=True)))

        # Strings (single and double quotes)
        self._rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), _fmt(string_color)))
        self._rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), _fmt(string_color)))

        # f-strings
        self._rules.append((re.compile(r"f'[^'\\]*(\\.[^'\\]*)*'"), _fmt(string_color)))
        self._rules.append((re.compile(r'f"[^"\\]*(\\.[^"\\]*)*"'), _fmt(string_color)))

        # Comments (must be last to override)
        self._rules.append((re.compile(r"#[^\n]*"), _fmt(comment_color, italic=True)))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


# ─── Line Number Area ────────────────────────────────────────────────────────


class _LineNumberArea(QWidget):
    """Gutter widget showing line numbers next to the code editor."""

    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.paint_line_numbers(event)


# ─── Code Editor (QPlainTextEdit subclass) ───────────────────────────────────


class CodeEditor(QPlainTextEdit):
    """Plain text editor with line numbers and Python syntax highlighting."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Font
        font = QFont("Fira Code", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab width (4 spaces)
        metrics = QFontMetrics(font)
        self.setTabStopDistance(4 * metrics.horizontalAdvance(" "))

        # Line numbers
        self._line_area = _LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_area_width(0)

        # Syntax highlighting
        self._highlighter = PythonHighlighter(self.document(), dark=False)

        # Initial highlight
        self._highlight_current_line()

    def set_dark_mode(self, dark: bool) -> None:
        """Switch syntax colours and editor UI for dark/light theme."""
        self._highlighter.set_dark_mode(dark)
        
        # Update colors from palette
        from quantia.theme.palette import PALETTE, Theme
        p = PALETTE[Theme.DARK if dark else Theme.LIGHT]
        
        # Selection highlight
        self._current_line_color = QColor(p["surface_tertiary"])
        
        # Line number area colors
        self._line_area_bg = QColor(p["surface_secondary"])
        self._line_number_color = QColor(p["text_secondary"])
        
        self._update_line_area_width(0)
        self._highlight_current_line()

    # ── Line number area ─────────────────────────────────────────────────

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        space = 8 + self.fontMetrics().horizontalAdvance("9") * max(digits, 3)
        return space

    def _update_line_area_width(self, _: int) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_area)
        bg_color = getattr(self, "_line_area_bg", QColor("#E8EBF0"))
        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(getattr(self, "_line_number_color", QColor("#9CA3AF")))
                painter.drawText(
                    0, top,
                    self._line_area.width() - 4, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

        painter.end()

    # ── Current line highlight ───────────────────────────────────────────

    def _highlight_current_line(self) -> None:
        selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = getattr(self, "_current_line_color", QColor("#F0F2F5"))
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
        self.setExtraSelections(selections)

    # ── Get selected or all text ─────────────────────────────────────────

    def get_selected_text(self) -> str:
        """Return selected text, or current line if nothing selected."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            return cursor.selectedText().replace("\u2029", "\n")
        # No selection: return current line
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        return cursor.selectedText()

    def get_all_text(self) -> str:
        return self.toPlainText()


# ─── Script Editor Widget (wrapper with toolbar) ─────────────────────────────


class ScriptEditorWidget(QWidget):
    """Complete script editor with toolbar, line numbers, and syntax highlighting."""

    # Emitted when user requests running code
    run_code = Signal(str)  # the code text to execute
    run_selection = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Editor toolbar ───────────────────────────────────────────────
        toolbar = QWidget()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(4, 2, 4, 2)
        tb_layout.setSpacing(4)

        run_btn = QPushButton()
        run_btn.setIcon(feather_icon("play", "#26A69A", 16))
        run_btn.setToolTip("Run All (F5)")
        run_btn.setFixedSize(28, 28)
        run_btn.setFlat(True)
        run_btn.clicked.connect(self._run_all)
        tb_layout.addWidget(run_btn)

        run_sel_btn = QPushButton()
        run_sel_btn.setIcon(feather_icon("play-circle", "#009688", 16))
        run_sel_btn.setToolTip("Run Selection (Ctrl+Enter)")
        run_sel_btn.setFixedSize(28, 28)
        run_sel_btn.setFlat(True)
        run_sel_btn.clicked.connect(self._run_selection)
        tb_layout.addWidget(run_sel_btn)

        sep = QLabel("│")
        sep.setStyleSheet("color: #D1D5DB;")
        tb_layout.addWidget(sep)

        save_btn = QPushButton()
        save_btn.setIcon(feather_icon("save", "#2D3E50", 16))
        save_btn.setToolTip("Save Script (Ctrl+Shift+S)")
        save_btn.setFixedSize(28, 28)
        save_btn.setFlat(True)
        save_btn.clicked.connect(self._save_script)
        tb_layout.addWidget(save_btn)

        clear_btn = QPushButton()
        clear_btn.setIcon(feather_icon("trash-2", "#6B7280", 16))
        clear_btn.setToolTip("Clear Editor")
        clear_btn.setFixedSize(28, 28)
        clear_btn.setFlat(True)
        clear_btn.clicked.connect(self._clear)
        tb_layout.addWidget(clear_btn)

        tb_layout.addStretch()

        # Cursor position indicator
        self._pos_label = QLabel("Ln 1, Col 1")
        self._pos_label.setStyleSheet("font-size: 11px; color: #6B7280;")
        tb_layout.addWidget(self._pos_label)

        layout.addWidget(toolbar)

        # ── Code editor ──────────────────────────────────────────────────
        self._editor = CodeEditor()
        self._editor.setPlaceholderText(
            "# Write Python code here, or use the GUI —\n"
            "# every action generates code automatically.\n"
            "#\n"
            "# Run All:       F5\n"
            "# Run Selection: Ctrl+Enter\n"
        )
        self._editor.cursorPositionChanged.connect(self._update_position)
        layout.addWidget(self._editor)

        # ── Keyboard shortcuts ───────────────────────────────────────────
        run_shortcut = QShortcut(QKeySequence("F5"), self)
        run_shortcut.activated.connect(self._run_all)

        run_sel_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        run_sel_shortcut.activated.connect(self._run_selection)

    # ── Public API ───────────────────────────────────────────────────────

    def append_code(self, code: str) -> None:
        """Append generated code to the editor (from GUI actions)."""
        current = self._editor.toPlainText()
        if current and not current.endswith("\n"):
            self._editor.appendPlainText("")
        self._editor.appendPlainText(code)

    def set_dark_mode(self, dark: bool) -> None:
        self._editor.set_dark_mode(dark)

    def refresh_theme(self, theme: Any) -> None:
        """Update editor colors for the current theme."""
        from quantia.theme.palette import Theme, PALETTE
        is_dark = (theme == Theme.DARK)
        self._editor.set_dark_mode(is_dark)
        
        # Sync palette colors for labels and toolbar
        p = PALETTE[theme]
        self._pos_label.setStyleSheet(f"font-size: 11px; color: {p['text_secondary']};")
        
        # Refresh toolbar icons
        ic = p["text_secondary"]
        for btn in self.findChildren(QPushButton):
            tt = btn.toolTip() or ""
            if "Run All" in tt:
                btn.setIcon(feather_icon("play", "#26A69A", 16))
            elif "Run Selection" in tt:
                btn.setIcon(feather_icon("play-circle", "#009688", 16))
            elif "Save" in tt:
                btn.setIcon(feather_icon("save", ic, 16))
            elif "Clear" in tt:
                btn.setIcon(feather_icon("trash-2", ic, 16))

    def set_text(self, text: str) -> None:
        self._editor.setPlainText(text)

    def get_text(self) -> str:
        return self._editor.toPlainText()

    @property
    def editor(self) -> CodeEditor:
        return self._editor

    # ── Internal ─────────────────────────────────────────────────────────

    def _run_all(self) -> None:
        code = self._editor.get_all_text()
        if code.strip():
            self.run_code.emit(code)

    def _run_selection(self) -> None:
        code = self._editor.get_selected_text()
        if code.strip():
            self.run_selection.emit(code)

    def _save_script(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Script", str(get_scripts_dir()), "Python Files (*.py);;All Files (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._editor.get_all_text())

    def _clear(self) -> None:
        self._editor.clear()

    def _update_position(self) -> None:
        cursor = self._editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self._pos_label.setText(f"Ln {line}, Col {col}")
