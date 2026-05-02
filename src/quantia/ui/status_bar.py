"""Status bar for the Quantia main window.

Shows: memory usage | dataset dimensions | GPU status | progress bar.
Styled to match Excel/VS Code status bars (brand colour background, white text).
"""

from __future__ import annotations

import psutil
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QStatusBar, QWidget, QHBoxLayout


class QuantiaStatusBar(QStatusBar):
    """Application status bar with live memory gauge and dataset info."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # ── Memory usage ─────────────────────────────────────────────────
        self._memory_label = QLabel("Memory: —")
        self._memory_label.setToolTip("Current process memory usage")
        self.addWidget(self._memory_label)

        # ── Separator ────────────────────────────────────────────────────
        sep1 = QLabel("│")
        sep1.setStyleSheet("color: #888888;")
        self.addWidget(sep1)

        # ── Dataset dimensions ───────────────────────────────────────────
        self._dataset_label = QLabel("No data loaded")
        self._dataset_label.setToolTip("Current dataset dimensions")
        self.addWidget(self._dataset_label)

        sep2 = QLabel("│")
        sep2.setStyleSheet("color: #888888;")
        self.addWidget(sep2)

        # ── GPU status ───────────────────────────────────────────────────
        self._gpu_label = QLabel("CPU only")
        self._gpu_label.setToolTip("GPU acceleration status")
        self.addWidget(self._gpu_label)

        # ── Spacer ───────────────────────────────────────────────────────
        spacer = QWidget()
        spacer.setFixedWidth(1)
        self.addWidget(spacer, 1)  # stretch

        # ── Progress bar (right side, hidden by default) ─────────────────
        self._progress = QProgressBar()
        self._progress.setFixedWidth(160)
        self._progress.setFixedHeight(14)
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        self.addPermanentWidget(self._progress)

        # ── Encoding / line ending (right-aligned like VS Code) ──────────
        self._encoding_label = QLabel("UTF-8")
        self.addPermanentWidget(self._encoding_label)

        # ── Refresh timer (every 3 seconds) ──────────────────────────────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_memory)
        self._timer.start(3000)
        self._update_memory()

    # ── Public API ───────────────────────────────────────────────────────

    def set_dataset_info(self, rows: int, cols: int) -> None:
        """Update dataset dimensions display."""
        self._dataset_label.setText(f"Rows: {rows:,} × Cols: {cols}")

    def clear_dataset_info(self) -> None:
        self._dataset_label.setText("No data loaded")

    def set_gpu_status(self, device: str) -> None:
        self._gpu_label.setText(f"GPU: {device}")

    def show_progress(self, value: int, maximum: int = 100, text: str = "") -> None:
        self._progress.setMaximum(maximum)
        self._progress.setValue(value)
        if text:
            self._progress.setFormat(text)
        self._progress.setVisible(True)

    def hide_progress(self) -> None:
        self._progress.setVisible(False)

    # ── Internal ─────────────────────────────────────────────────────────

    def _update_memory(self) -> None:
        try:
            process = psutil.Process()
            mem_mb = process.memory_info().rss / (1024 * 1024)
            self._memory_label.setText(f"Memory: {mem_mb:.0f} MB")
        except Exception:
            self._memory_label.setText("Memory: —")
