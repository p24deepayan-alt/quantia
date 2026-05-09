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
<p style="color:#64748B; text-align:center;">Version 0.9.0-beta &nbsp;|&nbsp; Fully Offline Statistical &amp; Machine Learning Desktop Application</p>

<hr>
<h2>1 &mdash; Overview</h2>
<p>Quantia is a no-code statistical and machine-learning workbench. Every action
you perform through the GUI is automatically translated into reproducible Python
code. All computation runs locally &mdash; no internet or cloud services required.
Quantia uses <b>Polars</b> as its primary high-performance data backend, with
seamless <b>Pandas</b> interop for libraries that require it.</p>

<h3>1.1 Application Layout</h3>
<table>
<tr><th>Area</th><th>Description</th></tr>
<tr><td><b>Menu Bar</b></td><td>File, Edit, View, Data, Statistics, Machine Learning, Visualize, Report, Help</td></tr>
<tr><td><b>Toolbar</b></td><td>Quick-access buttons: Open, Save, Undo, Redo, Import Data, Run Script, Toggle Theme, Preferences</td></tr>
<tr><td><b>Variable Panel</b> (left dock)</td><td>Lists all columns in the active dataset with type icons (&num; numeric, Abc text, date). Click a variable to see a quick summary in the Console.</td></tr>
<tr><td><b>Central Tabs</b></td><td><b>Data View</b> (spreadsheet), <b>Script Editor</b> (Python code), <b>Results</b> (HTML test output), <b>Workflow</b> (visual node builder), <b>Plots</b> (Matplotlib charts), <b>Dashboard Builder</b> (interactive layout)</td></tr>
<tr><td><b>Console</b> (bottom dock)</td><td>Shows colour-coded output: <span style="color:#1E40AF;"><b>commands</b></span> (blue), <span style="color:#16A34A;"><b>success</b></span> (green), <span style="color:#DC2626;"><b>errors</b></span> (red), <span style="color:#64748B;"><b>info</b></span> (gray)</td></tr>
<tr><td><b>Status Bar</b></td><td>Dataset dimensions (rows &times; columns), compute mode (CPU single/multi), progress indicator</td></tr>
</table>

<h3>1.2 Supported Data Formats</h3>
<table>
<tr><th>Format</th><th>Extensions</th><th>Import Method</th></tr>
<tr><td>CSV</td><td>.csv</td><td><code>polars.read_csv()</code> with robust encoding detection (UTF-8, CP1252, Latin-1, auto-detect via charset_normalizer)</td></tr>
<tr><td>Excel</td><td>.xls, .xlsx</td><td><code>pandas.read_excel()</code> converted to Polars; reads the first sheet</td></tr>
<tr><td>JSON</td><td>.json</td><td><code>polars.read_json()</code>; expects records or columnar format</td></tr>
<tr><td>Parquet</td><td>.parquet</td><td><code>polars.read_parquet()</code>; fastest format for large files (&gt;100K rows)</td></tr>
</table>

<h3>1.3 Project Files</h3>
<p>Quantia saves sessions as <code>.quantia</code> archive files (ZIP format) containing:</p>
<ul>
<li><b>data.parquet</b> &mdash; Your dataset in compressed columnar format</li>
<li><b>script.py</b> &mdash; All auto-generated Python code</li>
<li><b>metadata.json</b> &mdash; Project name, timestamps, settings</li>
<li><b>undo_history/</b> &mdash; Snapshots for undo/redo (up to 50 states)</li>
</ul>

<hr>
<h2>2 &mdash; Workflow Builder</h2>
<p>The <b>Workflow</b> tab provides a visual node-based interface for building analysis pipelines.
This is ideal for creating reproducible, multi-step processes where you can see the flow of data.</p>

<h3>2.1 Working with Nodes</h3>
<ul>
<li><b>Right-click</b> on the canvas to add nodes from categorized menus (I/O, Processing, Statistics, Machine Learning, Visualization, Reporting).</li>
<li><b>Connect</b> nodes by clicking an <b>output port</b> (right side) and dragging a wire to an <b>input port</b> (left side).</li>
<li><b>Double-click</b> a node to configure its parameters (ensure it is connected to a data source first).</li>
<li><b>Run Pipeline:</b> Click the Run button to execute the entire graph in topological order.</li>
<li><b>Persistence:</b> Workflow designs are saved automatically as part of your <code>.quantia</code> project file.</li>
</ul>

