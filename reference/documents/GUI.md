# Quantia – GUI Description Document

This document lists **every** graphical component in Quantia, from the main window to each analysis dialog, data viewer, and helper widget. All components are built with **PySide6 (Qt for Python)**.

---

## 1. Main Window (`MainWindow`)

**Structure**: QMainWindow with menu bar, toolbars, status bar, and dock widgets.

### 1.1 Menu Bar

| Menu | Items |
|------|-------|
| **File** | New Project, Open Project, Save Project, Save As, Import Data → (CSV, Excel, SPSS, SAS, Stata, JSON, Parquet), Export Data → (same formats), Exit |
| **Edit** | Undo, Redo, Cut, Copy, Paste, Find (in script), Preferences |
| **Data** | Clean Data (missing, outliers, duplicates), Transform (recode, bin, standardise, log, dummy), Merge/Join, Reshape (wide↔long), Pivot Table |
| **Statistics** | Descriptive Statistics, t‑test, ANOVA, Non‑parametric (submenu), Correlation, Regression (submenu), Chi‑square, Time Series, Survival, Multivariate (PCA/FA/Cluster), Bayesian, Power Analysis |
| **Machine Learning** | Classification, Clustering, Feature Importance, SHAP, Model Evaluation (CV) |
| **Visualize** | Histogram, Box Plot, Scatter Plot, Violin, Q‑Q Plot, Line Chart, Bar Chart, Heatmap, Geospatial Map, Dashboard Builder |
| **Report** | Generate Report (PDF/Word/HTML/LaTeX), Export Script, Version History, Audit Log |
| **Help** | User Manual, Guided Test Wizard, About Quantia, Check for Updates (manual) |

### 1.2 Toolbar (Icon + Text)

- New Project, Open, Save, Undo, Redo
- Import Data, Export Data
- Run Script (green play button)
- Generate Code for last action
- Open Workflow Builder
- Preferences

### 1.3 Status Bar

- Memory usage gauge (orange when >70% RAM)
- Current dataset: rows × columns
- GPU status (GPU active / CPU only)
- Progress bar for long operations

---

## 2. Dockable Panels

All panels can be hidden, floated, or tabbed.

### 2.1 Variable List (`VariableListWidget`)

- **Widget**: QListWidget with custom item delegate.
- **Shows**: Variable name, type (📊 numeric, 🏷️ categorical, 📅 datetime), % missing (coloured circle), starred for “key variable”.
- **Context menu (right‑click)**:
  - Set measurement level (Nominal / Ordinal / Continuous)
  - Describe (summary stats)
  - Recode
  - Visualise quick histogram
  - Copy variable name
- **Drag‑drop**: can drag variable names into any analysis dialog’s variable selectors.

### 2.2 Output Console (`ConsoleWidget`)

- **Widget**: QTextEdit with monospace font, black background, coloured text.
- **Shows**: Printed output from executed scripts, error messages (red), warnings (yellow), plain‑language assumption results (green).
- **Clear button** (eraser icon).
- **Copy all** button.

### 2.3 Script Editor (`ScriptEditorWidget`)

- **Widget**: QPlainTextEdit + QSyntaxHighlighter (Python syntax).
- **Features**:
  - Line numbers (QPlainTextEdit with side bar)
  - Run selection (Ctrl+Enter), Run all (F5)
  - Code completion (simple, based on `__builtins__` and imported libs)
  - Find/replace dialog
  - Save script to `.py`
- **Tab integration**: part of central tab widget, next to “Data View”.

---

## 3. Central Area (Tab Widget)

### 3.1 Data View (`DataTableView`)

- **Widget**: QTableView with custom `PandasModel` (subclass of QAbstractTableModel).
- **Features**:
  - Horizontal header with variable names (click to sort)
  - Vertical header with row numbers
  - Alternating row colours
  - Freeze first column (optional)
  - Filter row (text input above each column – using QLineEdit in header)
  - Column width auto‑adjust (double‑click separator)
- **Context menu** (on cell/header):
  - Sort ascending/descending
  - Filter by value
  - Copy cell / row
  - Plot column (quick histogram)

### 3.2 Script Editor (already described – appears as a tab)

### 3.3 Workflow Builder (`WorkflowCanvas`)

- **Widget**: QGraphicsView with a custom scene for node‑graph.
- **Node types** (each node is a QGraphicsRectItem with input/output ports):
  - **Data Source** (CSV file, Excel, etc.)
  - **Clean** (drop NAs, impute)
  - **Transform** (log, standardise)
  - **Filter** (subset rows by condition)
  - **Summarise** (grouped stats)
  - **Test** (t‑test, ANOVA, etc.) – output ports for result table and plot
  - **Plot** (histogram, box plot)
  - **Export** (PDF, Excel)
