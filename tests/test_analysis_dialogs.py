import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# PySide6 imports needed for mocking Qt UI
from PySide6.QtWidgets import QApplication

from quantia.ui.dialogs.pivot_table import PivotTableDialog
from quantia.ui.dialogs.pca import PCADialog
from quantia.ui.dialogs.model_compare import ModelComparisonDialog
from quantia.ui.dialogs.clustering import KMeansDialog

# Ensure a QApplication exists for Qt tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # No teardown needed, let it persist for other tests

@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing."""
    return pd.DataFrame({
        'Category': ['A', 'A', 'B', 'B', 'C', 'C'],
        'Region': ['North', 'South', 'North', 'South', 'North', 'South'],
        'Sales': [100, 150, 200, 250, 300, 350],
        'Profit': [10, 15, 20, 25, 30, 35],
        'Target': [0, 1, 0, 1, 0, 1]
    })

def test_pivot_table_generation(qapp, sample_data):
    """Test Pivot Table code generation and execution."""
    df = sample_data.copy()
    dialog = PivotTableDialog(df)
    
    # Simulate UI selections
    dialog.list_groupby.addItem("Category")
    dialog.list_pivot.addItem("Region")
    dialog.list_values.addItem("Sales")
    dialog.cmb_agg.setCurrentText("Sum")
    
    code = dialog.generate_code()
    
    # Assert code exists
    assert "pd.pivot_table" in code
    assert "index=['Category']" in code
    
    # Execute code
    namespace = {'df': df, 'pd': pd}
    exec(code, namespace)
    
    # Verify result
    assert 'pivot_df' in namespace
    pivot_df = namespace['pivot_df']
    assert pivot_df.shape[0] == 3

def test_pca_generation(qapp, sample_data):
    """Test PCA dialog code generation and execution."""
    df = sample_data.copy()
    dialog = PCADialog(df)
    
    # Simulate UI selections
    dialog.list_features.addItem("Sales")
    dialog.list_features.addItem("Profit")
    # Select items
    for i in range(dialog.list_features.count()):
        dialog.list_features.item(i).setSelected(True)
        
    dialog.spin_components.setValue(2)
    dialog.chk_append.setChecked(True)
    
    # Disable plotting/HTML outputs for clean testing
    dialog.chk_scree.setChecked(False)
    dialog.chk_biplot.setChecked(False)
    dialog.chk_var_table.setChecked(False)
    
    code = dialog.generate_code()
    
    # Assert code exists
    assert "pca = PCA(n_components=2)" in code
    
    # Execute code
    namespace = {'df': df, 'pd': pd, 'display_html': lambda x: None}
    exec(code, namespace)
    
    # Verify result
    result_df = namespace['df']
    assert 'PC1' in result_df.columns
    assert 'PC2' in result_df.columns

def test_model_compare_generation(qapp, sample_data):
    """Test Model Comparison code generation and execution."""
    df = sample_data.copy()
    dialog = ModelComparisonDialog(df)
    
    # Simulate UI selections
    dialog.list_dependent.addItem("Target")
    dialog.list_independent.addItem("Sales")
    dialog.list_independent.addItem("Profit")
    
    # Select only a few fast models
    for name, chk in dialog.chk_models.items():
        chk.setChecked(False)
    dialog.chk_models["Random Forest"].setChecked(True)
    dialog.chk_models["Naive Bayes"].setChecked(True)
    
    # Disable plotting/HTML outputs for clean testing
    dialog.chk_table.setChecked(False)
    dialog.chk_roc.setChecked(False)
    
    code = dialog.generate_code()
    
    # Assert code exists
    assert "models['Random Forest'] = RandomForestClassifier" in code
    assert "models['Naive Bayes'] = GaussianNB" in code
    assert "accuracy_score" in code
    
    # Execute code
    namespace = {'df': df, 'pd': pd, 'np': np, 'display_html': lambda x: None}
    exec(code, namespace)
    
    # Verify result
    assert 'comp_df' in namespace
    comp_df = namespace['comp_df']
    assert len(comp_df) == 2

def test_kmeans_generation(qapp, sample_data):
    """Test K-Means clustering code generation and execution."""
    df = sample_data.copy()
    dialog = KMeansDialog(df)
    
    # Simulate UI selections
    dialog.list_x.addItem("Sales")
    dialog.list_x.addItem("Profit")
    
    dialog.spin_k.setValue(2)
    # Enable outputs to catch NameError in generated code
    dialog.chk_profile.setChecked(True)
    dialog.chk_plot.setChecked(True)
    dialog.cmb_style.setCurrentText("Seaborn")

    code = dialog.generate_code()

    # Execute code
    # Mock show_result and display_html
    namespace = {'df': df, 'pd': pd, 'np': np, 'plt': plt, 'sns': sns, 'show_result': lambda x, y: None}
    exec(code, namespace)
    
    # Verify result
    assert 'labels' in namespace
    assert len(namespace['labels']) == len(df)

def test_kmeans_auto_generation(qapp, sample_data):
    """Test K-Means auto-select k (Elbow Method) code generation."""
    df = sample_data.copy()
    dialog = KMeansDialog(df)
    
    # Simulate UI selections
    dialog.list_x.addItem("Sales")
    dialog.list_x.addItem("Profit")
    dialog.chk_auto.setChecked(True)
    dialog.spin_max_k.setValue(5)
    
    # Disable plotting/HTML outputs for clean testing
    dialog.chk_profile.setChecked(False)
    dialog.chk_plot.setChecked(False)
    
    code = dialog.generate_code()
    
    # Assert code exists for elbow method
    assert "find_elbow" in code
    assert "best_k =" in code
    
    # Execute code
    namespace = {'df': df, 'pd': pd, 'np': np, 'display_html': lambda x: None}
    exec(code, namespace)
    
    # Verify result
    assert 'labels' in namespace
    assert len(namespace['labels']) == len(df)
