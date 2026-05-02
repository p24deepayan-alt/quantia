# Quantia – Product Requirements Document (PRD)

## 1. Executive Summary

**Quantia** is a fully offline, no‑code statistical desktop application for researchers, data analysts, and students. It combines a point‑and‑click interface with optional scripting (R/Python) to support the entire analytical workflow: data import/cleaning, descriptive & inferential statistics, machine learning, high‑quality visualisation, and reproducible reporting. All processing happens locally, with GPU acceleration for heavy computations.

---

## 2. Product Vision

> *“Democratise advanced statistics by removing the programming barrier, without sacrificing power, reproducibility, or performance.”*

Quantia bridges the gap between GUI‑based tools (like SPSS, JMP) and code‑first environments (R, Python). Every mouse action generates reproducible syntax; every analysis is accompanied by plain‑language assumption checks.

---

## 3. Target Users

| Persona | Use Case |
|---------|----------|
| **Academic researcher** | Runs complex models (mixed‑effects, survival, Bayesian) with publication‑ready tables and APA‑formatted reports. |
| **Data analyst (business)** | Cleans large CSV/Excel files, creates dashboards with linked filters, exports to PDF/HTML for stakeholders. |
| **Graduate student** | Learns statistics via guided test selection and assumption checking; produces R/Python scripts for assignments. |
| **Medical / clinical researcher** | Works with SPSS/SAS/Stata files, needs survival analysis and high‑DPI plots for papers. |
| **Power user (R/Python expert)** | Writes custom code inside Quantia, but uses the GUI for quick data munging and visualisation. |

---

## 4. Key Differentiators

- **Fully offline & secure** – No internet connection required; data never leaves the user’s machine.
- **No‑code by default, code when needed** – Dual interface eliminates switching between tools.
- **GPU acceleration** – For ML, bootstrapping, and large matrix operations (via DirectML / CUDA / OpenCL).
- **Chunked processing** – Handles datasets larger than RAM (e.g., 50+ GB CSV) seamlessly.
- **One‑click reproducibility** – Every action logs script/syntax; versioned history built‑in.

---

## 5. Functional Requirements

### 5.1 Data Management

| Req ID | Requirement |
|--------|-------------|
| DM‑01 | Import from CSV, Excel (`.xls`, `.xlsx`), SPSS (`.sav`), SAS (`.sas7bdat`), Stata (`.dta`), JSON, Parquet |
| DM‑02 | Export to all of the above + fixed‑width text, SQLite |
| DM‑03 | Data cleaning: handle missing values (delete, impute with mean/median/mode/model, KNN, iterative imputation), outlier detection (IQR, Z‑score, isolation forest), deduplication |
| DM‑04 | Variable transformation: recode (manual or by formula), binning, standardise, normalise, log, Box‑Cox, dummy coding |
| DM‑05 | Merge (one‑to‑one, one‑to‑many, many‑to‑many), join (inner, left, right, outer), reshape (wide ↔ long), pivot tables |
| DM‑06 | Large dataset support: chunked import, lazy evaluation, progress indicators, memory monitoring |

### 5.2 Descriptive Statistics

| Req ID | Requirement |
|--------|-------------|
| DS‑01 | Central tendency: mean, median, mode, trimmed mean |
| DS‑02 | Dispersion: variance, standard deviation, range, IQR, MAD, CV |
| DS‑03 | Frequency tables (1‑way, 2‑way, N‑way) with counts, percentages, cumulative |
| DS‑04 | Percentiles (any quantile), quartiles, skewness, kurtosis (Fisher/Pearson) |
| DS‑05 | Grouped / segmented summaries (by categorical variable) |

### 5.3 Inferential & Advanced Statistics

