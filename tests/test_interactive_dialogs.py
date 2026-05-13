"""Test interactive plot dialogs for correct initialization and imports."""

import pytest
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

def test_interactive_plot_dialog_instantiation(qtbot):
    """Verify InteractivePlotDialog can be instantiated without NameError."""
    from quantia.ui.central.interactive_plot import InteractivePlotDialog
    
    fig = Figure()
    dialog = InteractivePlotDialog(fig)
    qtbot.addWidget(dialog)
    
    # Check if setAttribute(Qt.WA_DeleteOnClose) worked
    assert dialog.testAttribute(Qt.WA_DeleteOnClose)
    assert dialog.windowTitle() == "Interactive Plot"

def test_interactive_plotly_dialog_instantiation(qtbot):
    """Verify InteractivePlotlyDialog can be instantiated without NameError."""
    from quantia.ui.central.plotly_view import InteractivePlotlyDialog
    
    html = "<html><body>Test Plotly</body></html>"
    dialog = InteractivePlotlyDialog(html)
    qtbot.addWidget(dialog)
    
    # Check if setAttribute(Qt.WA_DeleteOnClose) worked
    assert dialog.testAttribute(Qt.WA_DeleteOnClose)
    assert dialog.windowTitle() == "Interactive Plot (Plotly)"

def test_imports_contain_qt():
    """Verify that the files actually import Qt now."""
    import src.quantia.ui.central.interactive_plot as ip
    import src.quantia.ui.central.plotly_view as pv
    
    assert hasattr(ip, 'Qt')
    assert hasattr(pv, 'Qt')