<h3>2.2 Available Node Types</h3>
<table>
<tr><th>Category</th><th>Nodes</th></tr>
<tr><td><b>I/O</b></td><td>Load CSV, Export CSV</td></tr>
<tr><td><b>Processing</b></td><td>Clean Data (drop/fill NAs)</td></tr>
<tr><td><b>Statistics</b></td><td>Descriptive Stats, T-Test, Correlation, Chi-Square</td></tr>
<tr><td><b>Machine Learning</b></td><td>PCA, Regression (Linear, Decision Tree, Random Forest), Classification (RF, Gradient Boosting, DT, SVM, KNN, LDA, QDA, Naive Bayes), Clustering (K-Means, Hierarchical, DBSCAN, GMM)</td></tr>
<tr><td><b>Visualization</b></td><td>Histogram, Box Plot, Scatter Plot, Bar Chart, Heatmap, Line Chart, Violin Plot, Q-Q Plot</td></tr>
<tr><td><b>Reporting</b></td><td>Save Report (HTML summary)</td></tr>
</table>

<h3>2.3 Pipeline Execution</h3>
<p>The workflow engine performs a <b>topological sort</b> of connected nodes to determine execution order.
Each node receives data from its upstream connections and passes transformed data downstream.
Errors in any node are reported in the Console without stopping the rest of the pipeline.</p>

<hr>
<h2>3 &mdash; File Menu</h2>

<h3>3.1 Project Management</h3>
<table>
<tr><th>Action</th><th>Shortcut</th><th>Description</th></tr>
<tr><td>Open Project&hellip;</td><td>Ctrl+O</td><td>Loads a saved <code>.quantia</code> file. Dataset is restored, script is loaded, and Quantia automatically re-runs the code to repopulate results and plots.</td></tr>
<tr><td>Save Project</td><td>Ctrl+S</td><td>Packages your current dataset (as Parquet), script, and undo history into a compact <code>.quantia</code> archive. If no path set, prompts Save As.</td></tr>
<tr><td>Save Project As&hellip;</td><td>Ctrl+Shift+S</td><td>Saves the current project to a new file location.</td></tr>
</table>

<h3>3.2 Importing Data</h3>
<p><code>File &rarr; Import Data &rarr; ...</code></p>
<p>Choose a specific format (CSV, Excel, JSON, Parquet) from the submenu, or use the toolbar
<b>Import Data</b> button which auto-detects format by file extension.</p>
<p><b>CSV Encoding:</b> Quantia uses a multi-pass encoding strategy: UTF-8 first, then CP1252,
then auto-detection via <code>charset_normalizer</code>, and finally Latin-1 as a last resort.
This handles virtually all CSV files without manual encoding selection.</p>

<h3>3.3 Exporting Data</h3>
<p><code>File &rarr; Export Data&hellip;</code></p>
<p>Save the current (possibly transformed) DataFrame to CSV, Excel (.xlsx), JSON, or Parquet.
The format is determined by the file extension you choose in the Save dialog.</p>

<h3>3.4 Auto-Save</h3>
<p>Quantia automatically saves a temporary backup of your workspace every <b>5 minutes</b>
to <code>.temp.quantia</code> in the workspaces directory. This protects against data loss from crashes.</p>

<h3>3.5 Exit</h3>
<p><code>Ctrl+Q</code> or <code>File &rarr; Exit</code></p>

<hr>
<h2>4 &mdash; Edit &amp; View Menus</h2>

<h3>4.1 Undo / Redo</h3>
<table>
<tr><th>Action</th><th>Shortcut</th><th>Description</th></tr>
<tr><td>Undo</td><td>Ctrl+Z</td><td>Reverts the last data-modifying operation (clean, transform, filter, merge, etc.)</td></tr>
<tr><td>Redo</td><td>Ctrl+Y</td><td>Re-applies the last undone operation</td></tr>
</table>
<p><b>Note:</b> Undo/Redo apply to <i>data changes</i> only (not script edits). Up to 50 snapshots are kept in memory.</p>

<h3>4.2 Preferences</h3>
<p><code>Edit &rarr; Preferences</code> opens a settings dialog with:</p>
<ul>
<li><b>Compute Backend</b> &mdash; Choose between CPU single-core (sequential) or CPU multi-core (parallel). The status bar displays the active mode.</li>
</ul>

<h3>4.3 Toggle Theme</h3>
<p><code>View &rarr; Toggle Light/Dark Mode</code> switches between the Light and Dark themes.
All UI components, tab icons, Matplotlib plot styles, the workflow canvas, and the console
adapt automatically. The toolbar also has a quick-toggle button.</p>
<hr>
<h2>5 &mdash; Data Menu</h2>

<h3>5.1 Clean Data</h3>
<p><code>Data &rarr; Clean Data (Drop NA, Drop Cols, Impute)&hellip;</code></p>
<table>
<tr><th>Operation</th><th>Description</th></tr>
<tr><td><b>Drop Rows with NA</b></td><td>Remove all rows containing any missing values from the dataset</td></tr>
<tr><td><b>Drop Columns</b></td><td>Select specific columns to permanently remove from the dataset</td></tr>
<tr><td><b>Impute Missing Values</b></td><td>Fill NAs with one of: <b>mean</b>, <b>median</b>, <b>mode</b>, or a <b>constant value</b> you specify</td></tr>
</table>
<p>A preview of the changes is shown before applying. All operations generate reproducible Python code.</p>

