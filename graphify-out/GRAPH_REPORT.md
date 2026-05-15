# Graph Report - .  (2026-05-15)

## Corpus Check
- Large corpus: 412 files · ~107,383 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 1752 nodes · 5923 edges · 51 communities detected
- Extraction: 36% EXTRACTED · 64% INFERRED · 0% AMBIGUOUS · INFERRED: 3788 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]

## God Nodes (most connected - your core abstractions)
1. `BaseAnalysisDialog` - 179 edges
2. `MainWindow` - 178 edges
3. `Theme` - 94 edges
4. `BaseLogicNode` - 93 edges
5. `LinearRegressionDialog` - 83 edges
6. `LogisticRegressionDialog` - 79 edges
7. `SettingsManager` - 78 edges
8. `Main Window — the Quantia application shell.  Layout inspired by: - MS Excel:` - 75 edges
9. `Quantia main application window.` - 75 edges
10. `Switch between Light and Dark modes and refresh all components.` - 75 edges

## Surprising Connections (you probably didn't know these)
- `df()` --calls--> `dataframe()`  [INFERRED]
  tests\test_plotly_integration.py → src\quantia\core\data_model.py
- `str_df()` --calls--> `dataframe()`  [INFERRED]
  tests\test_string_dialogs.py → src\quantia\core\data_model.py
- `numeric_df()` --calls--> `dataframe()`  [INFERRED]
  tests\test_string_dialogs.py → src\quantia\core\data_model.py
- `mixed_df()` --calls--> `dataframe()`  [INFERRED]
  tests\test_type_convert.py → src\quantia\core\data_model.py
- `Complete script editor with toolbar, line numbers, and syntax highlighting.` --uses--> `Theme`  [INFERRED]
  src\quantia\ui\central\script_editor.py → src\quantia\theme\palette.py

