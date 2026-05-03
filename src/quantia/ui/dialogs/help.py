"""Help dialogs — User Manual and Guided Analysis Wizard."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
)


_USER_MANUAL_HTML = """\
<div style="text-align:center; margin-bottom:8px;">
<img src="quantia_logo" width="64" height="64">
</div>
<h1 style="color:#0F172A; border-bottom:3px solid #3B82F6; padding-bottom:8px; text-align:center;">
Quantia User Manual</h1>
<p style="color:#64748B; text-align:center;">Version 0.1.0 &nbsp;|&nbsp; Fully Offline Statistical Desktop Application</p>

<hr>
<h2>1 &mdash; Overview</h2>
<p>Quantia is a no-code statistical and machine-learning workbench. Every action
you perform through the GUI is automatically translated into reproducible Python
code. All computation runs locally &mdash; no internet or cloud services required.</p>

<h3>Application Layout</h3>
<table>
<tr><th>Area</th><th>Description</th></tr>
<tr><td><b>Menu Bar</b></td><td>File, Edit, Data, Statistics, Machine Learning, Visualize, Report, Help</td></tr>
<tr><td><b>Toolbar</b></td><td>Quick-access buttons: New, Open, Save, Undo, Redo, Import Data, Run Script</td></tr>
<tr><td><b>Variable Panel</b> (left dock)</td><td>Lists all columns in the active dataset. Click a variable to see a quick summary in the Console.</td></tr>
<tr><td><b>Central Tabs</b></td><td><b>Data View</b> (spreadsheet), <b>Script Editor</b> (Python code), <b>Results</b> (test output tables), <b>Workflow</b>, <b>Plots</b> (charts)</td></tr>
<tr><td><b>Console</b> (bottom dock)</td><td>Shows command log, success/error messages, and variable summaries</td></tr>
<tr><td><b>Status Bar</b></td><td>Dataset dimensions, progress indicator during long operations</td></tr>
</table>

<hr>
<h2>2 &mdash; File Menu</h2>

<h3>2.1 Project Management</h3>
<p>Quantia uses <code>.quantia</code> archive files to persist your workflow across sessions.</p>
<ul>
<li><code>New Project (Ctrl+N)</code>: Clears the current dataset, script, and undo/redo history to start fresh.</li>
<li><code>Open Project... (Ctrl+O)</code>: Loads a saved <code>.quantia</code> file. The dataset is restored, the script is loaded, and Quantia automatically re-runs the code to repopulate your results and plots.</li>
<li><code>Save Project (Ctrl+S)</code>: Packages your current dataset (as Parquet), your script, and your undo history into a compact <code>.quantia</code> archive.</li>
<li><code>Save Project As... (Ctrl+Shift+S)</code>: Saves the current project to a new location.</li>
</ul>

<h3>2.2 Importing Data</h3>
<p><code>File &rarr; Import Data &rarr; ...</code></p>
<table>
<tr><th>Format</th><th>Extensions</th><th>Notes</th></tr>
<tr><td>CSV</td><td>.csv</td><td>Uses <code>pd.read_csv()</code> with <code>low_memory=False</code></td></tr>
<tr><td>Excel</td><td>.xls, .xlsx</td><td>Uses <code>pd.read_excel()</code>; reads the first sheet</td></tr>
<tr><td>JSON</td><td>.json</td><td>Uses <code>pd.read_json()</code>; expects records or columnar format</td></tr>
<tr><td>Parquet</td><td>.parquet</td><td>Uses <code>pd.read_parquet()</code>; requires <code>pyarrow</code></td></tr>
</table>
<p>The toolbar <b>Import Data</b> button opens a combined dialog that auto-detects format by extension.</p>

<h3>2.3 Exporting Data</h3>
<p><code>File &rarr; Export Data&hellip;</code></p>
<p>Save the current (possibly transformed) DataFrame to CSV, Excel (.xlsx), JSON, or Parquet.
The format is determined by the file extension you choose in the Save dialog.</p>

<h3>2.4 Exit</h3>
<p><code>Ctrl+Q</code> or <code>File &rarr; Exit</code></p>

<hr>
<h2>3 &mdash; Edit Menu</h2>
<table>
<tr><th>Action</th><th>Shortcut</th><th>Description</th></tr>
<tr><td>Undo</td><td>Ctrl+Z</td><td>Reverts the last data-modifying operation (clean, transform, filter, merge)</td></tr>
<tr><td>Redo</td><td>Ctrl+Y</td><td>Re-applies the last undone operation</td></tr>
</table>
<p><b>Note:</b> Undo/Redo apply to <i>data changes</i> only (not script edits).</p>

