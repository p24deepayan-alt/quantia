"""Runtime tests for Quantia GUI."""

import pandas as pd
import pytest
from PySide6.QtCore import Qt

from quantia.ui.main_window import MainWindow
from quantia.ui.dialogs.descriptive import DescriptiveStatsDialog
from quantia.ui.dialogs.ttest import TTestDialog
from quantia.ui.dialogs.scatter import ScatterPlotDialog
from quantia.ui.dialogs.preferences import PreferencesDialog

@pytest.fixture
def dummy_df():
    return pd.DataFrame({
        "A": [1, 2, 3, 4, 5],
        "B": [5, 4, 3, 2, 1],
        "Group": ["X", "X", "Y", "Y", "X"]
    })

def test_main_window_startup(qtbot):
    """Test that the main window initializes without crashing."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    assert window.windowTitle() == "Quantia — Untitled"
    
    # Check that tabs are present
    assert window._tabs.count() == 5
    assert window._tabs.tabText(0) == "Data View"

def test_load_data_updates_ui(qtbot, dummy_df):
    """Test that loading data updates the variable panel and report maker."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    # Mock data loading
    window._data_view.load_dataframe(dummy_df)
    window._on_data_loaded(dummy_df)
    
    # Check that the variable list populated
    assert window._variable_panel._tree.topLevelItemCount() == 3
    
    # We no longer instantiate the report maker window implicitly on startup
    assert window._report_studio_window is None

def test_dialog_instantiation(qtbot, dummy_df):
    """Test that various dialogs can be instantiated without errors."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    # 1. Descriptive Stats
    desc_dialog = DescriptiveStatsDialog(dummy_df, parent=window)
    assert desc_dialog.windowTitle() == "Descriptive Statistics"
    
    # 2. T-Test
    ttest_dialog = TTestDialog(dummy_df, parent=window)
    assert ttest_dialog.windowTitle() == "Independent Samples t-test"
    
    # 3. Scatter Plot
    scatter_dialog = ScatterPlotDialog(dummy_df, parent=window)
    assert scatter_dialog.windowTitle() == "Scatter Plot"

def test_preferences_dialog(qtbot):
    """Test that the preferences dialog can be instantiated."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    pref_dialog = PreferencesDialog(parent=window)
    assert pref_dialog.windowTitle() == "Preferences"

def test_new_ml_dialogs_instantiation(qtbot, dummy_df):
    """Test that the new ML-specific dialogs can be instantiated."""
    from quantia.ui.main_window import MainWindow
    from quantia.ui.dialogs.tree_regression import (
        LinearRegressionMLDialog, RidgeDialog, LassoDialog, ElasticNetDialog
    )
    from quantia.ui.dialogs.classification import LogisticRegressionMLDialog
    
    window = MainWindow()
    qtbot.addWidget(window)
    
    # ML Regression
    assert RidgeDialog(dummy_df, window).windowTitle() == "Ridge Regression"
    assert LassoDialog(dummy_df, window).windowTitle() == "Lasso Regression"
    assert ElasticNetDialog(dummy_df, window).windowTitle() == "ElasticNet Regression"
    assert LinearRegressionMLDialog(dummy_df, window).windowTitle() == "Linear Regression (ML)"
    
    # ML Classification
    assert LogisticRegressionMLDialog(dummy_df, window).windowTitle() == "Logistic Regression (ML)"