<h3>5.2 Transform Data (Math)</h3>
<p><code>Data &rarr; Transform Data (Math)&hellip;</code></p>
<table>
<tr><th>Transform</th><th>Formula</th></tr>
<tr><td>Log</td><td><code>np.log(x)</code></td></tr>
<tr><td>Square Root</td><td><code>np.sqrt(x)</code></td></tr>
<tr><td>Square</td><td><code>x ** 2</code></td></tr>
<tr><td>Reciprocal</td><td><code>1 / x</code></td></tr>
<tr><td>Z-Score</td><td><code>(x - mean) / std</code></td></tr>
<tr><td>Min-Max Scale</td><td><code>(x - min) / (max - min)</code></td></tr>
</table>
<p>You can also create new computed columns from custom expressions.</p>

<h3>5.3 Type &amp; String Conversion</h3>
<p><code>Data &rarr; Type &amp; String Conversion&hellip;</code></p>
<ul>
<li>Cast columns to: <b>int</b>, <b>float</b>, <b>string</b>, <b>datetime</b>, or <b>category</b></li>
<li>Handles conversion errors gracefully with informative messages</li>
</ul>

<h3>5.4 Filter Data (Subset Rows)</h3>
<p><code>Data &rarr; Filter Data (Subset Rows)&hellip;</code></p>
<ul>
<li>Filter rows using conditions: equals, not equals, greater than, less than, contains, starts with, ends with, is null, is not null</li>
<li>Combine <b>multiple conditions</b> with AND/OR logic</li>
<li>Preview filtered row count before applying</li>
</ul>

<h3>5.5 Merge / Join</h3>
<p><code>Data &rarr; Merge / Join&hellip;</code></p>
<ul>
<li>Import a second dataset and join it with the current one</li>
<li>Join types: <b>inner</b>, <b>left</b>, <b>right</b>, <b>outer</b></li>
<li>Select matching key columns (can match by different column names)</li>
</ul>

<h3>5.6 String Operations</h3>
<p><code>Data &rarr; String Operations &rarr; ...</code></p>
<table>
<tr><th>Tool</th><th>Description</th></tr>
<tr><td><b>Text Before / After</b></td><td>Extract text before or after a delimiter character or pattern</td></tr>
<tr><td><b>Change Case &amp; Trim</b></td><td>Convert to uppercase, lowercase, title case; strip leading/trailing whitespace</td></tr>
<tr><td><b>Find &amp; Replace</b></td><td>Search for text patterns in a column and replace with new values</td></tr>
<tr><td><b>Concatenate Columns</b></td><td>Combine two or more columns into a single column with an optional separator</td></tr>
</table>

<h3>5.7 If / Else (Conditional)</h3>
<p><code>Data &rarr; If / Else (Conditional)&hellip;</code></p>
<p>Create new columns based on rule-based logic. Define conditions and assign values
for when conditions are met or not met. Supports nested rules and multiple condition groups.</p>

<h3>5.8 Pivot Table / Group-By</h3>
<p><code>Data &rarr; Pivot Table / Group By&hellip;</code></p>
<ul>
<li>Select <b>row grouping</b> columns (categorical)</li>
<li>Optionally select a <b>pivot column</b> to create cross-tabulated output</li>
<li>Choose <b>value columns</b> (numeric) and <b>aggregation functions</b>: Sum, Mean, Count, Min, Max, Std, Median</li>
<li>Choose to <b>display the result</b> in Results or <b>replace the current dataset</b></li>
</ul>

<hr>
<h2>6 &mdash; Statistics Menu</h2>

<h3>6.1 Descriptive Statistics</h3>
<p><code>Statistics &rarr; Descriptive Statistics&hellip;</code></p>
<p>Select one or more numeric columns to generate a comprehensive summary table:</p>
<ul>
<li>Count, Mean, Standard Deviation, Min, 25th percentile, Median, 75th percentile, Max</li>
<li>Skewness, Kurtosis, Missing value count and percentage</li>
</ul>
<p>Results appear in the <b>Results</b> tab as a formatted HTML table.</p>

<h3>6.2 t-test</h3>
<p><code>Statistics &rarr; t-test&hellip;</code></p>
<table>
<tr><th>Type</th><th>Use When</th><th>Required Inputs</th></tr>
<tr><td><b>Independent two-sample</b></td><td>Comparing means of two separate groups</td><td>1 numeric variable + 1 grouping variable (exactly 2 groups)</td></tr>
<tr><td><b>Paired</b></td><td>Comparing before/after measurements on the same subjects</td><td>2 numeric variables (same length)</td></tr>
<tr><td><b>One-sample</b></td><td>Testing a sample mean against a known value</td><td>1 numeric variable + hypothesized mean</td></tr>
</table>
<p><b>Reports:</b> t-statistic, p-value, degrees of freedom, 95% confidence interval, Cohen&rsquo;s d effect size.
All results include plain-language interpretation.</p>

