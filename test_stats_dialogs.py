import pandas as pd
import polars as pl
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.anova import anova_lm

# Mock environment
def show_result(title, html):
    print(f"\n--- Result: {title} ---")
    # Basic check if it looks like HTML
    if "<h3" in html and "</table>" in html:
        print("HTML format: OK")
    else:
        print("HTML format: POTENTIALLY BROKEN")
    
    # Check for the CSS bug
    if "if p < 0.05" in html or "if True" in html or "if False" in html:
        print("CSS BUG DETECTED!")

def progress(n):
    pass

# Sample Data
df_pd = pd.DataFrame({
    "Score": [10, 12, 11, 15, 14, 16, 100, 110, 105],
    "Group": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
    "Binary": ["X", "X", "X", "Y", "Y", "Y", "Y", "Y", "Y"],
    "X1": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    "X2": [1, 1, 2, 2, 3, 3, 4, 4, 5],
    "Cat1": ["Small", "Small", "Med", "Med", "Large", "Large", "Small", "Med", "Large"],
    "Cat2": ["Yes", "No", "Yes", "No", "Yes", "No", "Yes", "No", "Yes"]
})

def test_ttest_logic():
    print("\n>>> Testing T-test Logic")
    df = df_pd[df_pd["Group"].isin(["A", "B"])]
    test_vars = ["Score"]
    group_var = "Group"
    group1_val, group2_val = "A", "B"
    equal_var = True
    alternative = "two-sided"
    
    results = []
    for var in test_vars:
        data1 = df[df[group_var] == group1_val][var].dropna()
        data2 = df[df[group_var] == group2_val][var].dropna()
        res = stats.ttest_ind(data1, data2, equal_var=equal_var, alternative=alternative)
        results.append({
            'Variable': var,
            't-statistic': res.statistic,
            'p-value': res.pvalue,
            f'Mean ({group1_val})': data1.mean(),
            f'Mean ({group2_val})': data2.mean(),
        })
    results_df = pd.DataFrame(results)
    print(results_df.to_string())

def test_anova_logic():
    print("\n>>> Testing ANOVA Logic")
    model_data = df_pd.dropna()
    y = model_data['Score']
    X1 = model_data[['X1']]
    X1 = pd.get_dummies(X1, drop_first=True, dtype=float)
    X1 = sm.add_constant(X1)
    model1 = sm.OLS(y, X1).fit()
    
    X2 = model_data[['X1', 'X2']]
    X2 = pd.get_dummies(X2, drop_first=True, dtype=float)
    X2 = sm.add_constant(X2)
    model2 = sm.OLS(y, X2).fit()
    
    anova_results = anova_lm(model1, model2)
    print(anova_results.to_string())
    
    # Simulate the HTML formatting bug check
    p_val = anova_results['Pr(>F)'].iloc[1]
    print(f"P-value for ANOVA: {p_val}")

def test_nonparametric_logic():
    print("\n>>> Testing Non-parametric Logic")
    sub = df_pd[['Score', 'Group']].dropna()
    num_var = 'Score'
    cat_var = 'Group'
    alt = 'two-sided'
    
    # The generated code line:
    groups = [group[num_var].values for name, group in sub.groupby(cat_var)]
    group_names = [name for name, group in sub.groupby(cat_var)]
    
    stat, p = stats.kruskal(*groups)
    test_name = 'Kruskal-Wallis H Test'
    stat_name = 'H'
    medians = [np.median(g) for g in groups]
    
    # CSS BUG CHECK:
    # html += f'... background:#F0FDF4 if p < 0.05 else #FEF2F2; ...'
    # This is literal text in the source code.
    html = f'<div style="background:#F0FDF4 if p < 0.05 else #FEF2F2;">'
    show_result(test_name, html + "</table>")

def test_chisquare_logic():
    print("\n>>> Testing Chi-Square Logic")
    sub = df_pd[['Cat1', 'Cat2']].dropna()
    row_var, col_var = 'Cat1', 'Cat2'
    crosstab = pd.crosstab(sub[row_var], sub[col_var])
    chi2, p, dof, expected = stats.chi2_contingency(crosstab)
    
    # CSS BUG CHECK:
    # html += f'... background:#F0FDF4 if {p < 0.05} else #FEF2F2; ...'
    html = f'<div style="background:#F0FDF4 if {p < 0.05} else #FEF2F2;">'
    show_result("Chi-Square", html + "</table>")

test_ttest_logic()
test_anova_logic()
test_nonparametric_logic()
test_chisquare_logic()
