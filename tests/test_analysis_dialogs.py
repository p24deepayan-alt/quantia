import pytest
import pandas as pd
import numpy as np

# PySide6 imports needed for mocking Qt UI
from PySide6.QtWidgets import QApplication

from quantia.ui.dialogs.pivot_table import PivotTableDialog
from quantia.ui.dialogs.pca import PCADialog
from quantia.ui.dialogs.model_compare import ModelComparisonDialog

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
    """Create a sample dataset suitable for testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'Category': ['A', 'A', 'B', 'B', 'C', 'C'],
        'Region': ['North', 'South', 'North', 'South', 'North', 'South'],
        'Sales': [100, 150, 200, 250, 300, 350],
        'Profit': [10, 15, 20, 25, 30, 35],
        'Target': [0, 1, 0, 1, 0, 1]
    })


def test_pivot_table_group_by(qapp, sample_data):
    """Test generating a simple Group By aggregation."""
    df = sample_data.copy()
    dialog = PivotTableDialog(df)
    
    # Simulate UI selections
    dialog.list_groupby.addItem("Category")
    dialog.list_values.addItem("Sales")
    dialog.cmb_agg.setCurrentText("Sum")
    dialog.rad_overwrite.setChecked(True)
    
    code = dialog.generate_code()
    
    # Assert code exists
    assert "df.groupby(['Category'])['Sales'].agg('sum').reset_index()" in code
    
    # Execute code
    namespace = {'df': df, 'pd': pd}
    exec(code, namespace)
    
    # Verify result
    result_df = namespace['df']
    assert len(result_df) == 3
    assert result_df['Sales'].sum() == 1350


def test_pivot_table_pivot(qapp, sample_data):
    """Test generating a true Pivot Table."""
    df = sample_data.copy()
    dialog = PivotTableDialog(df)
    
    # Simulate UI selections
    dialog.list_groupby.addItem("Category")
    dialog.list_pivot.addItem("Region")
    dialog.list_values.addItem("Sales")
    dialog.cmb_agg.setCurrentText("Mean")
    dialog.rad_overwrite.setChecked(True)
    
    code = dialog.generate_code()
    
    # Assert code exists
    assert "pd.pivot_table(" in code
    assert "index=['Category']" in code
    assert "columns='Region'" in code
    
    # Execute code
    namespace = {'df': df, 'pd': pd}
    exec(code, namespace)
    
    # Verify result
    result_df = namespace['df']
    assert 'Sales_North' in result_df.columns
    assert 'Sales_South' in result_df.columns


def test_pca_generation(qapp, sample_data):
    """Test PCA dialog code generation and execution."""
    df = sample_data.copy()
    dialog = PCADialog(df)
    
    # Simulate UI selections
    dialog.list_features.addItem("Sales")
    dialog.list_features.addItem("Profit")
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
    # We need to mock display_html
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
    dialog.list_y.addItem("Target")
    dialog.list_x.addItem("Sales")
    dialog.list_x.addItem("Profit")
    
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
    # We need to mock display_html
    namespace = {'df': df, 'pd': pd, 'np': np, 'display_html': lambda x: None}
    exec(code, namespace)
    
    # Verify result
    # We should have a comp_df in the namespace
    assert 'comp_df' in namespace
    comp_df = namespace['comp_df']
    assert len(comp_df) == 2
    assert 'Random Forest' in comp_df.index
    assert 'Naive Bayes' in comp_df.index
    assert 'F1 Score' in comp_df.columns
