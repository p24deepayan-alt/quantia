import unittest
import pandas as pd
import polars as pl
from quantia.ui.dialogs.regression import LinearRegressionDialog
from quantia.ui.dialogs.descriptive import DescriptiveStatsDialog
from quantia.ui.dialogs.filter_data import FilterDataDialog
from quantia.ui.dialogs.clean_data import CleanDataDialog
from PySide6.QtWidgets import QApplication
import sys

# Ensure a QApplication exists
app = QApplication.instance() or QApplication(sys.argv)

class TestDialogCodeGeneration(unittest.TestCase):
    def setUp(self):
        self.sample_df = pd.DataFrame({
            "target": [1, 2, 3, 4, 5],
            "feature1": [10, 20, 30, 40, 50],
            "cat_var": ["A", "B", "A", "B", "A"]
        })
        self.pl_df = pl.from_pandas(self.sample_df)

    def test_regression_code_gen(self):
        dialog = LinearRegressionDialog(self.sample_df)
        # Mock selection
        dialog.list_dependent.addItem("target")
        dialog.list_independent.addItem("feature1")
        
        code = dialog.generate_code()
        self.assertIn("import polars as pl", code)
        self.assertIn("if isinstance(df, pl.DataFrame):", code)
        self.assertIn("model_data = df.select(model_vars).drop_nulls().to_pandas()", code)

    def test_descriptive_stats_code_gen(self):
        dialog = DescriptiveStatsDialog(self.sample_df)
        dialog.list_targets.addItem("target")
        dialog.list_targets.addItem("cat_var")
        
        code = dialog.generate_code()
        self.assertIn("import polars as pl", code)
        self.assertIn("if isinstance(df, pl.DataFrame):", code)
        self.assertIn("_pdf = df.select(vars_to_analyze).to_pandas()", code)
        self.assertIn("count = int(s.count())", code)

    def test_filter_data_code_gen(self):
        dialog = FilterDataDialog(self.sample_df)
        dialog.list_targets.addItem("target")
        dialog.cmb_operator.setCurrentText("> (Greater Than)")
        dialog.txt_value.setText("3")
        
        code = dialog.generate_code()
        self.assertIn("import polars as pl", code)
        self.assertIn("df = df.filter(pl.col(target) > 3)", code)

    def test_clean_data_code_gen(self):
        dialog = CleanDataDialog(self.sample_df)
        dialog.list_targets.addItem("feature1")
        dialog.rad_impute.setChecked(True)
        dialog.cmb_strategy.setCurrentText("Mean")
        
        code = dialog.generate_code()
        self.assertIn("import polars as pl", code)
        self.assertIn("progress(int((i+1)/len(target_cols)*100))", code)
        self.assertIn("df = df.with_columns(pl.col(c).fill_null(pl.col(c).mean()))", code)

if __name__ == "__main__":
    unittest.main()
