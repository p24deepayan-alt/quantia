"""Unit tests for TypeConvertDialog.

Tests cover:
1. Convert to Numeric (Strict + Whitespace handling)
2. Convert to String
3. Remove/Replace characters
4. Add Prefix/Suffix
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import pytest
from PySide6.QtWidgets import QApplication
from quantia.ui.dialogs.type_convert import TypeConvertDialog

# Ensure a single QApplication exists for the entire test session.
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def mixed_df():
    return pd.DataFrame({
        "NumericStr": [" 1 ", " 2.5", "3 "],
        "BadStr": ["1", "A", "3"],
        "Categorical": pd.Series([" 1", "2 ", " 3 "], dtype="category"),
        "BadCategorical": pd.Series(["1", "B", "3"], dtype="category"),
    })

class TestTypeConvertDialog:
    def test_to_numeric_success_pandas(self, qapp, mixed_df):
        dlg = TypeConvertDialog(mixed_df)
        dlg.list_targets.addItem("NumericStr")
        dlg.rad_to_numeric.setChecked(True)
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        assert "pd.to_numeric" in code
        assert "errors='raise'" in code

        df = mixed_df.copy()
        exec(code)
        assert pd.api.types.is_numeric_dtype(df["NumericStr"])
        assert list(df["NumericStr"]) == [1.0, 2.5, 3.0]

    def test_to_numeric_error_pandas(self, qapp, mixed_df):
        dlg = TypeConvertDialog(mixed_df)
        dlg.list_targets.addItem("BadStr")
        dlg.rad_to_numeric.setChecked(True)
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        df = mixed_df.copy()
        with pytest.raises(Exception):
            exec(code)

    def test_to_numeric_categorical_success_polars(self, qapp, mixed_df):
        dlg = TypeConvertDialog(mixed_df)
        dlg.list_targets.addItem("Categorical")
        dlg.rad_to_numeric.setChecked(True)
        dlg.rad_new_col.setChecked(True)

        code = dlg.generate_code()
        assert "str.strip_chars().cast(pl.Float64, strict=True)" in code

        # Simulate Polars execution
        df = pl.from_pandas(mixed_df)
        # The generated code expects 'df' in namespace
        ldict = {"df": df, "pl": pl}
        exec(code, globals(), ldict)
        df = ldict["df"]
        
        assert "Mod_Categorical" in df.columns
        assert df["Mod_Categorical"].dtype == pl.Float64
        assert df["Mod_Categorical"].to_list() == [1.0, 2.0, 3.0]

    def test_to_numeric_categorical_error_polars(self, qapp, mixed_df):
        dlg = TypeConvertDialog(mixed_df)
        dlg.list_targets.addItem("BadCategorical")
        dlg.rad_to_numeric.setChecked(True)
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        df = pl.from_pandas(mixed_df)
        ldict = {"df": df, "pl": pl}
        with pytest.raises(Exception):
            exec(code, globals(), ldict)

    def test_to_string(self, qapp, mixed_df):
        dlg = TypeConvertDialog(mixed_df)
        dlg.list_targets.addItem("NumericStr")
        dlg.rad_to_string.setChecked(True)
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        # Test pandas branch
        df = mixed_df.copy()
        exec(code)
        assert pd.api.types.is_string_dtype(df["NumericStr"])

    def test_replace_characters(self, qapp, mixed_df):
        dlg = TypeConvertDialog(mixed_df)
        dlg.list_targets.addItem("NumericStr")
        dlg.rad_replace.setChecked(True)
        dlg.txt_target.setText("2.5")
        dlg.txt_replace.setText("99")
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        df = mixed_df.copy()
        exec(code)
        # " 2.5" -> " 99"
        assert any("99" in str(v) for v in df["NumericStr"].values)

    def test_append_prefix_suffix(self, qapp, mixed_df):
        dlg = TypeConvertDialog(mixed_df)
        dlg.list_targets.addItem("NumericStr")
        dlg.rad_append.setChecked(True)
        dlg.txt_prefix.setText("PRE_")
        dlg.txt_suffix.setText("_POST")
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        df = mixed_df.copy()
        exec(code)
        # " 1 " -> "PRE_ 1 _POST"
        assert df["NumericStr"].iloc[0] == "PRE_ 1 _POST"