<h3>6.3 ANOVA</h3>
<p><code>Statistics &rarr; ANOVA&hellip;</code></p>
<p>One-way Analysis of Variance for comparing means across 3 or more groups.</p>
<ul>
<li>Select a <b>dependent variable</b> (numeric) and a <b>factor variable</b> (categorical)</li>
<li>Reports: F-statistic, p-value, sum of squares, degrees of freedom</li>
<li>Optional <b>Tukey HSD post-hoc test</b> to identify which specific groups differ</li>
<li>Includes model comparison capabilities for evaluating different grouping factors</li>
</ul>

<h3>6.4 Non-parametric Tests</h3>
<p><code>Statistics &rarr; Non-parametric Tests&hellip;</code></p>
<p>Use these when data is ordinal or not normally distributed:</p>
<table>
<tr><th>Test</th><th>Use When</th><th>Parametric Equivalent</th></tr>
<tr><td><b>Mann-Whitney U</b></td><td>Comparing two independent groups (ordinal/non-normal data)</td><td>Independent t-test</td></tr>
<tr><td><b>Wilcoxon Signed-Rank</b></td><td>Comparing two related/paired measurements</td><td>Paired t-test</td></tr>
<tr><td><b>Kruskal-Wallis</b></td><td>Comparing 3+ independent groups</td><td>One-way ANOVA</td></tr>
</table>
<p>Reports: test statistic, p-value, and plain-language interpretation.</p>

<h3>6.5 Correlation</h3>
<p><code>Statistics &rarr; Correlation&hellip;</code></p>
<table>
<tr><th>Method</th><th>When to Use</th></tr>
<tr><td><b>Pearson</b></td><td>Linear correlation between normally distributed variables</td></tr>
<tr><td><b>Spearman</b></td><td>Rank-based correlation; no normality assumption needed</td></tr>
<tr><td><b>Kendall</b></td><td>Rank correlation; robust to ties and small samples</td></tr>
</table>
<p>Generates a <b>correlation matrix</b> with optional <b>heatmap visualization</b> and a separate <b>p-value matrix</b>
showing statistical significance of each correlation.</p>

<h3>6.6 Chi-square Test</h3>
<p><code>Statistics &rarr; Chi-square&hellip;</code></p>
<p>Tests for independence between two categorical variables using a contingency table.</p>
<ul>
<li>Select two categorical columns</li>
<li><b>Reports:</b> &chi;&sup2; statistic, p-value, degrees of freedom, Cram&eacute;r&rsquo;s V effect size</li>
<li>Displays the <b>observed frequencies</b> table and <b>expected frequencies</b> table</li>
<li>Plain-language interpretation of results</li>
</ul>

<hr>
<h2>7 &mdash; Machine Learning Menu</h2>

<h3>7.1 Regression</h3>
<p><code>Machine Learning &rarr; Regression &rarr; ...</code></p>

<h4>7.1.1 Linear Regression (statsmodels)</h4>
<ul>
<li>Select a dependent (Y) variable and one or more independent (X) variables</li>
<li><b>Stepwise Selection:</b> Forward, Backward, or Both &mdash; automatically selects the best predictors using AIC</li>
<li>Categorical variables are automatically dummy-coded and treated as block groups in stepwise selection</li>
<li><b>Reports:</b> R&sup2;, Adjusted R&sup2;, F-statistic, AIC, BIC, coefficient table with significance stars</li>
<li><b>Plots:</b> Residual plot, Q-Q plot of residuals, Predicted vs Actual plot</li>
</ul>

<h4>7.1.2 Linear Regression (ML / scikit-learn)</h4>
<ul>
<li>scikit-learn implementation with train/test split</li>
<li>Reports: R&sup2;, RMSE, MAE on both training and test sets</li>
</ul>

<h4>7.1.3 Logistic Regression</h4>
<ul>
<li>Binary classification via logistic regression (statsmodels)</li>
<li><b>Stepwise Selection:</b> Same forward/backward/both methods as linear regression</li>
<li><b>Reports:</b> Pseudo-R&sup2;, AIC, BIC, odds ratios, coefficient table</li>
<li><b>Plots:</b> ROC curve with AUC, confusion matrix, classification report</li>
</ul>