## Hyperedges (group relationships)
- **Font Management Scripts** — check_fonts_script, install_fonts_script, install_heros_script, final_font_check_script, check_heros_name_script [INFERRED 0.85]
- **Report Document Models** — document_Document, document_Page, document_Block [INFERRED 0.90]
- **Main Window Tabs** — main_window_MainWindow, data_view_DataViewWidget, script_editor_ScriptEditorWidget, results_view_ResultsViewWidget, plot_view_PlotViewWidget, view_WorkflowTab [EXTRACTED 1.00]
- **Report Canvas Items** — items_BaseBlockItem, items_PlotBlockItem, items_TextBlockItem, items_TableBlockItem [EXTRACTED 1.00]
- **Workflow Graphics Items** — wf_items_NodeItem, wf_items_PortItem, wf_items_EdgeItem [EXTRACTED 1.00]
- **Analysis Dialogs** — anova_models_AnovaModelComparisonDialog, barchart_BarChartDialog, boxplot_BoxPlotDialog, chi_square_ChiSquareDialog, classification_BaseClassificationDialog, clean_data_CleanDataDialog, clustering_BaseClusteringDialog, concat_cols_ConcatColsDialog, correlation_CorrelationDialog, density2d_Density2DPlotDialog, descriptive_DescriptiveStatsDialog, filter_data_FilterDataDialog, find_replace_FindReplaceDialog, heatmap_HeatmapDialog, histogram_HistogramDialog, if_else_IfElseDialog, linechart_LineChartDialog, logistic_regression_LogisticRegressionDialog, merge_join_MergeJoinDialog, model_compare_ModelComparisonDialog, nonparametric_NonParametricDialog [EXTRACTED 1.00]
- **Classification Models** — classification_RandomForestDialog, classification_GradientBoostingDialog, classification_DecisionTreeDialog, classification_SVMDialog, classification_KNNDialog, classification_LDADialog, classification_QDADialog, classification_NaiveBayesDialog, classification_LogisticRegressionMLDialog [EXTRACTED 1.00]
- **Clustering Models** — clustering_KMeansDialog, clustering_HierarchicalDialog, clustering_DBSCANDialog, clustering_GMMDialog [EXTRACTED 1.00]
- **Analysis Dialogs** — pairplot_PairPlotDialog, pca_PCADialog, piechart_PieChartDialog, pivot_table_PivotTableDialog, qqplot_QQPlotDialog, regression_LinearRegressionDialog, ridgeplot_RidgePlotDialog, scatter_ScatterPlotDialog, string_format_StringFormatDialog, stripplot_StripPlotDialog, text_extract_TextExtractDialog, transform_TransformDataDialog, treemap_TreemapDialog, tree_regression_BaseTreeRegressionDialog, ttest_TTestDialog, type_convert_TypeConvertDialog, violinplot_ViolinPlotDialog [EXTRACTED 1.00]
- **Tree Regression Dialogs** — tree_regression_DecisionTreeRegressorDialog, tree_regression_RandomForestRegressorDialog, tree_regression_LinearRegressionMLDialog, tree_regression_RidgeDialog, tree_regression_LassoDialog, tree_regression_ElasticNetDialog [EXTRACTED 1.00]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (137): AnovaModelComparisonDialog, ANOVA Model Comparison Dialog.  Allows comparing two nested OLS regression mod, Add options for the comparison., Dialog for comparing two nested OLS models via ANOVA., Add Dependent and Independent Variable selectors for two models., Bar Chart Dialog.  Generates seaborn barplot / countplot code with style prese, Dialog for creating bar charts., BaseAnalysisDialog (+129 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (89): BarChartDialog, BaseAnalysisDialog, BoxPlotDialog, ChiSquareDialog, DecisionTreeDialog, GradientBoostingDialog, KNNDialog, LDADialog (+81 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (46): ConsolePanel, Update colors and icons for the current theme., Write error message in coral red., Write warning message in amber., Write success / assumption-check result in seafoam green., Write executed command echo in teal., Write informational message., Clear all console output. (+38 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (90): QuantiaApp, QuantiaApp, Quantia Application — QApplication subclass with theme management., Customised QApplication with font loading and Fusion base style., Catch-all for any unhandled exceptions in the GUI thread., Try to load Inter and Fira Code if available on the system., Apply a QSS theme and update global state., Switch between Light and Dark themes and return the new theme. (+82 more)

### Community 4 - "Community 4"
Cohesion: 0.02
Nodes (43): ConcatColsDialog, Concatenate Columns Dialog.  Joins two or more columns together with a specifi, Dialog for concatenating columns., FindReplaceDialog, Find & Replace Dialog.  Replaces string substrings in a column, optionally usi, Dialog for Find & Replace in string columns., IfElseDialog, If / Else (Conditional) Dialog.  Creates a new column based on a logical condi (+35 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (67): Report Canvas View and Scene (DTP Style)., Interactive view for the report canvas., Scene managing free-positioned report blocks on discrete pages., ReportCanvasScene, ReportCanvasView, Binding, BindingKind, Block (+59 more)

### Community 6 - "Community 6"
Cohesion: 0.03
Nodes (79): ReportCanvasScene, ReportCanvasView, CommandPaletteDialog, Command Palette — floating fuzzy search for application actions., Floating, frameless search dialog for running commands., DataViewWidget, ShiftScrollFilter, WorkflowEngine (+71 more)

### Community 7 - "Community 7"
Cohesion: 0.03
Nodes (38): Density2DPlotDialog, 2D Density / Hexbin Plot Dialog.  Generates seaborn kdeplot or matplotlib hexb, Dialog for creating 2D Density and Hexbin plots., Generate the Python code to run the logistic regression., PairPlotDialog, Pair Plot Dialog.  Generates seaborn pairplot code with style presets. Suppor, Dialog for creating pair plots / scatterplot matrices., PieChartDialog (+30 more)

### Community 8 - "Community 8"
Cohesion: 0.03
Nodes (27): Execution engine for Workflow Builder., Traverses a workflow scene and executes logic nodes., Extract all BaseLogicNodes from the scene., Perform topological sort on the nodes., Execute the DAG and return the full script., WorkflowEngine, Quantia dockable panel widgets., EdgeItem (+19 more)

### Community 9 - "Community 9"
Cohesion: 0.03
Nodes (63): AnovaModelComparisonDialog, BarChartDialog, BaseAnalysisDialog, BoxPlotDialog, ChiSquareDialog, BaseClassificationDialog, DecisionTreeDialog, GradientBoostingDialog (+55 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (26): get_cuda_version(), get_gpu_info(), is_nvidia_gpu_available(), GPU detection and hardware discovery utilities., Get the name of the first detected NVIDIA GPU., Attempt to extract the CUDA version from nvidia-smi., Check if an NVIDIA GPU is present and accessible via nvidia-smi.     This is the, QObject (+18 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (21): dataframe(), PandasTableModel — bridges a pandas DataFrame to QTableView.  Provides an Exce, dummy_df(), show_result(), test_chisquare_logic(), test_nonparametric_logic(), test_ttest_logic(), test_workspace_clear() (+13 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (13): from_dict(), from_json(), PlotBlock, Data models for the Report Maker., Base class for all report components., A block of custom text., A block containing a plot., A block containing a data table or statistical summary. (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.2
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (7): Block, Document, Page, ReportGenerator, ReportBlock, ReportConfig, ReportSerializer

### Community 16 - "Community 16"
Cohesion: 0.4
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (2): mock_qmessagebox(), Prevent QMessageBox from popping up and hanging tests.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): Logistic Regression Dialog.  Allows selecting a binary dependent variable (Y)

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (2): PLOT_STYLES, PLOTLY_STYLES

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (2): ScriptWorker, WorkerSignals

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (2): Polars Backend, Faster reads, lower memory, lazy evaluation

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (2): PySide6 Framework, Native look-and-feel, LGPL

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (2): HTML Results Output, Styled consistently, discoverable by report, theme-aware

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (2): Contributor Covenant 2.1, Quantia Code of Conduct

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Load a workspace from a .quantia zip archive.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): Execute the code in a background thread.

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): PandasTableModel

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): Workspace

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): ResizeHandle

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): CommandPaletteDialog

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): UserManualDialog

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): GuidedWizardDialog

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): ReportDialog

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Checkmark Icon