<hr>
<h2>4 &mdash; Data Menu</h2>

<h3>4.1 Clean Data</h3>
<p><code>Data &rarr; Clean Data&hellip;</code></p>
<ul>
<li><b>Drop Rows with NA</b> &mdash; Remove rows containing any missing values</li>
<li><b>Drop Columns</b> &mdash; Select specific columns to remove from the dataset</li>
<li><b>Impute Missing Values</b> &mdash; Fill NAs with mean, median, mode, or a constant</li>
</ul>

<h3>4.2 Transform Data</h3>
<p><code>Data &rarr; Transform Data (Math)&hellip;</code></p>
<ul>
<li>Apply mathematical transformations: log, sqrt, square, reciprocal, z-score, min-max scale</li>
<li>Create new computed columns from expressions</li>
</ul>

<h3>4.3 Type &amp; String Conversion</h3>
<p><code>Data &rarr; Type &amp; String Conversion&hellip;</code></p>
<ul>
<li>Cast columns to int, float, string, datetime, or category</li>
<li>String operations: uppercase, lowercase, strip whitespace, extract patterns</li>
</ul>

<h3>4.4 Filter Data</h3>
<p><code>Data &rarr; Filter Data (Subset Rows)&hellip;</code></p>
<ul>
<li>Filter rows using conditions (equals, not equals, greater than, contains, etc.)</li>
<li>Combine multiple conditions with AND/OR logic</li>
</ul>

<h3>4.5 Merge / Join</h3>
<p><code>Data &rarr; Merge / Join&hellip;</code></p>
<ul>
<li>Import a second dataset and join it with the current one</li>
<li>Supports inner, left, right, and outer joins on selected key columns</li>
</ul>

<h3>4.6 Pivot Table / Group-By</h3>
<p><code>Data &rarr; Pivot Table / Group By&hellip;</code></p>
<ul>
<li>Aggregate values by categorical columns (Sum, Mean, Count, etc.)</li>
<li>Optionally pivot a column to create a cross-tabulated table</li>
<li>Choose to display the result or replace the current dataset</li>
</ul>

<hr>
<h2>5 &mdash; Statistics Menu</h2>

<h3>5.1 Descriptive Statistics</h3>
<p>Generates count, mean, std, min, quartiles, max for selected numeric columns.
Also shows skewness, kurtosis, and missing-value counts.</p>

