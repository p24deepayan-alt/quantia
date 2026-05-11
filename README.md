# Quantia

**A fully offline, no-code statistical and machine learning desktop application.**

Quantia is designed to provide powerful data analysis and modeling capabilities without requiring you to write code or upload your data to the cloud. Every action performed through the graphical interface is automatically translated into reproducible Python code.

<p align="center">
  <img src="reference/logo/Quantia_logo.png" width="200" alt="Quantia Logo">
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#architecture">Architecture</a> •
  <a href="USER_GUIDE.md">User Guide</a>
</p>

---

## Features

### 🔒 Fully Offline
Your data stays on your machine. No cloud services, no telemetry, no internet required.

### 🛠️ Reproducible Workflows
Every GUI action generates standard Python code (`pandas`, `polars`, `scipy`, `scikit-learn`, `matplotlib`) in the built-in Script Editor. You can view, edit, and re-run this code at any time.

### ⛓️ Visual Workflow Builder
Design and connect data processing nodes in a visual canvas to build complex, reusable analysis pipelines. Supports **all** statistics, machine learning, and visualization tools via a categorized node interface.

### 🚀 Hardware Acceleration
Automatic detection of NVIDIA GPUs for future hardware-accelerated computation paths.

### 🎨 Light & Dark Themes
Switch between polished Light and Dark modes with a single click. All UI components, plots, and the workflow canvas adapt automatically.

---

### 📊 Statistics

| Category | Tools |
|----------|-------|
| **Descriptive** | Count, mean, std, min, quartiles, max, skewness, kurtosis, missing-value counts |
| **t-tests** | Independent two-sample, paired, one-sample — with Cohen's d effect size |
| **ANOVA** | One-way ANOVA with Tukey HSD post-hoc tests |
| **Non-parametric** | Mann-Whitney U, Wilcoxon Signed-Rank, Kruskal-Wallis |
| **Correlation** | Pearson, Spearman, Kendall — with correlation matrix and optional heatmap |
| **Chi-square** | Test of independence with Cramér's V and expected frequency tables |

### 🤖 Machine Learning

| Category | Algorithms |
|----------|------------|
| **Regression** | Linear (statsmodels + scikit-learn), Logistic, Ridge, Lasso, ElasticNet, Random Forest, Decision Tree |
| **Classification** | Logistic Regression, Random Forest, Gradient Boosting, Decision Tree, SVM, KNN, LDA, QDA, Naive Bayes |
| **Clustering** | K-Means, Hierarchical (with dendrogram), DBSCAN, Gaussian Mixture Model (GMM) |
| **Dimensionality Reduction** | PCA with Scree plot, Biplot, Explained Variance table, and dataset appending |
| **Model Comparison** | Run up to 8 classification models simultaneously; ranked metrics table + overlapping ROC curves |

### 📈 Visualizations

Histogram, Box Plot, Scatter Plot, Violin Plot, Q-Q Plot, Line Chart, Bar Chart, Heatmap — all generated via Matplotlib with auto-generated code.

### 🗄️ Data Operations

| Category | Operations |
|----------|------------|
| **Import / Export** | CSV, Excel (.xls/.xlsx), JSON, Parquet |
| **Cleaning** | Drop rows with NA, drop columns, impute (mean/median/mode/constant) |
| **Transform** | Log, sqrt, square, reciprocal, z-score, min-max scale, custom expressions |
| **Type Conversion** | Cast to int, float, string, datetime, category |
| **String Ops** | Text extract (before/after), change case & trim, find & replace, concatenate columns |
| **Filtering** | Subset rows with multi-condition AND/OR logic |
| **Merge / Join** | Inner, left, right, outer joins on selected key columns |
| **Conditional** | If/Else column creation with rule-based logic |
| **Aggregation** | Pivot Table / Group-By with sum, mean, count, etc. |

### 📑 Reporting

| Output | Details |
|--------|---------|
| **HTML Report** | Professional styled document viewable in any browser |
| **PDF Report** | Uses headless Microsoft Edge (or Chrome) for browser-quality rendering |
| **Script Export** | Save the full Script Editor contents as a standalone `.py` file |

