# Quantia – User Journey Document

This document traces the paths different personas take to accomplish key tasks. Each journey is **no‑code by default**; power users can switch to the script editor at any time.

## Journey 1: Academic Researcher – Running a Mixed‑Effects Model

1. **Launch Quantia** → “New Project” → name it “Depression_Study”.
2. **Import data**: File → Import Data → SPSS (.sav) → select `clinical_trial.sav`.
3. **Data cleaning**:
   - Variable list shows “age” has 5% missing → right‑click → “Handle Missing” → Impute with median.
   - Outlier detection: select “HDRS_score” → Data → Outlier Detection → IQR → Winsorize.
4. **Check assumptions** (for linear model):
   - Descriptive → Skewness/Kurtosis of HDRS_score → right‑click on output → “Explain” → reads “Moderate positive skew, consider transformation”.
   - Transform → Log10(HDRS_score).
5. **Mixed‑effects model** (lme4 via Python’s `statsmodels` or `mixedlm`):
   - Statistics → Regression → Mixed‑effects.
   - Dependent: `log_HDRS`, Fixed factors: `treatment`, `baseline_severity`, Random: `+ 1|patient_id`.
   - Click “Check Assumptions” → residual Q‑Q plot shown.
   - Click “Run” → Output table with coefficients, CIs, p‑values.
6. **Generate report**: Report → Generate Report → APA format → PDF. The report includes the model table, assumption checks, and a box plot of residuals.
7. **Export script**: File → Export Script → `mixed_model_analysis.py`. The researcher can later rerun or modify the script.

---

## Journey 2: Business Analyst – Sales Dashboard with Linked Filters

1. **Import Excel**: `sales_2025.xlsx` (1M rows). Quantia warns “large file – use memory‑safe mode?” → Yes.
2. **Quick descriptive**: Select `revenue` → Descriptive Stats → see mean, median, outliers.
3. **Pivot table**: Data → Pivot Table; Rows: `region`, Columns: `quarter`, Values: `revenue` (sum). Creates a new dataframe.
4. **Dashboard builder**:
   - Drag a map widget → assign `region` → colour by `total_revenue`.
   - Drag a bar chart widget → x=`product_category`, y=`revenue`.
   - Drag a filter (slider) for `quarter` → link it to both plots.
5. **Publish**: Dashboard → Export as HTML (interactive) → send to manager.

---

## Journey 3: Student Learning Statistics – Guided t‑test

1. **Open built‑in example**: Help → Sample Datasets → “Exam Scores (male/female)”.
2. **Guided test wizard** (Help → Guided Test Wizard):
   - Q1: Outcome type? → “Continuous”.
   - Q2: Groups? → “Two groups”.
   - Q3: Paired? → “No”.
   - Wizard suggests: “Independent samples t‑test”. Explanation: “Compares means between two unrelated groups”.
   - Click “Run this test” → t‑test dialog pre‑filled.
3. **Check assumptions** button → says “Normality p > 0.05 for both groups; variances equal (Levene p=0.34)”. Plain language: “Assumptions met.”
4. Run → Output: t(38)=2.14, p=0.038, Cohen’s d=0.68.
5. **Generate code** → Python script appears: `stats.ttest_ind(...)`. Student saves it for homework.
6. **Report**: One‑click → Word document with APA‑formatted results.

---

## Journey 4: Medical Researcher – Survival Analysis

1. **Import SAS data**: `cancer_trial.sas7bdat`.
2. **Survival dialog**:
   - Time: `survival_months`, Event: `died` (1=event).
   - Group: `treatment` (drug vs placebo).
   - Run → Kaplan‑Meier plot appears (step function).
   - Log‑rank test p = 0.03 → output says “Significant difference between groups”.
3. **Cox regression**:
   - Add covariates: `age`, `tumor_size`.
   - Output: hazard ratios (HR) with CIs.
4. **Export plot** as TIFF at 600 DPI → ready for manuscript.

---

## Journey 5: Power User (Python Coder) – Custom SHAP Analysis

1. **Load data** via GUI (point‑and‑click) → `credit_default.csv`.
2. Switch to **Script Editor** tab.
3. Write or paste:
   ```python
   import xgboost as xgb
   import shap
   model = xgb.XGBClassifier().fit(X_train, y_train)
   explainer = shap.TreeExplainer(model)
   shap_values = explainer.shap_values(X_test)
   shap.summary_plot(shap_values, X_test, show=False)
   ```
4. Execute (F5) → plot appears in “Plots” tab.
5. **Save script** as part of the project. The GUI also logs that SHAP was run (audit trail).
6. **Generate report** → includes the custom SHAP plot and the Python code used.

---

**All journeys share**:
- Every step is undoable.
- The full Python script of actions is available.
- The app never requires internet.

---