## Knowledge Gaps
- **180 isolated node(s):** `PandasTableModel — bridges a pandas DataFrame to QTableView.  Provides an Exce`, `Table model backed by a pandas DataFrame.     Implements virtual-windowing for`, `Replace the entire DataFrame and refresh the view.`, `Return metadata for each column (for the variable list panel).`, `Manages application settings using QSettings.` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (2 nodes): `process_file()`, `patch_dialogs.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `Logistic Regression Dialog.  Allows selecting a binary dependent variable (Y)`, `logistic_regression.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `fix_plotly.py`, `patch_dialogs.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `PLOT_STYLES`, `PLOTLY_STYLES`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `ScriptWorker`, `WorkerSignals`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `Polars Backend`, `Faster reads, lower memory, lazy evaluation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `PySide6 Framework`, `Native look-and-feel, LGPL`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `HTML Results Output`, `Styled consistently, discoverable by report, theme-aware`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `Contributor Covenant 2.1`, `Quantia Code of Conduct`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `check_fonts.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `check_heros_name.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `final_font_check.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `fix_plotly.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `install_fonts.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `install_heros.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `test.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Load a workspace from a .quantia zip archive.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `Execute the code in a background thread.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `PandasTableModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `Workspace`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `test_stats_dialogs.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `check_fonts.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `install_fonts.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `install_heros.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `final_font_check.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `check_heros_name.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `ResizeHandle`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `CommandPaletteDialog`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `UserManualDialog`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `GuidedWizardDialog`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `ReportDialog`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Checkmark Icon`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MainWindow` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.209) - this node is a cross-community bridge._
- **Why does `BaseAnalysisDialog` connect `Community 0` to `Community 1`, `Community 3`, `Community 4`, `Community 7`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `Theme` connect `Community 3` to `Community 0`, `Community 8`, `Community 2`, `Community 5`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 165 inferred relationships involving `BaseAnalysisDialog` (e.g. with `AnovaModelComparisonDialog` and `ANOVA Model Comparison Dialog.  Allows comparing two nested OLS regression mod`) actually correct?**
  _`BaseAnalysisDialog` has 165 INFERRED edges - model-reasoned connections that need verification._
- **Are the 88 inferred relationships involving `MainWindow` (e.g. with `Quantia entry point.  Usage:     python -m quantia     quantia  (if installed vi` and `Launch the Quantia application.`) actually correct?**
  _`MainWindow` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 91 inferred relationships involving `Theme` (e.g. with `QuantiaApp` and `Quantia Application — QApplication subclass with theme management.`) actually correct?**
  _`Theme` has 91 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `BaseLogicNode` (e.g. with `WorkflowEngine` and `Execution engine for Workflow Builder.`) actually correct?**
  _`BaseLogicNode` has 49 INFERRED edges - model-reasoned connections that need verification._