| Req ID | Requirement |
|--------|-------------|
| IS‑01 | **Parametric tests**: one/two‑sample t‑test (Welch’s), paired t‑test, one‑way/two‑way/repeated‑measures ANOVA, ANCOVA, MANOVA |
| IS‑02 | **Non‑parametric**: Mann‑Whitney U, Wilcoxon signed‑rank, Kruskal‑Wallis, Friedman, McNemar |
| IS‑03 | **Correlation**: Pearson, Spearman, Kendall’s tau, partial correlation, distance correlation |
| IS‑04 | **Regression**: linear, logistic (binary/multinomial), polynomial, ridge/lasso (with cross‑validated lambda), mixed‑effects (linear/non‑linear), GLM (Gaussian, Poisson, Gamma, Binomial) |
| IS‑05 | Chi‑square tests: goodness‑of‑fit, independence, homogeneity, exact tests (Fisher’s, Barnard’s) |
| IS‑06 | **Time series**: ARIMA (auto‑selection), exponential smoothing (ETS), seasonal decomposition (STL, X‑13), ACF/PACF plots, unit‑root tests |
| IS‑07 | **Survival analysis**: Kaplan‑Meier (log‑rank test), Cox proportional hazards, parametric survival models (Weibull, log‑normal) |
| IS‑08 | **Multivariate**: PCA (with varimax rotation), factor analysis (EFA, CFA), cluster analysis (k‑means, hierarchical, DBSCAN) |
| IS‑09 | **Bayesian statistics**: conjugate priors for common models, MCMC sampling (Stan/Brms integration via R), Bayes factors, posterior predictive checks |
| IS‑10 | **Power analysis** (for t‑tests, ANOVA, regression, proportions) and sample size calculation |

### 5.4 Machine Learning Bridge

| Req ID | Requirement |
|--------|-------------|
| ML‑01 | Classification: logistic regression (already covered), k‑NN, SVM (linear/RBF), naive Bayes, random forest, XGBoost (basic) |
| ML‑02 | Clustering: k‑means, hierarchical, DBSCAN, Gaussian mixture models |
| ML‑03 | Cross‑validation: k‑fold, LOOCV, stratified, time‑series split; evaluation metrics (accuracy, precision, recall, F1, ROC‑AUC, log‑loss, RMSE, MAE, R², etc.) |
| ML‑04 | Feature importance: permutation importance, SHAP (approximated with TreeExplainer / KernelExplainer), LIME (basic) |
| ML‑05 | Model export: PMML, ONNX, or pickled model for deployment elsewhere |

### 5.5 Visualisation

| Req ID | Requirement |
|--------|-------------|
| VZ‑01 | Standard charts: histogram, density plot, box plot (with jitter), violin plot, scatter plot (with trend line), bar chart (grouped/stacked), line chart, area chart, Q‑Q plot, P‑P plot |
| VZ‑02 | Statistical overlays: confidence intervals, kernel density, regression line, distribution fit |
| VZ‑03 | Interactive features: pan, zoom, tooltip, data point highlighting, brush linking across plots |
| VZ‑04 | Publication quality: export at 300+ DPI (PNG, TIFF, SVG, PDF), customisable themes (ggplot2 like, minimal, corporate), axis/legend/title formatting, annotation tools |
| VZ‑05 | Dashboards: drag‑and‑drop grid of plots/filters, linked brushing and selection, parameterised controls (sliders, dropdowns) |
| VZ‑06 | Geospatial mapping: choropleth, point maps, bubble maps (requires shapefiles or GeoJSON) |

### 5.6 Usability & Workflow

| Req ID | Requirement |
|--------|-------------|
| UX‑01 | Dual interface – point‑and‑click for all operations, plus a script editor for R/Python with syntax highlighting and execution |
| UX‑02 | Drag‑and‑drop workflow builder: nodes for “Import → Clean → Transform → Test → Plot → Export”, can be saved/loaded |
| UX‑03 | Assumption checking w/ plain‑language output: normality (Shapiro‑Wilk, Q‑Q plot), homoscedasticity (Levene, Breusch‑Pagan), multicollinearity (VIF), independence (Durbin‑Watson) |
| UX‑04 | Guided test selection wizard: “What is your outcome type? (continuous / categorical / time)” → “How many groups?” → suggests applicable tests with explanations |
| UX‑05 | Templates for common analyses: “Basic descriptives”, “t‑test report”, “Linear regression with diagnostics”, “ANOVA with post‑hoc”, “Time series forecast” |

### 5.7 Reproducibility & Reporting

