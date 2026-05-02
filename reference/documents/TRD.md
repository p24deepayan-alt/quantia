# Quantia – Technical Requirements Document

## 1. System Overview

Quantia is a cross‑platform, fully offline desktop application written in **Python 3.11+**. The GUI is built with **Qt for Python (PySide6)**, providing native performance and look. All data processing, statistics, machine learning, and visualisation use the Python scientific stack. GPU acceleration is available via PyTorch (CUDA, DirectML, Metal) and optionally cuML. No external R installation is required; users who want R can add it themselves (unsupported offline guarantee).

---

## 2. Technology Stack (Python Only)

| Layer | Library / Component |
|-------|---------------------|
| **GUI** | PySide6 (Qt6) – for main window, dialogs, plots, script editor, workflow builder |
| **Data Handling** | pandas (with pyarrow backend), numpy |
| **Import/Export** | pandas (CSV, Excel, JSON, Parquet), pyreadstat (SPSS, SAS, Stata), openpyxl, fastparquet |
| **Statistics** | scipy, statsmodels, pingouin (simplified stats) |
| **Machine Learning** | scikit‑learn, xgboost, lightgbm |
| **GPU Acceleration** | PyTorch (CUDA / DirectML / Metal), cuML (optional, if CUDA available) |
| **Time Series** | statsmodels.tsa, pmdarima (auto‑ARIMA) |
| **Survival Analysis** | lifelines |
| **Bayesian** | PyMC (or Bambi for easy syntax) |
| **Visualisation** | matplotlib (static high‑DPI), plotly (interactive dashboards) |
| **Reporting** | jinja2, weasyprint (PDF), python‑docx (Word), markdown + pandoc (optional) |
| **Version Control / Audit** | dulwich (pure‑Python Git) + custom JSONL log |
| **Workflow Builder** | PyFlow (modified for Qt6) or custom node‑editor built on QGraphicsView |
| **Packaging** | PyInstaller or Nuitka (compile to single executable) |

All libraries are bundled inside the final application. No user‑side installation of Python or packages is required.

---

## 3. Architecture (Python‑Only)

```
┌────────────────────────────────────────────────────────────┐
│                     PySide6 (Qt) GUI                        │
│  ├── MainWindow (QMainWindow)                              │
│  ├── DataTableView (QTableView + pandas model)             │
│  ├── VariableList (QListWidget)                            │
│  ├── ScriptEditor (QPlainTextEdit + syntax highlight)      │
│  ├── PlotCanvas (FigureCanvasQTAgg for matplotlib,         │
│  │                QWebEngineView for plotly)               │
│  ├── WorkflowCanvas (QGraphicsView + custom nodes)         │
│  └── Console (QTextEdit)                                   │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                   Application Core (Python)                 │
│  • Session manager (data + metadata)                       │
│  • Command registry (every GUI action → Python code)       │
│  • Code generator (translates actions to script)           │
│  • Chunked data iterator (for large datasets)              │
│  • GPU dispatcher (torch device selection)                 │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                 Compute Engines (Python)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ pandas/  │ │ scipy/   │ │ sklearn/ │ │ PyTorch/ │      │
│  │ numpy    │ │statsmodels│ │ xgboost  │ │ cuML     │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└────────────────────────────────────────────────────────────┘
```

---

## 4. Data Management (Python Implementation)

### 4.1 In‑memory representation
- Primary: `pandas.DataFrame` (backed by `pyarrow` for efficiency and chunking).
- For large data (> memory threshold), use `pandas.read_csv(..., chunksize=...)` and aggregate incrementally.

### 4.2 Chunked processing
All functions that can work incrementally (mean, variance, quantiles, linear regression via `statsmodels.RLM` with chunked arrays) will use a generator pattern. Functions that require full data (e.g., random forests) will show a warning if the dataset exceeds available RAM.

### 4.3 Importers (offline, no internet)
```python
# Pseudo-code
def import_file(path):
    ext = Path(path).suffix
    if ext == '.csv':
        return pd.read_csv(path, low_memory=False)
    elif ext in ['.xls', '.xlsx']:
        return pd.read_excel(path)
    elif ext == '.sav':
        import pyreadstat
        return pyreadstat.read_sav(path)[0]
    # ... similar for SAS, Stata, JSON, Parquet
```

### 4.4 Data cleaning
- Missing values: `df.fillna()`, `sklearn.impute.SimpleImputer`, `IterativeImputer`.
- Outliers: IQR (custom function), Z‑score, Isolation Forest (`sklearn.ensemble`).
- Deduplication: `df.drop_duplicates()`.

---

## 5. GPU Acceleration (Python)

- **PyTorch** is the primary GPU library: `torch.linalg.lstsq` for OLS, `torch` optimisers for logistic/GLM, `torch.pca` (custom or via `sklearn.decomposition.PCA` with torch backend).
- **cuML** used if RAPIDS is installed (optional detection). Fallback to scikit‑learn.
- User preference: GUI checkbox for “Use GPU if available”.
- Device detection:
  ```python
  if torch.cuda.is_available(): device = 'cuda'
  elif torch.backends.mps.is_available(): device = 'mps'
  else: device = 'cpu'
  ```

---

## 6. Dual Interface (No‑Code + Python Scripting)

- **Every GUI action** generates Python code (using the `inspect` module and code templates).
- The generated code appears in the **Script Editor** and can be executed directly.
- Users can edit the script, run it, and see results in the same environment.
- Script execution: `exec()` inside a restricted namespace (no file/network access by default).
- All plots generated by the script are captured and displayed in the Plot area.

### Example code generation for t‑test:
```python
def generate_code(dependent, group, equal_var=True):
    return f"""
from scipy import stats
result = stats.ttest_ind(df['{dependent}'], df['{group}'], equal_var={equal_var})
print(result)
"""
```

---

## 7. GUI Framework Details (PySide6)

All components are native Qt widgets. Later I will provide a **full GUI description document** with every dialog and control.

Main window layout:
- **Left panel**: Variable list (drag‑drop enabled)
- **Central area**: Tab widget with Data View, Script Editor, Workflow Builder, Plots
- **Right panel (collapsible)**: Output console & assumption check summaries
- **Top menu**: File, Data, Statistics, ML, Visualize, Report, Help

---

## 8. Reporting & Reproducibility (Python)

- **Script export**: Every session saves a `.py` file with all actions.
- **Version control**: `dulwich` provides Git‑like versioning without external Git.
- **Audit trail**: JSON lines file.
- **Report generation**:
  - Template engine: `jinja2`
  - PDF: `weasyprint` (HTML → PDF)
  - Word: `python-docx`
  - HTML: direct output
  - LaTeX: via `pylatex` or template + `pdflatex` (if installed)
- **APA formatting**: Use `statsmodels.stats` outputs + custom formatters.

---

## 9. Performance & Benchmarks (Same as before, achievable in Python)

With PyTorch for GPU and optimised pandas/numpy, the previous targets are realistic.

---

## 10. Packaging

- **PyInstaller** or **Nuitka** to create a standalone executable.
- Bundle all dependencies (pandas, numpy, scipy, PySide6, etc.) inside.
- For Windows: `Quantia.exe`; macOS: `Quantia.app`; Linux: `Quantia` binary.
- No admin rights needed (user‑level installation).

