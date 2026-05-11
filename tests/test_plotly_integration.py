"""Comprehensive test for Plotly integration across all dialogs."""
import sys
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

import pandas as pd
df = pd.DataFrame({'A': [1,2,3,4,5], 'B': [5,4,3,2,1], 'C': ['x','y','x','y','x']})

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")

# Test 1: Histogram
from quantia.ui.dialogs.histogram import HistogramDialog
dlg = HistogramDialog(df)
dlg.list_variable.addItem('A')
code_mpl = dlg._generate_matplotlib_code('A')
check("Histogram mpl: sns.histplot", 'sns.histplot' in code_mpl)
check("Histogram mpl: show_plot", 'show_plot' in code_mpl)
code_plotly = dlg._generate_plotly_code('A')
check("Histogram plotly: px.histogram", 'px.histogram' in code_plotly)
check("Histogram plotly: show_plotly", 'show_plotly' in code_plotly)

# Test 2: Scatter
from quantia.ui.dialogs.scatter import ScatterPlotDialog
dlg = ScatterPlotDialog(df)
code_mpl = dlg._generate_matplotlib_code('A', 'B', None)
check("Scatter mpl: sns.scatterplot", 'sns.scatterplot' in code_mpl)
code_plotly = dlg._generate_plotly_code('A', 'B', 'C')
check("Scatter plotly: px.scatter", 'px.scatter' in code_plotly)
check("Scatter plotly: color", "color='C'" in code_plotly)

# Test 3: BoxPlot
from quantia.ui.dialogs.boxplot import BoxPlotDialog
dlg = BoxPlotDialog(df)
code_mpl = dlg._generate_matplotlib_code('A', None)
check("BoxPlot mpl: sns.boxplot", 'sns.boxplot' in code_mpl)
code_plotly = dlg._generate_plotly_code('A', 'C')
check("BoxPlot plotly: px.box", 'px.box' in code_plotly)

# Test 4: Violin
from quantia.ui.dialogs.violinplot import ViolinPlotDialog
dlg = ViolinPlotDialog(df)
code_mpl = dlg._generate_matplotlib_code('A', None)
check("ViolinPlot mpl: sns.violinplot", 'sns.violinplot' in code_mpl)
code_plotly = dlg._generate_plotly_code('A', None)
check("ViolinPlot plotly: px.violin", 'px.violin' in code_plotly)

# Test 5: Line Chart
from quantia.ui.dialogs.linechart import LineChartDialog
dlg = LineChartDialog(df)
code_mpl = dlg._generate_matplotlib_code('A', 'B', None)
check("LineChart mpl: sns.lineplot", 'sns.lineplot' in code_mpl)
code_plotly = dlg._generate_plotly_code('A', 'B', None)
check("LineChart plotly: px.line", 'px.line' in code_plotly)

# Test 6: Bar Chart
from quantia.ui.dialogs.barchart import BarChartDialog
dlg = BarChartDialog(df)
code_mpl = dlg._generate_matplotlib_code('C', None)
check("BarChart mpl: sns.countplot", 'sns.countplot' in code_mpl)
code_plotly = dlg._generate_plotly_code('C', 'A')
check("BarChart plotly: px.bar", 'px.bar' in code_plotly)

# Test 7: Heatmap
from quantia.ui.dialogs.heatmap import HeatmapDialog
dlg = HeatmapDialog(df)
code_mpl = dlg._generate_matplotlib_code(['A', 'B'])
check("Heatmap mpl: sns.heatmap", 'sns.heatmap' in code_mpl)
code_plotly = dlg._generate_plotly_code(['A', 'B'])
check("Heatmap plotly: go.Heatmap", 'go.Heatmap' in code_plotly)

# Test 8: Q-Q Plot
from quantia.ui.dialogs.qqplot import QQPlotDialog
dlg = QQPlotDialog(df)
code_mpl = dlg._generate_matplotlib_code('A', 'norm')
check("QQPlot mpl: sm.qqplot", 'sm.qqplot' in code_mpl)
code_plotly = dlg._generate_plotly_code('A', 'norm')
check("QQPlot plotly: stats.probplot", 'stats.probplot' in code_plotly)
check("QQPlot plotly: show_plotly", 'show_plotly' in code_plotly)

# Test 9: Plotly styles (all 10)
from quantia.ui.central.plotly_styles import PLOTLY_STYLES, generate_plotly_style_code
for name in PLOTLY_STYLES:
    code = generate_plotly_style_code(name)
    check(f"Plotly Style: {name}", 'go.layout.Template' in code)

# Test 10: Backend selector
check("Backend selector exists", hasattr(dlg, 'cmb_backend'))
check("Default backend is matplotlib", dlg._backend == 'matplotlib')
check("_is_plotly returns False by default", not dlg._is_plotly())

# Test 11: PlotViewWidget has both methods
from quantia.ui.central.plot_view import PlotViewWidget
check("PlotViewWidget.add_plot exists", hasattr(PlotViewWidget, 'add_plot'))
check("PlotViewWidget.add_plotly_plot exists", hasattr(PlotViewWidget, 'add_plotly_plot'))

# Test 12: Worker signals
from quantia.utils.worker import WorkerSignals
check("WorkerSignals.display_plotly exists", hasattr(WorkerSignals, 'display_plotly'))

# Test 13: Plotly view dialog
from quantia.ui.central.plotly_view import InteractivePlotlyDialog
check("InteractivePlotlyDialog importable", True)

# Test 14: pyproject.toml optional deps
with open('pyproject.toml', 'r') as f:
    toml_content = f.read()
check("pyproject.toml: plotly optional dep", 'plotly' in toml_content and 'PySide6-WebEngine' in toml_content)

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED!")
    sys.exit(1)