### 🎛️ Additional Features

- **Command Palette** — Quick fuzzy search across all actions (`Ctrl+Shift+P` style)
- **Preferences** — Configure compute backend (CPU single-core / multi-core), scripting font size, appearance
- **Auto-Save** — Workspace is automatically saved every 5 minutes
- **Undo / Redo** — Full undo/redo history for all data-modifying operations (up to 50 snapshots)
- **Dashboard Builder** — Visual tab for composing interactive dashboard layouts
- **Guided Analysis Wizard** — Step-by-step workflow guide for common analyses
- **Stepwise Variable Selection** — Forward, backward, and both methods for regression models using AIC

---

## Installation

### Prerequisites

- **Python 3.11** or higher
- **Git**

### Option 1: Install from Source (Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/p24deepayan-alt/quantia.git
   cd quantia
   ```

2. **Create and activate a virtual environment:**

   Windows:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

   macOS / Linux:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the package in editable mode:**
   ```bash
   pip install -e .
   ```

   This installs all core dependencies defined in `pyproject.toml`:

   | Package | Min Version | Purpose |
   |---------|-------------|---------|
   | PySide6 | 6.7 | GUI framework (Qt6) |
   | pandas | 2.1 | DataFrames & data wrangling |
   | polars | 0.20 | High-performance data backend |
   | pyarrow | 14.0 | Columnar data & Parquet support |
   | numpy | 1.26 | Numerical computing |
   | psutil | 5.9 | System monitoring (RAM, CPU) |
   | openpyxl | 3.1 | Excel file read/write |
   | scipy | 1.11 | Statistical tests & distributions |
   | statsmodels | 0.14 | Regression & advanced statistics |

4. **Install optional dependencies for ML and visualization:**
   ```bash
   pip install scikit-learn matplotlib seaborn
   ```

5. **Install development tools (optional):**
   ```bash
   pip install -e ".[dev]"
   ```
   This adds `ruff`, `mypy`, and `pytest`.

### Option 2: Install with uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that can replace `pip` and `venv`. Since this project uses `pyproject.toml`, uv works out of the box.

1. **Install uv:**

   Windows (PowerShell):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   macOS / Linux:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/p24deepayan-alt/quantia.git
   cd quantia
   ```

3. **Install Python (if not already available):**
   ```bash
   uv python install 3.14
   ```

4. **Create and activate a virtual environment:**

   Windows:
   ```cmd
   uv venv --python 3.14
   .venv\Scripts\activate
   ```

   macOS / Linux:
   ```bash
   uv venv --python 3.14
   source .venv/bin/activate
   ```

5. **Install the package in editable mode:**
   ```bash
   uv pip install -e .
   ```

6. **Install optional dependencies for ML and visualization:**
   ```bash
   uv pip install scikit-learn matplotlib seaborn
   ```

7. **Install interactive Plotly visualizations (optional):**
   ```bash
   uv pip install -e ".[plotly]"
   ```
   This enables the **Plotly** rendering backend across all visualization and ML dialogs, providing interactive zoom, pan, hover, and export capabilities via an embedded web view.

8. **Install development tools (optional):**
   ```bash
   uv pip install -e ".[dev]"
   ```

9. **Run Quantia:**
   ```bash
   uv run -m quantia
   ```

### Option 3: Windows Installer

A standalone Windows installer is available (built with PyInstaller + Inno Setup). See `installer/quantia_setup.iss` for the Inno Setup configuration. After installation, launch `Quantia.exe` — no Python installation required.

---

## Usage

### Launching Quantia

```bash
# If installed via pip (editable or standard)
python -m quantia

# Or use the entry point
quantia
```

### Quick Start

1. **Import Data** — `File → Import Data` → select CSV, Excel, JSON, or Parquet.
2. **Explore** — Click variables in the left panel to see quick summaries in the Console.
3. **Analyze** — Select tools from `Data`, `Statistics`, `Machine Learning`, or `Visualize` menus.
4. **Review** — Check generated code in the **Script Editor** tab and results in the **Results** or **Plots** tabs.
5. **Save** — Save your session as a `.quantia` project file (`File → Save Project`) to resume later.
6. **Export** — Create professional output via `Report → Generate Report` or `Report → Export Script`.