<h3>5.2 t-test</h3>
<table>
<tr><th>Type</th><th>Use When</th></tr>
<tr><td>Independent two-sample</td><td>Comparing means of two separate groups</td></tr>
<tr><td>Paired</td><td>Comparing before/after measurements on the same subjects</td></tr>
<tr><td>One-sample</td><td>Testing a sample mean against a known value</td></tr>
</table>
<p>Reports: t-statistic, p-value, degrees of freedom, confidence interval, effect size (Cohen's d).</p>

<h3>5.3 ANOVA</h3>
<p>One-way Analysis of Variance for comparing means across 3+ groups.
Reports: F-statistic, p-value, sum of squares, and optional post-hoc tests (Tukey HSD).</p>

<h3>5.4 Non-parametric Tests</h3>
<ul>
<li><b>Mann-Whitney U</b> &mdash; Non-parametric alternative to the independent t-test</li>
<li><b>Wilcoxon Signed-Rank</b> &mdash; Non-parametric alternative to the paired t-test</li>
<li><b>Kruskal-Wallis</b> &mdash; Non-parametric alternative to one-way ANOVA</li>
</ul>
<p>Use these when data is ordinal or not normally distributed.</p>

<h3>5.5 Correlation</h3>
<ul>
<li><b>Pearson</b> &mdash; Linear correlation (requires normality)</li>
<li><b>Spearman</b> &mdash; Rank-based correlation (no normality assumption)</li>
<li><b>Kendall</b> &mdash; Rank correlation, robust to ties</li>
</ul>
<p>Generates a correlation matrix with optional heatmap visualization and p-value matrix.</p>

<h3>5.6 Chi-square Test</h3>
<p>Tests for independence between two categorical variables using a contingency table.
Reports: &chi;&sup2; statistic, p-value, degrees of freedom, Cram&eacute;r's V effect size, expected frequencies.</p>

<hr>
<h2>6 &mdash; Machine Learning Menu</h2>

<h3>6.1 Regression</h3>
<h4>Linear Regression</h4>
<ul>
<li>Select a dependent (Y) variable and one or more independent (X) variables</li>
<li><b>Stepwise Selection</b>: Forward, Backward, or Both &mdash; automatically selects the best predictors using AIC</li>
<li>Categorical variables are automatically dummy-coded and treated as block groups in stepwise selection</li>
<li>Reports: R&sup2;, Adj. R&sup2;, F-statistic, AIC, BIC, coefficient table with significance stars</li>
<li>Generates: residual plot, Q-Q plot of residuals, predicted vs actual plot</li>
</ul>

<h4>Logistic Regression</h4>
<ul>
<li>Binary classification via logistic regression</li>
<li><b>Stepwise Selection</b>: Same forward/backward/both methods as linear regression</li>
<li>Reports: pseudo-R&sup2;, AIC, BIC, odds ratios, coefficient table</li>
<li>Generates: ROC curve with AUC, confusion matrix, classification report</li>
</ul>

<h3>6.2 Classification (Supervised)</h3>
<p>All classifiers share a common workflow:</p>
<ol>
<li>Select target variable (categorical/binary) and feature columns</li>
<li>Set train/test split ratio (default 70/30)</li>
<li>Configure algorithm-specific hyperparameters</li>
<li>View results: accuracy, confusion matrix, classification report, ROC curve</li>
</ol>
<p><b>Model Comparison:</b> <code>ML &rarr; Classification &rarr; Compare Models...</code> lets you run up to 8 models simultaneously and view a ranked metrics table (Accuracy, F1, AUC, etc.) alongside an overlapping ROC curve plot.</p>

<table>
<tr><th>Algorithm</th><th>Key Parameters</th><th>Notes</th></tr>
<tr><td><b>Random Forest</b></td><td>n_estimators, max_depth</td><td>Ensemble of decision trees; shows feature importance</td></tr>
<tr><td><b>Gradient Boosting</b></td><td>n_estimators, learning_rate, max_depth</td><td>Sequential boosting; shows feature importance</td></tr>
<tr><td><b>Decision Tree</b></td><td>max_depth, min_samples_split</td><td>Single tree; shows feature importance</td></tr>
<tr><td><b>SVM</b></td><td>C, kernel (rbf/linear/poly)</td><td><b>Mandatory StandardScaler</b> (auto-applied)</td></tr>
<tr><td><b>KNN</b></td><td>n_neighbors, weights, metric</td><td><b>Mandatory StandardScaler</b> (auto-applied)</td></tr>
<tr><td><b>LDA</b></td><td>solver</td><td>Linear Discriminant Analysis; optional scaling</td></tr>
<tr><td><b>QDA</b></td><td>&mdash;</td><td>Quadratic Discriminant Analysis; optional scaling</td></tr>
<tr><td><b>Naive Bayes</b></td><td>var_smoothing</td><td>Gaussian Naive Bayes; optional scaling</td></tr>
</table>

<h3>6.3 Dimensionality Reduction</h3>
<p><code>ML &rarr; Dimensionality Reduction &rarr; Principal Component Analysis (PCA)&hellip;</code></p>
<ul>
<li>Reduces the number of features while retaining variance</li>
<li>Generates Scree plot, Biplot (first 2 components), and Explained Variance table</li>
<li>Optionally appends the calculated Principal Components (PC1, PC2...) back to the dataset</li>
</ul>

<h3>6.4 Clustering (Unsupervised)</h3>
<p>All clustering methods share a common workflow:</p>
<ol>
<li>Select feature columns (numeric only)</li>
<li>Configure algorithm parameters</li>
<li>View: cluster scatter plot (auto-PCA if &gt;2 features), cluster profile table, silhouette score</li>
<li>Optionally append cluster labels to the dataset</li>
</ol>

<table>
<tr><th>Algorithm</th><th>Key Parameters</th><th>Notes</th></tr>
<tr><td><b>K-Means</b></td><td>n_clusters, max_iter</td><td>Partitions data into K spherical clusters</td></tr>
<tr><td><b>Hierarchical</b></td><td>n_clusters, linkage method</td><td>Generates a dendrogram; supports ward, complete, average, single</td></tr>
<tr><td><b>DBSCAN</b></td><td>eps, min_samples</td><td>Density-based; finds arbitrary shapes; labels outliers as -1</td></tr>
<tr><td><b>GMM</b></td><td>n_components, covariance_type</td><td>Gaussian Mixture Model; soft probabilistic clustering</td></tr>
</table>

<hr>
<h2>7 &mdash; Visualize Menu</h2>
<table>
<tr><th>Chart</th><th>Best For</th><th>Required Inputs</th></tr>
<tr><td><b>Histogram</b></td><td>Distribution of a single numeric variable</td><td>1 numeric column, optional bins count</td></tr>
<tr><td><b>Box Plot</b></td><td>Spread, median, outliers; comparing groups</td><td>1 numeric column, optional grouping column</td></tr>
<tr><td><b>Scatter Plot</b></td><td>Relationship between two numeric variables</td><td>2 numeric columns, optional hue column</td></tr>
<tr><td><b>Violin Plot</b></td><td>Distribution shape + box plot combined</td><td>1 numeric column, optional grouping column</td></tr>
<tr><td><b>Q-Q Plot</b></td><td>Checking if data follows a normal distribution</td><td>1 numeric column</td></tr>
<tr><td><b>Line Chart</b></td><td>Trends over an ordered axis (e.g. time)</td><td>X column + 1 or more Y columns</td></tr>
<tr><td><b>Bar Chart</b></td><td>Comparing values across categories</td><td>1 categorical column, 1 numeric column</td></tr>
<tr><td><b>Heatmap</b></td><td>Visualizing correlation matrices or pivot tables</td><td>Multiple numeric columns</td></tr>
</table>
<p>All plots appear in the <b>Plots</b> tab. Each plot generates the equivalent Matplotlib code in the Script Editor.</p>

<hr>
<h2>8 &mdash; Report Menu</h2>

<h3>8.1 Generate Report</h3>
<p><code>Report &rarr; Generate Report (HTML/PDF)&hellip;</code></p>
<ul>
<li>Set a custom report title</li>
<li>Choose which sections to include: Dataset Summary, Python Script, Statistical Results</li>
<li><b>HTML</b> &mdash; Professional styled document viewable in any browser</li>
<li><b>PDF</b> &mdash; Uses Microsoft Edge (headless) for browser-quality rendering. Falls back to Chrome if Edge is unavailable.</li>
<li>Each major section starts on a new page in the PDF</li>
<li>The Dataset Summary table is transposed (variables as rows) for readability</li>
</ul>

<h3>8.2 Export Script</h3>
<p><code>Report &rarr; Export Script (.py)&hellip;</code></p>
<p>Saves the entire contents of the Script Editor tab as a standalone <code>.py</code> file.
This file can be run independently with <code>python script.py</code> (requires the same packages).</p>

<hr>
<h2>9 &mdash; Script Editor</h2>
<p>The Script Editor tab shows all auto-generated Python code from your GUI actions.</p>

<h3>Features</h3>
<ul>
<li><b>Syntax Highlighting</b> &mdash; Python keywords, strings, comments, numbers, decorators</li>
<li><b>Line Numbers</b> &mdash; Displayed in the left gutter</li>
<li><b>Auto-indentation</b> &mdash; Maintains indent level on Enter</li>
<li><b>Editable</b> &mdash; You can modify or add your own code</li>
</ul>

<h3>Running Code</h3>
<table>
<tr><th>Action</th><th>Shortcut</th><th>Description</th></tr>
<tr><td>Run All</td><td>F5</td><td>Executes the entire script from top to bottom</td></tr>
<tr><td>Run Selection</td><td>Ctrl+Enter</td><td>Executes only the selected/highlighted lines</td></tr>
</table>
<p>The code runs in an environment with <code>df</code> (the current DataFrame), <code>pd</code>, <code>np</code>,
<code>plt</code>, <code>sns</code>, <code>scipy.stats</code>, and <code>sklearn</code> pre-imported.
Any changes to <code>df</code> will update the Data View.</p>

<hr>
<h2>10 &mdash; Console Panel</h2>
<p>The bottom Console panel shows:</p>
<ul>
<li><span style="color:#1E40AF;"><b>Commands</b></span> (blue) &mdash; The Python equivalent of each GUI action</li>
<li><span style="color:#16A34A;"><b>Success</b></span> (green) &mdash; Confirmation messages (rows loaded, export complete, etc.)</li>
<li><span style="color:#DC2626;"><b>Errors</b></span> (red) &mdash; Exception messages and tracebacks</li>
<li><span style="color:#64748B;"><b>Info</b></span> (gray) &mdash; Variable summaries, status updates</li>
</ul>

<hr>
<h2>11 &mdash; Keyboard Shortcuts</h2>
<table>
<tr><th>Shortcut</th><th>Action</th></tr>
<tr><td>Ctrl+Q</td><td>Exit Quantia</td></tr>
<tr><td>Ctrl+Z</td><td>Undo data change</td></tr>
<tr><td>Ctrl+Y</td><td>Redo data change</td></tr>
<tr><td>F5</td><td>Run entire script</td></tr>
<tr><td>Ctrl+Enter</td><td>Run selected code</td></tr>
</table>

<hr>
<h2>12 &mdash; Tips &amp; Best Practices</h2>
<ul>
<li><b>Check your data first:</b> Use Descriptive Statistics and histograms before running tests.</li>
<li><b>Normality matters:</b> Use Q-Q plots to check normality. Choose non-parametric tests if violated.</li>
<li><b>Scale when needed:</b> SVM and KNN auto-scale. For other classifiers, tick the StandardScaler checkbox if features have very different ranges.</li>
<li><b>Stepwise with caution:</b> Stepwise variable selection is a convenience tool, not a substitute for domain knowledge. Always review selected variables.</li>
<li><b>PCA in clustering:</b> When clustering with &gt;2 features, Quantia auto-applies PCA for the scatter plot only. The actual clustering uses all original features.</li>
<li><b>Reproducibility:</b> The Script Editor captures everything. Export it with <code>Report &rarr; Export Script</code> to share or re-run later.</li>
<li><b>Large datasets:</b> Parquet format is fastest for large files (&gt;100K rows). Use it for import and export when possible.</li>
</ul>

"""


_WIZARD_HTML = """\
<h2>Guided Analysis Wizard</h2>
<p>Follow these steps for a typical statistical analysis workflow:</p>

<h3>Step 1: Load Your Data</h3>
<p>Go to <code>File → Import Data</code> and select your dataset.
Check the <b>Data View</b> tab to confirm it loaded correctly.</p>

<h3>Step 2: Explore & Clean</h3>
<p>Click variables in the left panel to see summaries.
Use <code>Data → Clean Data</code> to handle missing values.
Create visualizations from the <code>Visualize</code> menu (histograms, box plots, scatter plots).</p>

<h3>Step 3: Choose Your Analysis</h3>
<table>
    <tr><th>Your Goal</th><th>Where to Go</th></tr>
    <tr><td>Compare group means</td><td><code>Statistics → t-test</code> or <code>ANOVA</code></td></tr>
    <tr><td>Test variable relationships</td><td><code>Statistics → Correlation</code></td></tr>
    <tr><td>Test categorical associations</td><td><code>Statistics → Chi-square</code></td></tr>
    <tr><td>Predict a continuous outcome</td><td><code>ML → Regression → Linear</code></td></tr>
    <tr><td>Predict a binary outcome</td><td><code>ML → Regression → Logistic</code></td></tr>
    <tr><td>Classify into categories</td><td><code>ML → Classification</code> (pick an algorithm)</td></tr>
    <tr><td>Find natural groups in data</td><td><code>ML → Clustering</code> (pick an algorithm)</td></tr>
</table>

<h3>Step 4: Review Results</h3>
<p>Check the <b>Results</b> tab for tables and metrics.
Check the <b>Plots</b> tab for visualizations.
Review the <b>Script Editor</b> tab for the generated Python code.</p>

<h3>Step 5: Export</h3>
<p>Go to <code>Report → Generate Report</code> for a professional HTML or PDF summary.
Use <code>Report → Export Script</code> to save the reproducible Python code.
Use <code>File → Export Data</code> to save your modified dataset.</p>
"""


class UserManualDialog(QDialog):
    """Scrollable user manual dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("User Manual — Quantia")
        self.setMinimumSize(720, 600)
        self.resize(780, 700)

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)

        # Load logo into the document's resource cache
        logo_path = Path(__file__).parent.parent.parent.parent.parent / "reference" / "logo" / "69e99e05-da76-4624-b75e-3f64158aa657_removalai_preview.png"
        if logo_path.exists():
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QImage, QTextDocument
            img = QImage(str(logo_path))
            browser.document().addResource(
                QTextDocument.ResourceType.ImageResource,
                QUrl("quantia_logo"),
                img,
            )

        browser.setHtml(_USER_MANUAL_HTML)
        browser.setStyleSheet("QTextBrowser { background: #fff; padding: 16px; border: none; }")
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)


class GuidedWizardDialog(QDialog):
    """Step-by-step analysis guide dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Guided Analysis Wizard — Quantia")
        self.setMinimumSize(600, 520)

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(_WIZARD_HTML)
        browser.setStyleSheet("QTextBrowser { background: #fff; padding: 16px; border: none; }")
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