- **Controls**:
  - Right‑click → Add Node
  - Drag to connect ports (data flow)
  - Double‑click node → open configuration dialog
  - Run button (top left) executes the graph sequentially
  - Save/Load workflow (`.quantia_flow` JSON)

### 3.4 Plot Area (`PlotTabWidget`)

- Contains one or more plots (each in a sub‑tab). Each sub‑tab has:
  - **Plot canvas**:
    - For static plots: `FigureCanvasQTAgg` (matplotlib)
    - For interactive plots: `QWebEngineView` (plotly)
  - **Toolbar** (Zoom, Pan, Save as PNG, Copy to clipboard)
  - **Plot options** (modify title, labels, theme from a side panel)

---

## 4. Analysis Dialogs (Non‑modal, can stay open)

Each dialog follows a consistent layout:

```
+--------------------------------------------------+
|  [Dialog Title]                            [X]  |
+--------------------------------------------------+
|  Variable selection:                              |
|    [List of available variables (drag‑drop)]    |
|                                                  |
|  Dependent variable:  [combobox]                |
|  Grouping variable:    [combobox]                |
|                                                  |
|  [ ] Assume equal variance?                      |
|  α level:  [0.05]                               |
|                                                  |
|  [Check Assumptions]   [Run]   [Generate Code]  |
+--------------------------------------------------+
```

### 4.1 Descriptive Statistics Dialog

- Select variables (checklist)
- Options: mean, median, sd, skewness, kurtosis, percentiles (custom)
- Group by (optional categorical variable)
- Output: table in console + option to export to Excel

### 4.2 t‑test Dialog

- Two samples:
  - Two independent groups (select dependent + grouping variable)
  - Paired (select two dependent variables)
- Options: equal variance (Welch’s correction), alternative hypothesis (two‑sided / less / greater)
- Assumptions button → shows Shapiro‑Wilk (normality) and Levene (homogeneity) results in plain English.

### 4.3 ANOVA Dialog

- One‑way: dependent + factor
- Two‑way: dependent + factor1 + factor2 (+ interaction checkbox)
- Repeated measures: select multiple dependent variables (within‑subjects)
- Post‑hoc: Tukey HSD, Bonferroni (checkboxes)
- Effect size: η², ω²

### 4.4 Linear Regression Dialog

- Dependent variable (numeric)
- Independent variables (multiple selection from list)
- Options:
  - Include intercept
  - Standardise coefficients
  - Diagnostics (VIF, Durbin‑Watson, residual plots)
  - Ridge/Lasso (alpha slider)
- Output: coefficients table (with CI, p‑value), R², adjusted R², F‑test.

### 4.5 Logistic Regression Dialog

- Dependent: binary (0/1) categorical
- Independent: numeric/categorical
- Link function: logit, probit
- Output: odds ratios, confusion matrix, ROC curve (optional)

### 4.6 Correlation Matrix Dialog

- Select multiple numeric variables
- Method: Pearson, Spearman, Kendall
- Display: heatmap (interactive) or table
- Partial correlation: add controlling variable(s)

### 4.7 Chi‑square Dialog

- Two categorical variables (contingency table)
- Options: Goodness‑of‑fit (expected proportions), Fisher’s exact if any expected <5
- Output: χ², df, p, Cramér’s V.

### 4.8 PCA / Factor Analysis Dialog

- Variables (numeric)
- Rotation: Varimax, Promax, none
- Number of components (eigenvalue >1 or user‑defined)
- Output: scree plot, loadings table, biplot.

### 4.9 Time Series Dialog

- Date/datetime column as index
- Variable to forecast
- Decomposition (additive/multiplicative)
- ARIMA: auto (pmdarima) or manual p,d,q
- Exponential smoothing: trend/seasonal options
- Forecast horizon (slider)

### 4.10 Survival Analysis Dialog

- Time variable
- Event variable (binary: 1=event, 0=censored)
- Group variable (optional for KM curves)
- Cox regression: select covariates
- Output: Kaplan‑Meier plot, log‑rank test, hazard ratios (Cox)

### 4.11 Machine Learning – Classification Dialog

- Target variable (binary/multiclass)
- Features (multiple)
- Algorithm selection (Random Forest, SVM, k‑NN, XGBoost)
- Train/test split ratio (slider)
- Cross‑validation folds (spinbox)
- Output: accuracy, precision, recall, F1, ROC curve

