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
    assert window._tabs.count() == 6
    assert window._tabs.tabText(0) == "Data View"
    assert window._tabs.tabText(5) == "Dashboard Builder"

def test_load_data_updates_ui(qtbot, dummy_df):
    """Test that loading data updates the variable panel and dashboard tab."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    # Mock data loading
    window._data_view.load_dataframe(dummy_df)
    window._on_data_loaded(dummy_df)
    
    # Check that the variable list populated
    assert window._variable_panel._tree.topLevelItemCount() == 3
    
    # Check that dashboard tab combo boxes updated
    # Dash panel 1 x-combo box should have "-- None --" + 3 columns
    assert window._dashboard_tab.plot_configs[0]["x"].count() == 4

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