For a comprehensive walkthrough, see the **[User Guide](USER_GUIDE.md)** or open `Help → User Manual` within the app.

---

## Project Structure

```text
quantia/
├── reference/
│   ├── documents/           # PRD, TRD, GUI spec, branding, user journeys
│   ├── fonts/               # Bundled TTF/OTF fonts (Inter, Fira Code)
│   └── logo/                # Logo assets (PNG, ICO)
├── src/
│   └── quantia/
│       ├── core/
│       │   ├── data_model.py     # Pandas/Polars table model for QTableView
│       │   ├── workspace.py      # Project save/load, undo/redo state machine
│       │   └── settings.py       # Persistent settings (compute mode, etc.)
│       ├── theme/
│       │   ├── dark.qss          # Dark mode Qt stylesheet
│       │   ├── light.qss         # Light mode Qt stylesheet
│       │   └── palette.py        # Colour definitions & theme accessor
│       ├── ui/
│       │   ├── central/
│       │   │   ├── data_view.py       # Spreadsheet-style data table
│       │   │   ├── script_editor.py   # Python code editor with syntax highlighting
│       │   │   ├── results_view.py    # HTML-rendered analysis results
│       │   │   ├── plot_view.py       # Matplotlib figure viewer
│       │   │   ├── dashboard_tab.py   # Interactive dashboard builder
│       │   │   └── workflow/          # Visual node-based pipeline builder
│       │   │       ├── view.py        # QGraphicsView canvas
│       │   │       ├── scene.py       # Node graph scene management
│       │   │       ├── items.py       # Node, port, and edge graphics items
│       │   │       ├── nodes_logic.py # Execution logic for all node types
│       │   │       └── engine.py      # Topological sort & pipeline runner
│       │   ├── dialogs/               # 38 analysis & operation dialogs
│       │   │   ├── base.py            # Shared dialog base class
│       │   │   ├── descriptive.py     # Descriptive statistics
│       │   │   ├── ttest.py           # t-tests (independent, paired, one-sample)
│       │   │   ├── anova_models.py    # ANOVA with post-hoc
│       │   │   ├── nonparametric.py   # Mann-Whitney, Wilcoxon, Kruskal-Wallis
│       │   │   ├── correlation.py     # Pearson, Spearman, Kendall
│       │   │   ├── chi_square.py      # Chi-square test of independence
│       │   │   ├── regression.py      # Linear regression (statsmodels)
│       │   │   ├── logistic_regression.py  # Logistic regression
│       │   │   ├── tree_regression.py # Ridge, Lasso, ElasticNet, RF, DT regressors
│       │   │   ├── classification.py  # 9 classification algorithms
│       │   │   ├── model_compare.py   # Multi-model comparison dashboard
│       │   │   ├── clustering.py      # K-Means, Hierarchical, DBSCAN, GMM
│       │   │   ├── pca.py             # Principal Component Analysis
│       │   │   ├── clean_data.py      # Missing value handling
│       │   │   ├── transform.py       # Mathematical transformations
│       │   │   ├── filter_data.py     # Row filtering
│       │   │   ├── merge_join.py      # Dataset joins
│       │   │   ├── pivot_table.py     # Pivot table / group-by aggregation
│       │   │   ├── if_else.py         # Conditional column creation
│       │   │   ├── type_convert.py    # Type casting
│       │   │   ├── text_extract.py    # Text extraction (before/after)
│       │   │   ├── string_format.py   # Case changes & trimming
│       │   │   ├── find_replace.py    # Find & replace in data
│       │   │   ├── concat_cols.py     # Column concatenation
│       │   │   ├── histogram.py       # Histogram dialog
│       │   │   ├── boxplot.py         # Box plot dialog
│       │   │   ├── scatter.py         # Scatter plot dialog
│       │   │   ├── violinplot.py      # Violin plot dialog
│       │   │   ├── qqplot.py          # Q-Q plot dialog
│       │   │   ├── linechart.py       # Line chart dialog
│       │   │   ├── barchart.py        # Bar chart dialog
│       │   │   ├── heatmap.py         # Heatmap dialog
│       │   │   ├── report.py          # Report generation (HTML/PDF)
│       │   │   ├── help.py            # User Manual & Guided Wizard
│       │   │   ├── preferences.py     # Settings dialog
│       │   │   └── command_palette.py # Fuzzy command search
│       │   ├── panels/
│       │   │   ├── variable_list.py   # Left dock — variable browser
│       │   │   └── console.py         # Bottom dock — output console
│       │   ├── main_window.py         # Main application window assembly
│       │   ├── menu_bar.py            # Full menu structure & signal routing
│       │   ├── toolbar.py             # Quick-access toolbar
│       │   ├── status_bar.py          # Dataset info, compute mode, progress
│       │   └── icons.py               # Feather icon renderer (SVG→QIcon)
│       ├── utils/
│       │   ├── codegen.py             # Python code generation helpers
│       │   ├── gpu.py                 # NVIDIA GPU detection
│       │   ├── paths.py               # Application directory management
│       │   ├── resources.py           # Resource path resolver (dev + bundled)
│       │   └── worker.py              # QRunnable script executor (threading)
│       ├── app.py                     # QApplication subclass with theme management
│       ├── __main__.py                # Entry point with splash screen
│       └── __init__.py                # Package version (0.9.0-beta)
├── tests/                             # Test suite
├── installer/
│   └── quantia_setup.iss              # Inno Setup installer configuration
├── pyproject.toml                     # Dependencies & project metadata
├── quantia.spec                       # PyInstaller build specification
├── USER_GUIDE.md                      # Comprehensive user guide
└── README.md                          # This file
```

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                      PySide6 (Qt6) GUI                       │
│  ├── MainWindow (QMainWindow)                                │
│  ├── DataTableView (QTableView + Polars/Pandas model)        │
│  ├── VariableList (QListWidget + column metadata)            │
│  ├── ScriptEditor (QPlainTextEdit + Python syntax highlight) │
│  ├── PlotCanvas (FigureCanvasQTAgg — matplotlib)             │
│  ├── WorkflowCanvas (QGraphicsView + custom node graph)      │
│  ├── ResultsView (QTextBrowser — HTML rendered)              │
│  └── Console (QTextEdit — colour-coded output)               │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                    Application Core                          │
│  • Workspace (project save/load, undo/redo)                  │
│  • Data Model (pandas ↔ polars bridge)                       │
│  • Code Generator (GUI action → Python code)                 │
│  • Script Worker (QRunnable threaded execution)              │
│  • Settings Manager (compute mode, preferences)              │
│  • GPU Detector (NVIDIA / CUDA introspection)                │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                      Compute Engines                         │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ pandas / │ │ scipy /    │ │ sklearn  │ │ matplotlib / │  │
│  │ polars / │ │ statsmodels│ │          │ │ seaborn      │  │
│  │ numpy    │ │            │ │          │ │              │  │
│  └──────────┘ └────────────┘ └──────────┘ └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Polars as primary data backend** | Faster reads, lower memory, lazy evaluation support. Falls back to Pandas for Excel import and libraries that require it. |
| **PySide6 (Qt6)** | Native look-and-feel on all platforms; rich widget library; permissive LGPL license. |
| **QRunnable worker threads** | Keeps the GUI responsive during long computations; results routed back via Qt signals. |
| **QSS-based theming** | Clean separation of styling from logic; easy to add new themes. |
| **ZIP-based `.quantia` project files** | Compact format containing Parquet data + Python script + JSON metadata + undo history. |
| **Feather icon set** | Consistent, clean outline icons that adapt colour to light/dark theme. |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open Project |
| `Ctrl+S` | Save Project |
| `Ctrl+Shift+S` | Save Project As |
| `Ctrl+Q` | Exit |
| `Ctrl+Z` | Undo data change |
| `Ctrl+Y` | Redo data change |
| `F5` | Run entire script |
| `Ctrl+Enter` | Run selected code |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Run linting: `ruff check src/`
5. Run type checks: `mypy src/quantia/`
6. Run tests: `pytest`
7. Submit a pull request

---

## License

This project is released under the MIT License.
