"""Code generation utilities for Quantia."""

from __future__ import annotations

def get_gpu_import(sklearn_import: str, sklearn_class: str, cuml_module: str | None = None) -> list[str]:
    """
    Returns the appropriate Python import statements taking ComputeMode into account.
    If GPU mode is enabled, it attempts to use cuML (RAPIDS) or falls back to Scikit-Learn.
    """
    from quantia.core.settings import SettingsManager, ComputeMode
    
    settings = SettingsManager()
    base_import = f"from {sklearn_import} import {sklearn_class}"
    
    if settings.compute_mode == ComputeMode.GPU and cuml_module:
        return [
            "try:",
            f"    from {cuml_module} import {sklearn_class}",
            "    print('Using GPU Acceleration (cuML)')",
            "except ImportError:",
            f"    {base_import}",
            "    print('GPU acceleration requested but cuML not installed. Falling back to CPU.')"
        ]
    
    return [base_import]
