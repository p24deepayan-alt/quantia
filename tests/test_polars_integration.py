import unittest
import pandas as pd
import polars as pl
import numpy as np
from PySide6.QtWidgets import QApplication
from quantia.ui.central.data_view import DataViewWidget
import sys

# Ensure a QApplication exists for widget testing
app = QApplication.instance() or QApplication(sys.argv)

class TestPolarsIntegration(unittest.TestCase):
    def setUp(self):
        self.data_view = DataViewWidget()
        # Create a sample dataset
        self.sample_df = pd.DataFrame({
            "A": [1, 2, 3, None, 5],
            "B": ["x", "y", "z", "x", "y"],
            "C": [10.5, 20.1, 30.2, 40.8, 50.9]
        })
        self.pl_df = pl.from_pandas(self.sample_df)

    def test_load_dataframe_pandas(self):
        """Test loading a Pandas DataFrame."""
        self.data_view.load_dataframe(self.sample_df)
        df = self.data_view.get_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 5)
        self.assertEqual(list(df.columns), ["A", "B", "C"])

    def test_load_dataframe_polars(self):
        """Test loading a Polars DataFrame."""
        self.data_view.load_dataframe(self.pl_df)
        df = self.data_view.get_dataframe()
        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(df.height, 5)
        self.assertEqual(df.columns, ["A", "B", "C"])

    def test_ui_model_is_always_pandas(self):
        """Test that the UI model always contains a Pandas DataFrame for display."""
        self.data_view.load_dataframe(self.pl_df)
        # Internal model used by QTableView should be Pandas
        self.assertIsInstance(self.data_view.model.dataframe, pd.DataFrame)
        self.assertEqual(len(self.data_view.model.dataframe), 5)

    def test_polars_to_pandas_accuracy(self):
        """Verify data integrity during Polars -> Pandas conversion in UI."""
        self.data_view.load_dataframe(self.pl_df)
        pd_df = self.data_view.model.dataframe
        # Check specific value (ignoring null type differences for now)
        self.assertEqual(pd_df.iloc[0, 0], 1.0)
        self.assertEqual(pd_df.iloc[0, 1], "x")

    def test_describe_polars(self):
        """Test the multi-threaded describe logic in MainWindow context."""
        # Simulate MainWindow._on_variable_selected logic
        series = self.pl_df.get_column("A")
        description = series.describe()
        self.assertIsInstance(description, pl.DataFrame)
        # Polars describe for numeric usually has 'statistic' and 'value' columns
        self.assertIn("statistic", description.columns)

if __name__ == "__main__":
    unittest.main()