<h4>7.1.4 Regularized Regression</h4>
<table>
<tr><th>Algorithm</th><th>Key Parameters</th><th>Description</th></tr>
<tr><td><b>Ridge</b></td><td>alpha (regularization strength)</td><td>L2 penalty; shrinks coefficients toward zero</td></tr>
<tr><td><b>Lasso</b></td><td>alpha</td><td>L1 penalty; can drive coefficients exactly to zero (feature selection)</td></tr>
<tr><td><b>ElasticNet</b></td><td>alpha, l1_ratio</td><td>Combines L1 and L2 penalties</td></tr>
</table>

<h4>7.1.5 Tree-Based Regression</h4>
<table>
<tr><th>Algorithm</th><th>Key Parameters</th><th>Notes</th></tr>
<tr><td><b>Random Forest</b></td><td>n_estimators, max_depth</td><td>Ensemble of decision trees; shows feature importance; supports CCP pruning optimization</td></tr>
<tr><td><b>Decision Tree</b></td><td>max_depth, min_samples_split</td><td>Single tree; shows feature importance; supports CCP pruning</td></tr>
</table>

<h3>7.2 Classification (Supervised)</h3>
<p><code>Machine Learning &rarr; Classification &rarr; ...</code></p>
<p>All classifiers share a common workflow:</p>
<ol>
<li>Select <b>target variable</b> (categorical/binary) and <b>feature columns</b></li>
<li>Set <b>train/test split ratio</b> (default 70/30)</li>
<li>Configure algorithm-specific hyperparameters</li>
<li>Optionally enable <b>StandardScaler</b> preprocessing (mandatory for SVM and KNN, auto-applied)</li>
<li>View results: accuracy, confusion matrix, classification report, ROC curve</li>
</ol>

<table>
<tr><th>Algorithm</th><th>Key Parameters</th><th>Notes</th></tr>
<tr><td><b>Logistic Regression (ML)</b></td><td>C, max_iter</td><td>scikit-learn implementation; supports multiclass</td></tr>
<tr><td><b>Random Forest</b></td><td>n_estimators, max_depth</td><td>Ensemble of decision trees; shows feature importance</td></tr>
<tr><td><b>Gradient Boosting</b></td><td>n_estimators, learning_rate, max_depth</td><td>Sequential boosting; shows feature importance</td></tr>
<tr><td><b>Decision Tree</b></td><td>max_depth, min_samples_split</td><td>Single tree; shows feature importance</td></tr>
<tr><td><b>SVM</b></td><td>C, kernel (rbf/linear/poly)</td><td><b>Mandatory StandardScaler</b> (auto-applied)</td></tr>
<tr><td><b>KNN</b></td><td>n_neighbors, weights, metric</td><td><b>Mandatory StandardScaler</b> (auto-applied)</td></tr>
<tr><td><b>LDA</b></td><td>solver</td><td>Linear Discriminant Analysis; optional scaling</td></tr>
<tr><td><b>QDA</b></td><td>&mdash;</td><td>Quadratic Discriminant Analysis; optional scaling</td></tr>
<tr><td><b>Naive Bayes</b></td><td>var_smoothing</td><td>Gaussian Naive Bayes; optional scaling</td></tr>
</table>

<h4>Model Comparison Dashboard</h4>
<p><code>ML &rarr; Classification &rarr; Compare Models&hellip;</code></p>
<p>Run <b>up to 8 classification models simultaneously</b> on the same dataset and view:</p>
<ul>
<li>A <b>ranked metrics table</b> (Accuracy, Precision, Recall, F1, AUC) sorted by performance</li>
<li>An <b>overlapping ROC curve plot</b> comparing all models visually</li>
<li>Quick identification of the best-performing algorithm for your data</li>
</ul>

<h3>7.3 Dimensionality Reduction</h3>
<p><code>ML &rarr; Dimensionality Reduction &rarr; Principal Component Analysis (PCA)&hellip;</code></p>
<ul>
<li>Reduces the number of features while retaining maximum variance</li>
<li>Select numeric feature columns and number of components</li>
<li><b>Outputs:</b> Scree plot (eigenvalue decay), Biplot (first 2 components), Explained Variance table</li>
<li>Optionally <b>appends</b> the calculated Principal Components (PC1, PC2, &hellip;) back to the dataset as new columns</li>
</ul>

<h3>7.4 Clustering (Unsupervised)</h3>
<p><code>Machine Learning &rarr; Clustering &rarr; ...</code></p>
<p>All clustering methods share a common workflow:</p>
<ol>
<li>Select feature columns (numeric only)</li>
<li>Configure algorithm parameters</li>
<li>View: cluster scatter plot (auto-PCA if &gt;2 features), cluster profile table, silhouette score</li>
<li>Optionally <b>append cluster labels</b> to the dataset as a new column</li>
</ol>

