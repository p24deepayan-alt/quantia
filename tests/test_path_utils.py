"""Tests for Quantia path utilities."""

import os
from pathlib import Path
from quantia.utils.paths import (
    get_quantia_root,
    get_exports_dir,
    get_plots_dir,
    get_workspaces_dir,
    get_scripts_dir
)


def test_directories_exist():
    """Verify that all standard Quantia directories are accessible."""
    dirs = [
        get_quantia_root(),
        get_exports_dir(),
        get_plots_dir(),
        get_workspaces_dir(),
        get_scripts_dir()
    ]
    
    for d in dirs:
        p = Path(d)
        assert p.exists(), f"Directory {d} should exist"
        assert p.is_dir(), f"Path {d} should be a directory"


def test_quantia_root_structure():
    """Verify the expected sub-folder structure under the root Quantia folder."""
    root = Path(get_quantia_root())
    expected_subs = ["Plots", "Exports", "Workspaces", "Scripts"]
    
    for sub in expected_subs:
        sub_path = root / sub
        assert sub_path.exists(), f"Sub-directory {sub} missing from Quantia root"
