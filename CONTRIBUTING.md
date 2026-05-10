# Contributing to Quantia

Thank you for your interest in contributing to Quantia! This guide will help you get set up and explain the conventions we follow.

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Git**

### Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/quantia.git
cd quantia

# 2. Create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Install optional ML/viz dependencies
pip install scikit-learn matplotlib seaborn
```

### Verify your setup

```bash
# Run the app
python -m quantia

# Run the test suite
pytest

# Run linting
ruff check src/

# Run type checking
mypy src/quantia/
```

---

## Development Workflow

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/short-description
   ```

2. **Make your changes** — keep commits focused and atomic.

3. **Run checks before pushing:**
   ```bash
   ruff check src/
   mypy src/quantia/
   pytest
   ```

4. **Push and open a Pull Request** against `main`.

---

## Project Layout

```
src/quantia/
├── core/           # Data model, workspace, settings
├── theme/          # QSS stylesheets and colour palettes
├── ui/
│   ├── central/    # Main area tabs (data, script, results, plots, workflow)
│   ├── dialogs/    # All analysis and operation dialogs
│   └── panels/     # Side panels (variable list, console)
├── utils/          # Code generation, threading, paths, GPU detection
├── app.py          # QApplication subclass
└── __main__.py     # Entry point
```

---

## Code Style

| Rule | Details |
|------|---------|
| **Formatter / Linter** | [Ruff](https://docs.astral.sh/ruff/) — configured in `pyproject.toml` |
| **Line length** | 100 characters max |
| **Target version** | Python 3.12 syntax features allowed |
| **Type hints** | Required — `mypy --strict` is enforced |
| **Imports** | `from __future__ import annotations` at the top of every module |
| **Docstrings** | Required for classes and public methods; use triple-quoted `"""` style |

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions / variables**: `snake_case`
- **Private members**: Prefix with `_` (e.g. `_build_html`, `self._df`)
- **Constants**: `UPPER_SNAKE_CASE`

---

## Adding a New Analysis Dialog

Most contributions add a new statistical test or ML algorithm. Follow this pattern:

1. **Create the dialog** in `src/quantia/ui/dialogs/`. Subclass `BaseAnalysisDialog`:

   ```python
   from quantia.ui.dialogs.base import BaseAnalysisDialog

   class MyNewDialog(BaseAnalysisDialog):
       def __init__(self, df, parent=None):
           super().__init__("My New Analysis", df, parent)

       def _build_selectors(self, layout):
           # Add variable selection widgets
           ...

       def build_options(self, layout):
           # Add checkboxes, dropdowns, etc.
           ...

       def generate_code(self) -> str:
           # Return Python code as a string
           # Use show_result('Title', html_string) for HTML output
           ...
   ```

2. **Output format**: Use rich HTML strings via `show_result('Title', html)` — **not** raw DataFrames. This ensures results are:
   - Styled consistently with other tests
   - Discoverable by the report export
   - Theme-aware in the Results View

3. **Wire it up**:
   - Add a `Signal()` in `menu_bar.py`
   - Add a menu action in the appropriate menu
   - Connect the signal in `main_window.py`
   - Optionally add a workflow node in `nodes_logic.py` and `scene.py`

4. **Add tests** in the `tests/` directory.

---

## Adding a Workflow Node

If your feature should be available in the visual Workflow Builder:

1. Create a `class MyNewNode(BaseLogicNode)` in `nodes_logic.py`.
2. Register it in `scene.py` — add to imports, the context menu, and the `_node_class_map`.
3. The node's `configure()` method should open your dialog and store the generated code.

---

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Mann-Whitney U test dialog
fix: handle NaN in correlation matrix
docs: update user guide with PCA section
refactor: extract shared table styling into helper
test: add tests for chi-square dialog
chore: update ruff to 0.5
```

---

## Testing

- **Framework**: [pytest](https://docs.pytest.org/) (v8+)
- **Location**: `tests/` directory
- Test files should be named `test_*.py`
- Run the full suite: `pytest`
- Run a specific file: `pytest tests/test_analysis_dialogs.py`
- Run with verbose output: `pytest -v`

### What to test

- Dialog code generation (`generate_code()` returns valid Python)
- Edge cases (empty selection, single variable, missing data)
- Generated code executes without errors against sample DataFrames

---

## Reporting Bugs

Open an issue with:

1. **Steps to reproduce** — what you did, what data you used
2. **Expected vs actual behaviour**
3. **Environment** — OS, Python version, Quantia version (`python -c "import quantia; print(quantia.__version__)"`)
4. **Console output** — paste any error messages or tracebacks

---

## Feature Requests

Open an issue tagged `enhancement` with:

- A clear description of the feature
- Why it's useful (what problem it solves)
- Any reference implementations or papers, if applicable

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