### 4.12 Cluster Analysis Dialog

- Variables (all numeric)
- Method: k‑means, hierarchical, DBSCAN
- Number of clusters (silhouette suggested)
- Output: cluster assignment column (adds to dataset), cluster plot (2D PCA reduced)

### 4.13 Power Analysis Dialog

- Test family (t‑test, ANOVA, regression, proportion)
- Effect size (Cohen’s d, η², etc.)
- α, power (1‑β)
- Compute required sample size OR power given N.

### 4.14 Guided Test Wizard (Modal)

- Step 1: “What is your outcome variable type?” (Continuous, Categorical, Time to event)
- Step 2: “How many groups / predictors?” (One sample, two groups, >2 groups, continuous predictor, multiple predictors)
- Step 3: “Do you have repeated measures?” (Yes/No)
- Step 4: Wizard suggests tests (e.g., “t‑test for independent samples”) with explanation.
- Button: “Run this test” → opens the respective dialog.

---

## 5. Data Cleaning & Transformation Dialogs

### 5.1 Handle Missing Data

- **Options**:
  - Delete rows with any missing (listwise)
  - Delete rows with missing in selected variables only
  - Impute: mean, median, mode (all numeric), constant value, KNN (k slider), iterative imputation (MICE)
- Preview of changes (highlighted rows)

### 5.2 Outlier Treatment

- Detection method: IQR (multiplier 1.5), Z‑score (threshold 3), Isolation Forest
- Action: cap (winsorize), remove, keep with indicator variable (new column “is_outlier”)

### 5.3 Recode Variables

- Manual recode: old value → new value (grid of entries)
- Recode by formula: e.g., `log(x)`, `(x - mean)/sd`
- Binning: user‑defined bins or equal frequency/width
- Dummy coding: select categorical variable → creates binary columns

### 5.4 Merge/Join Dialog

- Left dataset (current), right dataset (imported or another sheet)
- Join type: inner, left, right, outer
- Merge key(s): select matching columns (can match by different names)
- Indicator column (“_merge”) optional

### 5.5 Reshape (Wide <-> Long)

- Wide → Long: identify id columns, stub names of measured variables
- Long → Wide: id columns, variable name column, value column

### 5.6 Pivot Table Dialog

- Rows (categorical), Columns (categorical), Values (numeric), Aggregation (mean, sum, count, etc.)

---

## 6. Visualisation Dialogs

Each plot type shares a common dialog:

- Variable selectors (drag‑drop)
- Options (transparency, colour, bin number for histograms)
- Facet (by categorical variable) – row/col
- Theme selector (light, dark, ggplot, minimal)
- Export button (PNG, SVG, PDF at user‑selected DPI)

**Specific options per chart**:

- **Histogram**: bins (auto via Freedman‑Diaconis or manual), density overlay, KDE
- **Box plot**: notch, jitter points, outlier style
- **Scatter plot**: trend line (linear, LOESS), confidence band, point size mapping
- **Violin plot**: side‑by‑side groups, quartile lines
- **Q‑Q plot**: distribution (normal, t, uniform, etc.)
- **Bar chart**: error bars (SD, SE, CI), value labels
- **Heatmap**: colour scheme, cluster rows/columns
- **Geospatial map**: shapefile upload, variable to colour, position markers

---

## 7. Dashboard Builder

- **Canvas**: QGraphicsView with grid layout (size adjustable)
- **Toolbox** (side panel): drag‑drop widgets: Plot, Filter (slider, dropdown), Text box, Image
- **Linking**: define which filter controls which plots (by variable name)
- **Export** dashboard as standalone HTML (interactive) or PDF.

---

## 8. Preferences Dialog

Tabs:

- **General**: Default import folder, autosave interval (minutes), memory limit (GB)
- **Compute**: Radio buttons for compute backend selection:
  - **CPU - single core**: Sequential execution.
  - **CPU - Multi core**: Parallel execution using all available CPU cores. (Shows warning about compute power usage)
- **Scripting**: Default language (Python only), font size, indentation spaces
- **Appearance**: Theme (Light / Dark / High Contrast), accent colour picker
- **Report**: Default template (APA, Minimal), default DPI for images (300)

---

## 9. Help & Documentation

- **User Manual**: QTextBrowser showing local HTML help (searchable)
- **Tooltips**: Every button and menu item has a descriptive tooltip (e.g., “t‑test – Compares means between two groups”)
- **Status tips**: Shown in status bar when hovering over controls.

---

**End of GUI Description Document** – covers every component from main window to smallest dialog. No part of the interface is omitted.

---