<table>
<tr><th>Algorithm</th><th>Key Parameters</th><th>Notes</th></tr>
<tr><td><b>K-Means</b></td><td>n_clusters, max_iter</td><td>Partitions data into K spherical clusters; includes Elbow Method plot</td></tr>
<tr><td><b>Hierarchical</b></td><td>n_clusters, linkage (ward/complete/average/single)</td><td>Generates a <b>dendrogram</b> showing the merging hierarchy</td></tr>
<tr><td><b>DBSCAN</b></td><td>eps, min_samples</td><td>Density-based; finds arbitrary-shaped clusters; labels outliers as -1</td></tr>
<tr><td><b>GMM</b></td><td>n_components, covariance_type</td><td>Gaussian Mixture Model; soft probabilistic cluster assignments</td></tr>
</table>
<hr>
<h2>8 &mdash; Visualize Menu</h2>
<p>All charts are generated using <b>Matplotlib</b> and appear in the <b>Plots</b> tab.
Each plot automatically generates the equivalent Python code in the Script Editor.</p>

<table>
<tr><th>Chart</th><th>Best For</th><th>Required Inputs</th><th>Options</th></tr>
<tr><td><b>Histogram</b></td><td>Distribution of a single numeric variable</td><td>1 numeric column</td><td>Number of bins, optional grouping</td></tr>
<tr><td><b>Box Plot</b></td><td>Spread, median, and outliers; comparing groups</td><td>1 numeric column</td><td>Optional grouping column for side-by-side comparison</td></tr>
<tr><td><b>Scatter Plot</b></td><td>Relationship between two numeric variables</td><td>2 numeric columns</td><td>Optional hue/colour column for grouping</td></tr>
<tr><td><b>Violin Plot</b></td><td>Distribution shape + box plot combined</td><td>1 numeric column</td><td>Optional grouping column</td></tr>
<tr><td><b>Q-Q Plot</b></td><td>Checking if data follows a normal distribution</td><td>1 numeric column</td><td>Reference distribution selection</td></tr>
<tr><td><b>Line Chart</b></td><td>Trends over an ordered axis (e.g. time)</td><td>X column + 1 or more Y columns</td><td>Multiple Y series on same axis</td></tr>
<tr><td><b>Bar Chart</b></td><td>Comparing values across categories</td><td>1 categorical + 1 numeric column</td><td>Aggregation function selection</td></tr>
<tr><td><b>Heatmap</b></td><td>Visualizing correlation matrices or pivot tables</td><td>Multiple numeric columns</td><td>Colour scheme, annotation toggle</td></tr>
</table>

<h3>8.1 Plot Interaction</h3>
<ul>
<li>Each plot opens in a new sub-tab within the Plots area</li>
<li>Use the <b>Matplotlib toolbar</b> (zoom, pan, save) at the top of each plot</li>
<li>Plots adapt to the current theme (light or dark background)</li>
<li>Right-click or use the save button to export as PNG</li>
</ul>

<hr>
<h2>9 &mdash; Report Menu</h2>

<h3>9.1 Generate Report</h3>
<p><code>Report &rarr; Generate Report (HTML/PDF)&hellip;</code></p>
<ul>
<li>Set a <b>custom report title</b></li>
<li>Choose which sections to include: <b>Dataset Summary</b>, <b>Python Script</b>, <b>Statistical Results</b></li>
<li>The Dataset Summary table is <b>transposed</b> (variables as rows) for readability</li>
</ul>
<table>
<tr><th>Format</th><th>Details</th></tr>
<tr><td><b>HTML</b></td><td>Professional styled document viewable in any browser. Includes syntax-highlighted code and formatted tables.</td></tr>
<tr><td><b>PDF</b></td><td>Uses <b>Microsoft Edge</b> (headless mode) for browser-quality rendering. Falls back to Chrome if Edge is unavailable. Each major section starts on a new page.</td></tr>
</table>

<h3>9.2 Export Script</h3>
<p><code>Report &rarr; Export Script (.py)&hellip;</code></p>
<p>Saves the entire contents of the Script Editor tab as a standalone <code>.py</code> file.
This file can be run independently with <code>python script.py</code> (requires the same packages:
polars, pandas, numpy, scipy, sklearn, matplotlib, seaborn).</p>

<hr>
<h2>10 &mdash; Script Editor</h2>
<p>The <b>Script Editor</b> tab shows all auto-generated Python code from your GUI actions.
It is a fully editable code editor that doubles as a Python IDE.</p>

<h3>10.1 Features</h3>
<table>
<tr><th>Feature</th><th>Description</th></tr>
<tr><td><b>Syntax Highlighting</b></td><td>Python keywords, strings, comments, numbers, decorators, built-ins &mdash; all colour-coded</td></tr>
<tr><td><b>Line Numbers</b></td><td>Displayed in the left gutter for easy reference</td></tr>
<tr><td><b>Auto-indentation</b></td><td>Maintains indent level on Enter; auto-indents after colons</td></tr>
<tr><td><b>Editable</b></td><td>Freely modify or add your own code alongside auto-generated code</td></tr>
<tr><td><b>Theme-aware</b></td><td>Syntax colours adapt to Light and Dark modes</td></tr>
</table>

