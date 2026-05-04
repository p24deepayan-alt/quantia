"""Path management for Quantia user data."""

from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QStandardPaths


def get_quantia_root() -> Path:
    """Get the Quantia root folder in User Documents."""
    docs_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    if not docs_path:
        # Fallback to home/Documents if QStandardPaths fails
        root = Path.home() / "Documents" / "Quantia"
    else:
        root = Path(docs_path) / "Quantia"
    
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_plots_dir() -> Path:
    """Get directory for saved plots."""
    d = get_quantia_root() / "Plots"
    d.mkdir(exist_ok=True)
    return d


def get_exports_dir() -> Path:
    """Get directory for exported data files."""
    d = get_quantia_root() / "Exports"
    d.mkdir(exist_ok=True)
    return d


def get_workspaces_dir() -> Path:
    """Get directory for Quantia workspace files."""
    d = get_quantia_root() / "Workspaces"
    d.mkdir(exist_ok=True)
    return d


def get_scripts_dir() -> Path:
    """Get directory for saved Python scripts."""
    d = get_quantia_root() / "Scripts"
    d.mkdir(exist_ok=True)
    return d
