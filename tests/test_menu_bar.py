"""Tests for Quantia Menu Bar."""

import pytest
from quantia.ui.main_window import MainWindow

def test_menu_bar_structure(qtbot):
    """Test that the main menus are created correctly."""
    window = MainWindow()
    qtbot.addWidget(window)
    menu_bar = window._menu_bar
    
    # Extract top-level menu titles
    menus = [action.text() for action in menu_bar.actions()]
    
    assert "&File" in menus
    assert "&Edit" in menus
    assert "&Data" in menus
    assert "&Statistics" in menus
    assert "&Machine Learning" in menus
    assert "&Visualize" in menus
    assert "&Report" in menus
    assert "&Help" in menus

def _find_action(window, text_substring):
    """Recursively search for an action by text using findChildren."""
    from PySide6.QtGui import QAction
    for action in window.findChildren(QAction):
        if action.text() and text_substring in action.text():
            return action
    return None

def test_menu_bar_signals(qtbot):
    """Test that triggering actions emits the correct signals."""
    window = MainWindow()
    qtbot.addWidget(window)
    menu_bar = window._menu_bar

    # List of tuples: (Action text substring, signal to wait for)
    actions_to_test = [
        ("CSV (.csv)", menu_bar.import_csv),
        ("Exit", menu_bar.exit_app),
        ("Undo", menu_bar.undo),
        ("Clean Data", menu_bar.clean_data),
        ("Descriptive Statistics", menu_bar.descriptive_stats),
        ("Linear Regression", menu_bar.regression_linear),
        ("Random Forest…", menu_bar.cls_random_forest), # exact match for Classification to avoid matching Regression
        ("K-Means", menu_bar.clu_kmeans),
        ("Histogram", menu_bar.histogram),
        ("Generate Report", menu_bar.generate_report),
        ("About Quantia", menu_bar.about),
    ]

    for action_text, signal in actions_to_test:
        action = None
        from PySide6.QtGui import QAction
        for act in window.findChildren(QAction):
            if act.text() and action_text in act.text():
                action = act
                # Break on exact match to prevent finding broader ones later
                if action_text == act.text() or action_text + "…" == act.text():
                    break
                    
        assert action is not None, f"Action '{action_text}' not found."
        
        with qtbot.waitSignal(signal, timeout=1000):
            action.trigger()

def test_menu_bar_shortcuts(qtbot):
    """Test that some key shortcuts are assigned correctly."""
    window = MainWindow()
    qtbot.addWidget(window)
    menu_bar = window._menu_bar

    open_action = _find_action(window, "Open Project")
    assert open_action.shortcut().toString() == "Ctrl+O"

    save_action = _find_action(window, "Save Project")
    assert save_action.shortcut().toString() == "Ctrl+S"

    exit_action = _find_action(window, "Exit")
    assert exit_action.shortcut().toString() == "Ctrl+Q"