<h3>10.2 Running Code</h3>
<table>
<tr><th>Action</th><th>Shortcut</th><th>Description</th></tr>
<tr><td>Run All</td><td>F5</td><td>Executes the entire script from top to bottom</td></tr>
<tr><td>Run Selection</td><td>Ctrl+Enter</td><td>Executes only the selected/highlighted lines</td></tr>
</table>

<h3>10.3 Execution Environment</h3>
<p>Code runs in a sandboxed namespace with these pre-imported:</p>
<table>
<tr><th>Variable</th><th>Value</th></tr>
<tr><td><code>df</code></td><td>The current DataFrame (Polars or Pandas)</td></tr>
<tr><td><code>pd</code></td><td><code>pandas</code></td></tr>
<tr><td><code>pl</code></td><td><code>polars</code></td></tr>
<tr><td><code>np</code></td><td><code>numpy</code></td></tr>
<tr><td><code>scipy</code></td><td><code>scipy</code> (access <code>scipy.stats</code> etc.)</td></tr>
</table>
<p>Any changes to <code>df</code> will update the Data View. Print statements appear in the Console.
Matplotlib figures are captured and displayed in the Plots tab.</p>

<hr>
<h2>11 &mdash; Console Panel</h2>
<p>The bottom Console panel provides colour-coded feedback for all operations:</p>
<table>
<tr><th style="width:120px;">Type</th><th>Colour</th><th>Examples</th></tr>
<tr><td><b>Commands</b></td><td style="color:#1E40AF;">Blue</td><td>The Python equivalent of each GUI action</td></tr>
<tr><td><b>Success</b></td><td style="color:#16A34A;">Green</td><td>&ldquo;Loaded 10,000 rows from data.csv&rdquo;, &ldquo;Project saved&rdquo;</td></tr>
<tr><td><b>Errors</b></td><td style="color:#DC2626;">Red</td><td>Exception messages and tracebacks</td></tr>
<tr><td><b>Info</b></td><td style="color:#64748B;">Gray</td><td>Variable summaries, column descriptions</td></tr>
</table>
<p>Click any variable name in the Variable Panel to see its <code>describe()</code> output here.</p>

<hr>
<h2>12 &mdash; Dashboard Builder</h2>
<p>The <b>Dashboard Builder</b> tab lets you compose interactive dashboard layouts.
Configure chart widgets, connect them to your data columns, and generate
the corresponding Python code. The dashboard adapts to the active theme.</p>

<hr>
<h2>13 &mdash; Keyboard Shortcuts</h2>
<table>
<tr><th>Shortcut</th><th>Action</th></tr>
<tr><td>Ctrl+O</td><td>Open Project</td></tr>
<tr><td>Ctrl+S</td><td>Save Project</td></tr>
<tr><td>Ctrl+Shift+S</td><td>Save Project As</td></tr>
<tr><td>Ctrl+Q</td><td>Exit Quantia</td></tr>
<tr><td>Ctrl+Z</td><td>Undo data change</td></tr>
<tr><td>Ctrl+Y</td><td>Redo data change</td></tr>
<tr><td>F5</td><td>Run entire script</td></tr>
<tr><td>Ctrl+Enter</td><td>Run selected code</td></tr>
</table>

<hr>
<h2>14 &mdash; Tips &amp; Best Practices</h2>
<ul>
<li><b>Check your data first:</b> Use Descriptive Statistics and histograms before running tests. Look for outliers and missing values.</li>
<li><b>Normality matters:</b> Use Q-Q plots to check normality. Choose non-parametric tests (Mann-Whitney, Kruskal-Wallis) if normality is violated.</li>
<li><b>Scale when needed:</b> SVM and KNN auto-scale their inputs. For other classifiers, enable the StandardScaler checkbox if features have very different ranges.</li>
<li><b>Stepwise with caution:</b> Stepwise variable selection is a convenience tool, not a substitute for domain knowledge. Always review selected variables for theoretical justification.</li>
<li><b>PCA in clustering:</b> When clustering with &gt;2 features, Quantia auto-applies PCA <i>for the scatter plot only</i>. The actual clustering uses all original features.</li>
<li><b>Model Comparison:</b> Use <code>ML &rarr; Classification &rarr; Compare Models</code> to quickly find the best algorithm before fine-tuning hyperparameters.</li>
<li><b>Reproducibility:</b> The Script Editor captures everything. Export it with <code>Report &rarr; Export Script</code> to share or re-run later.</li>
<li><b>Large datasets:</b> Parquet format is fastest for large files (&gt;100K rows). Use it for import and export when possible.</li>
<li><b>Theme consistency:</b> Switch themes <i>before</i> generating plots for consistent styling in your reports.</li>
<li><b>Auto-save protection:</b> Quantia auto-saves every 5 minutes. If you experience a crash, check the workspaces directory for <code>.temp.quantia</code>.</li>
<li><b>Workflow pipelines:</b> For repeated analyses, build a Workflow pipeline once and re-run it with different data files.</li>
</ul>
"""


_WIZARD_HTML = """\
<h2>Guided Analysis Wizard</h2>
<p>Follow these steps for a typical statistical analysis workflow:</p>

