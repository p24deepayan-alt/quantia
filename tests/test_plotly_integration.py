"""Comprehensive test for Plotly integration across all dialogs."""

import pytest
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

@pytest.fixture
def df():
    return pd.DataFrame({
        'A': [1, 2, 3, 4, 5], 
        'B': [5, 4, 3, 2, 1], 
        'C': ['x', 'y', 'x', 'y', 'x']
    })

def test_histogram_plotly_code(qtbot, df):
    from quantia.ui.dialogs.histogram import HistogramDialog
    dlg = HistogramDialog(df)
    qtbot.addWidget(dlg)
    dlg.list_variable.addItem('A')
    
    code_mpl = dlg._generate_matplotlib_code(['A'])
    assert 'sns.histplot' in code_mpl
    assert 'show_plot' in code_mpl
    
    code_plotly = dlg._generate_plotly_code(['A'])
    assert 'px.histogram' in code_plotly
    assert 'show_plotly' in code_plotly

def test_scatter_plotly_code(qtbot, df):
    from quantia.ui.dialogs.scatter import ScatterPlotDialog
    dlg = ScatterPlotDialog(df)
    qtbot.addWidget(dlg)
    
    code_mpl = dlg._generate_matplotlib_code('A', 'B', None)
    assert 'sns.scatterplot' in code_mpl
    
    code_plotly = dlg._generate_plotly_code('A', 'B', 'C')
    assert 'px.scatter' in code_plotly
    assert "color='C'" in code_plotly

def test_boxplot_plotly_code(qtbot, df):
    from quantia.ui.dialogs.boxplot import BoxPlotDialog
    dlg = BoxPlotDialog(df)
    qtbot.addWidget(dlg)
    
    code_mpl = dlg._generate_matplotlib_code('A', None)
    assert 'sns.boxplot' in code_mpl
    
    code_plotly = dlg._generate_plotly_code('A', 'C')
    assert 'px.box' in code_plotly

def test_violin_plotly_code(qtbot, df):
    from quantia.ui.dialogs.violinplot import ViolinPlotDialog
    dlg = ViolinPlotDialog(df)
    qtbot.addWidget(dlg)
    
    code_mpl = dlg._generate_matplotlib_code('A', None)
    assert 'sns.violinplot' in code_mpl
    
    code_plotly = dlg._generate_plotly_code('A', None)
    assert 'px.violin' in code_plotly

def test_linechart_plotly_code(qtbot, df):
    from quantia.ui.dialogs.linechart import LineChartDialog
    dlg = LineChartDialog(df)
    qtbot.addWidget(dlg)
    
    code_mpl = dlg._generate_matplotlib_code('A', 'B', None)
    assert 'sns.lineplot' in code_mpl
    
    code_plotly = dlg._generate_plotly_code('A', 'B', None)
    assert 'px.line' in code_plotly

def test_barchart_plotly_code(qtbot, df):
    from quantia.ui.dialogs.barchart import BarChartDialog
    dlg = BarChartDialog(df)
    qtbot.addWidget(dlg)
    
    code_mpl = dlg._generate_matplotlib_code('C', None)
    assert 'sns.countplot' in code_mpl
    
    code_plotly = dlg._generate_plotly_code('C', 'A')
    assert 'px.bar' in code_plotly

def test_heatmap_plotly_code(qtbot, df):
    from quantia.ui.dialogs.heatmap import HeatmapDialog
    dlg = HeatmapDialog(df)
    qtbot.addWidget(dlg)
    
    code_mpl = dlg._generate_matplotlib_code(['A', 'B'])
    assert 'sns.heatmap' in code_mpl
    
    code_plotly = dlg._generate_plotly_code(['A', 'B'])
    assert 'go.Heatmap' in code_plotly

def test_qqplot_plotly_code(qtbot, df):
    from quantia.ui.dialogs.qqplot import QQPlotDialog
    dlg = QQPlotDialog(df)
    qtbot.addWidget(dlg)
    
    code_mpl = dlg._generate_matplotlib_code('A', 'norm')
    assert 'sm.qqplot' in code_mpl
    
    code_plotly = dlg._generate_plotly_code('A', 'norm')
    assert 'stats.probplot' in code_plotly
    assert 'show_plotly' in code_plotly

def test_plotly_styles():
    from quantia.ui.central.plotly_styles import PLOTLY_STYLES, generate_plotly_style_code
    for name in PLOTLY_STYLES:
        code = generate_plotly_style_code(name)
        assert 'go.layout.Template' in code

def test_backend_selector(qtbot, df):
    from quantia.ui.dialogs.qqplot import QQPlotDialog
    dlg = QQPlotDialog(df)
    qtbot.addWidget(dlg)
    assert hasattr(dlg, 'cmb_backend')
    assert dlg._backend == 'matplotlib'
    assert not dlg._is_plotly()

def test_plot_view_methods(qtbot):
    from quantia.ui.central.plot_view import PlotViewWidget
    widget = PlotViewWidget()
    qtbot.addWidget(widget)
    assert hasattr(PlotViewWidget, 'add_plot')
    assert hasattr(PlotViewWidget, 'add_plotly_plot')

def test_worker_signals():
    from quantia.utils.worker import WorkerSignals
    # display_plotly is checked if it exists
    assert hasattr(WorkerSignals, 'display_plotly')

def test_interactive_dialog_imports():
    from quantia.ui.central.plotly_view import InteractivePlotlyDialog
    assert InteractivePlotlyDialog is not None

def test_pyproject_deps():
    with open('pyproject.toml', 'r') as f:
        toml_content = f.read()
    assert 'plotly' in toml_content
    assert 'PySide6-WebEngine' in toml_content