| Req ID | Requirement |
|--------|-------------|
| RP‑01 | Every GUI action generates executable syntax (R or Python). User chooses preferred language at project startup. |
| RP‑02 | Version history (local git‑like) – every “save point” is timestamped, can revert, diff changes |
| RP‑03 | Audit trail: log of all user actions (who, what, when) for compliance |
| RP‑04 | One‑click report generation: PDF, Word (docx), HTML, LaTeX. Contains code, output tables, plots, and interpretation text. |
| RP‑05 | APA‑formatted output: tables follow APA 7th style, statistics reported with effect sizes and confidence intervals |
| RP‑06 | Live integration with Jupyter (.ipynb) and R Markdown (.Rmd) – can open/edit/save these formats natively |

### 5.8 Deployment & Performance

| Req ID | Requirement |
|--------|-------------|
| DP‑01 | Fully offline desktop app for Windows, macOS, Linux (native installers) |
| DP‑02 | GPU acceleration: for matrix operations (linear regression, PCA, random forests) and SHAP – using Vulkan/DirectML/CUDA if available |
| DP‑03 | Chunked processing for datasets > RAM – users see a “memory‑safe mode” toggle |
| DP‑04 | Minimal startup time (<5 seconds), responsive UI even during heavy computation (background threads with progress bar) |

---

## 6. Non‑Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Load 10M rows CSV in < 30s; run linear regression on 1M x 100 features in < 2 seconds (GPU). |
| **Security** | No telemetry; all data stays local; optional password protection for projects (AES‑256). |
| **Reliability** | Automatic recovery from crashes; incremental autosave every 5 minutes. |
| **Usability** | 95% of common tasks (import, descriptive stats, t‑test, bar chart) must be possible in ≤ 3 clicks from launch. |
| **Compatibility** | Full support for R 4.2+ and Python 3.9+ (embedded runtimes, no external installation required). |
| **Accessibility** | High contrast theme, keyboard navigation, screen reader support (WCAG 2.1 AA). |

---

## 7. Constraints & Assumptions

- **Constraints**  
  - No cloud dependencies – everything bundled in the installer (~500‑800 MB due to R/Python runtimes).  
  - GPU acceleration may fall back to CPU if unsupported hardware/drivers are missing.  
  - Must not rely on admin rights for typical usage (user‑level install available).

- **Assumptions**  
  - Target hardware: ≥8 GB RAM, ≥2 GB free disk, integrated GPU (Intel UHD or better) for basic acceleration, dedicated GPU for heavy ML.  
  - Users are familiar with basic statistical concepts (p‑values, distributions, etc.) but not necessarily programming.

---

## 8. Success Metrics (for v1.0)

1. **Adoption**: 10,000 downloads within first 3 months (academic + free tier).  
2. **Task completion rate**: 90% of users can perform a t‑test and generate a report without external help.  
3. **Performance**: 95% of operations on 2 GB dataset finish within 10 seconds (on recommended hardware).  
4. **Reproducibility**: 100% of GUI actions produce correct R/Python code that, when re‑run, yields identical results.  
5. **User satisfaction**: NPS ≥ 50 in post‑use survey.

---

## 9. Release Phases (Roadmap)

| Phase | Focus | Timeline |
|-------|-------|----------|
| **Alpha** | Core data management + descriptive stats + basic t‑test/ANOVA + linear regression + static plots (histogram, box plot) | Month 1‑4 |
| **Beta** | Add non‑parametrics, logistic regression, PCA, cluster analysis, dashboard builder, report export (PDF/HTML) | Month 5‑8 |
| **v1.0** | All ML bridge features, survival analysis, Bayesian stats, mixed‑effects, geospatial maps, GPU acceleration, script export | Month 9‑12 |
| **v1.5** | Workflow builder, version control (git), Jupyter/Rmd integration, power analysis wizard | Month 13‑15 |

---

## 10. Appendices

- **Glossary**: Included in the user documentation.  
- **Competitive matrix** (SPSS vs JMP vs Jamovi vs RStudio vs Quantia) – internal reference.  
- **RFI / RFP responses** – not applicable.

---