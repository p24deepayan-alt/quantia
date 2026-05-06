"""Background calculation and threading utilities for Quantia.

Provides a Worker/Runner pattern to execute Python code in a separate thread,
keeping the UI responsive.
"""

from __future__ import annotations

import sys
import traceback
import io
import contextlib
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal()
    error = Signal(tuple)  # (exctype, value, traceback.format_exc())
    result = Signal(object) # (namespace, stdout, stderr)
    progress = Signal(int)


class ScriptWorker(QRunnable):
    """
    Worker thread for executing Python scripts.
    """

    def __init__(self, code: str, namespace: dict[str, Any]):
        super().__init__()
        self.code = code
        self.namespace = namespace
        self.signals = WorkerSignals()

        # Inject progress function into namespace
        self.namespace["progress"] = self.emit_progress

    def emit_progress(self, n: int):
        """Callback function used within scripts to report progress."""
        self.signals.progress.emit(int(n))

    @Slot()
    def run(self):
        """
        Execute the code in a background thread.
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                # Execute the code in the provided namespace
                exec(self.code, self.namespace)
            
            # Pack results
            result_data = {
                "namespace": self.namespace,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue()
            }
            self.signals.result.emit(result_data)
            
        except Exception:
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()