<h3>Step 1: Load Your Data</h3>
<p>Go to <code>File &rarr; Import Data</code> and select your dataset (CSV, Excel, JSON, or Parquet).
Check the <b>Data View</b> tab to confirm it loaded correctly. The status bar shows row and column counts.</p>

<h3>Step 2: Explore &amp; Clean</h3>
<ul>
<li>Click variables in the left panel to see quick summaries (mean, std, nulls) in the Console.</li>
<li>Use <code>Data &rarr; Clean Data</code> to handle missing values (drop rows, drop columns, or impute).</li>
<li>Create quick visualizations from the <code>Visualize</code> menu: histograms to check distributions, box plots to spot outliers, scatter plots to explore relationships.</li>
<li>Use <code>Data &rarr; Transform Data</code> for log transforms or z-score standardization if needed.</li>
</ul>

<h3>Step 3: Choose Your Analysis</h3>
<table>
<tr><th>Your Goal</th><th>Where to Go</th><th>When to Use</th></tr>
<tr><td>Summarize your data</td><td><code>Statistics &rarr; Descriptive Statistics</code></td><td>Always start here to understand your variables</td></tr>
<tr><td>Compare two group means</td><td><code>Statistics &rarr; t-test</code></td><td>Normal data, 2 groups (use Mann-Whitney if non-normal)</td></tr>
<tr><td>Compare 3+ group means</td><td><code>Statistics &rarr; ANOVA</code></td><td>Normal data, 3+ groups (use Kruskal-Wallis if non-normal)</td></tr>
<tr><td>Non-normal group comparisons</td><td><code>Statistics &rarr; Non-parametric Tests</code></td><td>Ordinal data or violated normality assumption</td></tr>
<tr><td>Test variable relationships</td><td><code>Statistics &rarr; Correlation</code></td><td>Measuring strength of association between numeric variables</td></tr>
<tr><td>Test categorical associations</td><td><code>Statistics &rarr; Chi-square</code></td><td>Two categorical variables; are they independent?</td></tr>
<tr><td>Predict a continuous outcome</td><td><code>ML &rarr; Regression &rarr; Linear</code></td><td>Predict numeric Y from numeric/categorical X variables</td></tr>
<tr><td>Predict a binary outcome</td><td><code>ML &rarr; Regression &rarr; Logistic</code></td><td>Predict yes/no outcome; get odds ratios</td></tr>
<tr><td>Classify into categories</td><td><code>ML &rarr; Classification</code></td><td>Predict category labels; try Compare Models first</td></tr>
<tr><td>Find natural groups</td><td><code>ML &rarr; Clustering</code></td><td>Discover structure; no predefined labels needed</td></tr>
<tr><td>Reduce feature dimensions</td><td><code>ML &rarr; Dimensionality Reduction &rarr; PCA</code></td><td>Too many features; visualize high-dimensional data</td></tr>
</table>

<h3>Step 4: Review Results</h3>
<ul>
<li>Check the <b>Results</b> tab for formatted tables, metrics, and statistical output</li>
<li>Check the <b>Plots</b> tab for generated visualizations (ROC curves, residual plots, cluster plots, etc.)</li>
<li>Review the <b>Script Editor</b> tab for the auto-generated Python code</li>
<li>Read the <b>Console</b> for plain-language summaries and any warnings</li>
</ul>

<h3>Step 5: Compare &amp; Iterate</h3>
<ul>
<li>For classification: use <code>ML &rarr; Classification &rarr; Compare Models</code> to benchmark up to 8 algorithms</li>
<li>For regression: try different variable combinations; use stepwise selection to find optimal predictors</li>
<li>Use Undo (Ctrl+Z) to revert any data changes and try a different approach</li>
</ul>

<h3>Step 6: Export</h3>
<ul>
<li><code>Report &rarr; Generate Report</code> for a professional HTML or PDF summary of your analysis</li>
<li><code>Report &rarr; Export Script</code> to save the reproducible Python code as a standalone .py file</li>
<li><code>File &rarr; Export Data</code> to save your modified/cleaned dataset</li>
<li><code>File &rarr; Save Project</code> to save everything as a <code>.quantia</code> archive for later</li>
</ul>
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

        # Load logo into the document\'s resource cache
        from quantia.utils.resources import resource_path
        logo_path = resource_path("reference/logo/Quantia_logo.png")
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
