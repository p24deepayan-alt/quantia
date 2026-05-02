# Quantia

**A fully offline, no-code statistical and machine learning desktop application.**

Quantia is designed to provide powerful data analysis and modeling capabilities without requiring you to write code or upload your data to the cloud. Every action performed through the graphical interface is automatically translated into reproducible Python code.

<p align="center">
  <img src="reference/logo/69e99e05-da76-4624-b75e-3f64158aa657_removalai_preview.png" width="200" alt="Quantia Logo">
</p>

## Features

*   **🔒 Fully Offline:** Your data stays on your machine. No cloud services, no telemetry, no internet required.
*   **🛠️ Reproducible Workflows:** Every GUI action generates standard Python code (`pandas`, `scipy`, `scikit-learn`, `matplotlib`) in the built-in Script Editor. You can view, edit, and re-run this code at any time.
*   **📊 Comprehensive Statistics:** Descriptive statistics, t-tests (independent, paired, one-sample), ANOVA, Non-parametric tests (Mann-Whitney, Wilcoxon, Kruskal-Wallis), Correlation (Pearson, Spearman, Kendall), and Chi-square.
*   **🤖 Machine Learning:** 
    *   **Regression:** Linear and Logistic (with stepwise selection).
    *   **Classification:** Random Forest, Gradient Boosting, Decision Tree, SVM, KNN, LDA, QDA, Naive Bayes.
    *   **Clustering:** K-Means, Hierarchical, DBSCAN, GMM (with automatic PCA for visualization).
*   **📈 Visualizations:** Histograms, Box Plots, Scatter Plots, Violin Plots, Q-Q Plots, Line Charts, Bar Charts, and Heatmaps.
*   **🗄️ Data Operations:** Import/Export (CSV, Excel, JSON, Parquet), Data Cleaning (drop NA, impute), Transformations, Type Conversions, Filtering, and Merging/Joining.
*   **📑 Professional Reporting:** Generate browser-quality HTML or PDF reports (via headless Edge/Chrome) containing dataset summaries, statistical results, and generated Python code.

## Installation

### Prerequisites

*   Python 3.11 or higher
*   Git

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/p24deepayan-alt/quantia.git
    cd quantia
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment:**
    *   Windows:
        ```cmd
        .venv\Scripts\activate
        ```
    *   macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install PySide6 pandas pyarrow scipy statsmodels scikit-learn charset-normalizer
    # Note: Ensure matplotlib and seaborn are installed if not automatically pulled in.
    pip install scikit-learn matplotlib seaborn
    ```

## Usage

Start the application by running:

```bash
python -m quantia
```

### Getting Started

1.  **Import Data:** Use `File -> Import Data` to load a CSV, Excel, JSON, or Parquet file.
2.  **Explore:** Click on variables in the left panel to see quick summaries in the console.
3.  **Analyze:** Select tools from the `Data`, `Statistics`, `Machine Learning`, or `Visualize` menus.
4.  **Review:** Check the generated code in the **Script Editor** tab and the results in the **Results** or **Plots** tabs.
5.  **Save:** Save your session as a `.quantia` project file (`File -> Save Project`) so you can resume your work later.
6.  **Export:** Create a professional output using `Report -> Generate Report` or `Report -> Export Script`.

For a full breakdown of features, check out `Help -> User Manual` or the `Help -> Guided Analysis Wizard` within the app.

## Project Structure

```text
quantia/
├── reference/                # Documentation and logo assets
├── src/
│   └── quantia/
│       ├── core/             # Core data models and backend logic
│       ├── theme/            # PySide6 stylesheets and color palettes
│       ├── ui/
│       │   ├── central/      # Main workspace tabs (Data, Script, Results, Plots)
│       │   ├── dialogs/      # All analysis and operational popups (Stats, ML, Viz)
│       │   ├── panels/       # Dockable side panels (Variable List, Console)
│       │   ├── main_window.py# Main application window assembly
│       │   ├── menu_bar.py   # Application menu structure and routing
│       │   └── toolbar.py    # Quick access tools
│       ├── app.py            # Application initialization
│       └── __main__.py       # Entry point
├── pyproject.toml            # Dependencies and project metadata
└── README.md                 # Project documentation
```

## Architecture

Quantia is built using:
*   **GUI Framework:** PySide6 (Qt6)
*   **Data Manipulation:** `pandas`, `numpy`, `pyarrow`
*   **Statistics & ML:** `scipy`, `statsmodels`, `scikit-learn`
*   **Visualization:** `matplotlib`, `seaborn`

## License

This project is released under the MIT License.
