"""Unit tests for String Operation dialogs and Regression Interaction Terms.

Tests cover:
1. TextExtractDialog – text before/after delimiter
2. StringFormatDialog – case changes & trim
3. FindReplaceDialog – literal and regex replacement
4. ConcatColsDialog – column concatenation
5. IfElseDialog – conditional logic (numeric & string)
6. LinearRegressionDialog – interaction term UI + marginality in code gen
7. LogisticRegressionDialog – interaction term UI + marginality in code gen
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

# Ensure a single QApplication exists for the entire test session.
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ── Sample DataFrames ────────────────────────────────────────────────────────

@pytest.fixture
def str_df():
    return pd.DataFrame({
        "Name": ["Alice Smith", "Bob Jones", "Charlie Brown"],
        "City": ["  New York  ", "los angeles", "CHICAGO"],
        "Score": [85, 92, 78],
        "Status": ["active", "inactive", "active"],
    })


@pytest.fixture
def numeric_df():
    return pd.DataFrame({
        "Age": [25, 35, 45, 55],
        "Income": [50000, 75000, 100000, 125000],
        "Education": ["BS", "MS", "PhD", "BS"],
        "Target": [0, 1, 1, 0],
    })


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TextExtractDialog
# ═══════════════════════════════════════════════════════════════════════════════

class TestTextExtractDialog:
    def test_text_before(self, qapp, str_df):
        from quantia.ui.dialogs.text_extract import TextExtractDialog
        dlg = TextExtractDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.txt_delimiter.setText(" ")
        dlg.rad_before.setChecked(True)
        dlg.txt_new_col.setText("FirstName")

        code = dlg.generate_code()
        assert code != ""
        assert "str.split(' ').str[0]" in code
        assert "FirstName" in code

        # Execute the generated code against a copy
        df = str_df.copy()
        exec(code)
        assert list(df["FirstName"]) == ["Alice", "Bob", "Charlie"]

    def test_text_after(self, qapp, str_df):
        from quantia.ui.dialogs.text_extract import TextExtractDialog
        dlg = TextExtractDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.txt_delimiter.setText(" ")
        dlg.rad_after.setChecked(True)
        dlg.txt_new_col.setText("LastName")

        code = dlg.generate_code()
        assert "str.split(' ', n=1).str[1]" in code

        df = str_df.copy()
        exec(code)
        assert list(df["LastName"]) == ["Smith", "Jones", "Brown"]

    def test_overwrite_when_blank(self, qapp, str_df):
        """When new column name is blank, it should overwrite the target."""
        from quantia.ui.dialogs.text_extract import TextExtractDialog
        dlg = TextExtractDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.txt_delimiter.setText(" ")
        dlg.rad_before.setChecked(True)
        dlg.txt_new_col.setText("")  # blank → overwrite

        code = dlg.generate_code()
        assert "df['Name']" in code

    def test_missing_delimiter_returns_empty(self, qapp, str_df):
        from quantia.ui.dialogs.text_extract import TextExtractDialog
        dlg = TextExtractDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.txt_delimiter.setText("")  # no delimiter

        code = dlg.generate_code()
        assert code == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 2. StringFormatDialog
# ═══════════════════════════════════════════════════════════════════════════════

class TestStringFormatDialog:
    def test_uppercase(self, qapp, str_df):
        from quantia.ui.dialogs.string_format import StringFormatDialog
        dlg = StringFormatDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.cmb_operation.setCurrentText("UPPERCASE")
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        assert "str.upper()" in code

        df = str_df.copy()
        exec(code)
        assert df["Name"].iloc[0] == "ALICE SMITH"

    def test_lowercase(self, qapp, str_df):
        from quantia.ui.dialogs.string_format import StringFormatDialog
        dlg = StringFormatDialog(str_df)
        dlg.list_targets.addItem("City")
        dlg.cmb_operation.setCurrentText("lowercase")
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        df = str_df.copy()
        exec(code)
        assert df["City"].iloc[2] == "chicago"

    def test_title_case(self, qapp, str_df):
        from quantia.ui.dialogs.string_format import StringFormatDialog
        dlg = StringFormatDialog(str_df)
        dlg.list_targets.addItem("City")
        dlg.cmb_operation.setCurrentText("Title Case")
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        df = str_df.copy()
        exec(code)
        assert df["City"].iloc[2] == "Chicago"

    def test_trim(self, qapp, str_df):
        from quantia.ui.dialogs.string_format import StringFormatDialog
        dlg = StringFormatDialog(str_df)
        dlg.list_targets.addItem("City")
        dlg.cmb_operation.setCurrentText("Trim Whitespace (Leading & Trailing)")
        dlg.rad_overwrite.setChecked(True)

        code = dlg.generate_code()
        df = str_df.copy()
        exec(code)
        assert df["City"].iloc[0] == "New York"

    def test_new_col_output(self, qapp, str_df):
        from quantia.ui.dialogs.string_format import StringFormatDialog
        dlg = StringFormatDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.cmb_operation.setCurrentText("UPPERCASE")
        dlg.rad_new_col.setChecked(True)

        code = dlg.generate_code()
        df = str_df.copy()
        exec(code)
        assert "Formatted_Name" in df.columns
        assert df["Name"].iloc[0] == "Alice Smith"  # original unchanged

    def test_no_targets_returns_empty(self, qapp, str_df):
        from quantia.ui.dialogs.string_format import StringFormatDialog
        dlg = StringFormatDialog(str_df)
        # No targets added
        code = dlg.generate_code()
        assert code == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FindReplaceDialog
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindReplaceDialog:
    def test_literal_replace(self, qapp, str_df):
        from quantia.ui.dialogs.find_replace import FindReplaceDialog
        dlg = FindReplaceDialog(str_df)
        dlg.list_targets.addItem("Status")
        dlg.txt_find.setText("active")
        dlg.txt_replace.setText("ACTIVE")
        dlg.chk_regex.setChecked(False)
        dlg.txt_new_col.setText("")

        code = dlg.generate_code()
        assert "str.replace" in code
        assert "regex=False" in code

        df = str_df.copy()
        exec(code)
        assert df["Status"].iloc[0] == "ACTIVE"

    def test_regex_replace(self, qapp, str_df):
        from quantia.ui.dialogs.find_replace import FindReplaceDialog
        dlg = FindReplaceDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.txt_find.setText(r"\s+")
        dlg.txt_replace.setText("_")
        dlg.chk_regex.setChecked(True)
        dlg.txt_new_col.setText("Name_Fixed")

        code = dlg.generate_code()
        assert "regex=True" in code

        df = str_df.copy()
        exec(code)
        assert df["Name_Fixed"].iloc[0] == "Alice_Smith"

    def test_remove_text(self, qapp, str_df):
        """Empty replace → delete the match."""
        from quantia.ui.dialogs.find_replace import FindReplaceDialog
        dlg = FindReplaceDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.txt_find.setText(" ")
        dlg.txt_replace.setText("")  # remove spaces
        dlg.chk_regex.setChecked(False)
        dlg.txt_new_col.setText("")

        code = dlg.generate_code()
        df = str_df.copy()
        exec(code)
        assert df["Name"].iloc[0] == "AliceSmith"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ConcatColsDialog
# ═══════════════════════════════════════════════════════════════════════════════

class TestConcatColsDialog:
    def test_concat_two_cols(self, qapp, str_df):
        from quantia.ui.dialogs.concat_cols import ConcatColsDialog
        dlg = ConcatColsDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.list_targets.addItem("City")
        dlg.txt_sep.setText(" - ")
        dlg.txt_new_col.setText("Combined")

        code = dlg.generate_code()
        assert code != ""
        assert "Combined" in code

        df = str_df.copy()
        exec(code)
        assert "Alice Smith" in df["Combined"].iloc[0]
        assert " - " in df["Combined"].iloc[0]

    def test_concat_no_separator(self, qapp, str_df):
        from quantia.ui.dialogs.concat_cols import ConcatColsDialog
        dlg = ConcatColsDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.list_targets.addItem("Status")
        dlg.txt_sep.setText("")  # no separator
        dlg.txt_new_col.setText("Joined")

        code = dlg.generate_code()
        df = str_df.copy()
        exec(code)
        assert df["Joined"].iloc[0] == "Alice Smithactive"

    def test_less_than_two_cols_returns_empty(self, qapp, str_df):
        from quantia.ui.dialogs.concat_cols import ConcatColsDialog
        dlg = ConcatColsDialog(str_df)
        dlg.list_targets.addItem("Name")  # only one
        dlg.txt_new_col.setText("Out")

        code = dlg.generate_code()
        assert code == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 5. IfElseDialog
# ═══════════════════════════════════════════════════════════════════════════════

class TestIfElseDialog:
    def test_numeric_greater_than(self, qapp, str_df):
        from quantia.ui.dialogs.if_else import IfElseDialog
        dlg = IfElseDialog(str_df)
        dlg.list_targets.addItem("Score")
        dlg.cmb_operator.setCurrentText("Greater Than (>)")
        dlg.txt_value.setText("80")
        dlg.txt_true.setText("High")
        dlg.txt_false.setText("Low")
        dlg.txt_new_col.setText("ScoreCategory")

        code = dlg.generate_code()
        assert "np.where" in code
        assert "> 80" in code

        df = str_df.copy()
        exec(code)
        assert list(df["ScoreCategory"]) == ["High", "High", "Low"]

    def test_string_equals(self, qapp, str_df):
        from quantia.ui.dialogs.if_else import IfElseDialog
        dlg = IfElseDialog(str_df)
        dlg.list_targets.addItem("Status")
        dlg.cmb_operator.setCurrentText("Equals (==)")
        dlg.txt_value.setText("active")
        dlg.txt_true.setText("1")
        dlg.txt_false.setText("0")
        dlg.txt_new_col.setText("IsActive")

        code = dlg.generate_code()
        assert "np.where" in code

        df = str_df.copy()
        exec(code)
        assert list(df["IsActive"]) == [1, 0, 1]

    def test_contains(self, qapp, str_df):
        from quantia.ui.dialogs.if_else import IfElseDialog
        dlg = IfElseDialog(str_df)
        dlg.list_targets.addItem("Name")
        dlg.cmb_operator.setCurrentText("Contains (string)")
        dlg.txt_value.setText("Smith")
        dlg.txt_true.setText("Yes")
        dlg.txt_false.setText("No")
        dlg.txt_new_col.setText("HasSmith")

        code = dlg.generate_code()
        assert "str.contains" in code

        df = str_df.copy()
        exec(code)
        assert list(df["HasSmith"]) == ["Yes", "No", "No"]

    def test_is_missing(self, qapp):
        from quantia.ui.dialogs.if_else import IfElseDialog
        df_na = pd.DataFrame({"Val": [1, None, 3]})
        dlg = IfElseDialog(df_na)
        dlg.list_targets.addItem("Val")
        dlg.cmb_operator.setCurrentText("Is Missing (NA)")
        dlg.txt_value.setText("")  # not used for Is Missing
        dlg.txt_true.setText("Missing")
        dlg.txt_false.setText("Present")
        dlg.txt_new_col.setText("Status")

        code = dlg.generate_code()
        assert "isna()" in code

        df = df_na.copy()
        exec(code)
        assert list(df["Status"]) == ["Present", "Missing", "Present"]

    def test_missing_true_false_returns_empty(self, qapp, str_df):
        from quantia.ui.dialogs.if_else import IfElseDialog
        dlg = IfElseDialog(str_df)
        dlg.list_targets.addItem("Score")
        dlg.cmb_operator.setCurrentText("Greater Than (>)")
        dlg.txt_value.setText("80")
        dlg.txt_true.setText("")
        dlg.txt_false.setText("")
        dlg.txt_new_col.setText("Result")

        code = dlg.generate_code()
        assert code == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 6. LinearRegressionDialog – Interaction Terms
# ═══════════════════════════════════════════════════════════════════════════════

class TestLinearRegressionInteractions:
    def test_add_interaction_pair(self, qapp, numeric_df):
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        # Simulate moving items to the independent list
        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")

        # Select both items
        for i in range(dlg.list_independent.count()):
            dlg.list_independent.item(i).setSelected(True)

        dlg._add_interaction()
        assert dlg.list_interactions.count() == 1
        assert dlg.list_interactions.item(0).text() == "Age * Income"

    def test_add_interaction_three_vars(self, qapp, numeric_df):
        """Selecting 3 vars should produce 3 pairwise interactions."""
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")
        dlg.list_independent.addItem("Education")

        for i in range(dlg.list_independent.count()):
            dlg.list_independent.item(i).setSelected(True)

        dlg._add_interaction()
        terms = [dlg.list_interactions.item(i).text() for i in range(dlg.list_interactions.count())]
        assert len(terms) == 3
        assert "Age * Income" in terms
        assert "Age * Education" in terms
        assert "Income * Education" in terms

    def test_no_duplicate_interactions(self, qapp, numeric_df):
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")

        for i in range(dlg.list_independent.count()):
            dlg.list_independent.item(i).setSelected(True)

        dlg._add_interaction()
        dlg._add_interaction()  # second call should NOT duplicate
        assert dlg.list_interactions.count() == 1

    def test_remove_interaction(self, qapp, numeric_df):
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        dlg.list_interactions.addItem("Age * Income")
        dlg.list_interactions.item(0).setSelected(True)
        dlg._remove_interaction()
        assert dlg.list_interactions.count() == 0

    def test_code_gen_with_interaction(self, qapp, numeric_df):
        """Generated code should create interaction columns."""
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        dlg.list_dependent.addItem("Target")
        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")
        dlg.list_interactions.addItem("Age * Income")
        dlg.chk_stepwise.setChecked(False)

        code = dlg.generate_code()
        assert "interaction_vars" in code
        assert "Age * Income" in code
        assert "var_groups" in code

    def test_stepwise_marginality_add(self, qapp, numeric_df):
        """Stepwise code must gate interaction behind constituent vars."""
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        dlg.list_dependent.addItem("Target")
        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")
        dlg.list_interactions.addItem("Age * Income")
        dlg.chk_stepwise.setChecked(True)
        dlg.cmb_criterion.setCurrentText("AIC (Bidirectional)")

        code = dlg.generate_code()
        # The add-candidate filter must check constituents
        assert "if ' * ' in v:" in code
        assert "p1, p2 = v.split(' * ')" in code
        assert "if p1 in current_vars and p2 in current_vars:" in code

    def test_stepwise_marginality_drop(self, qapp, numeric_df):
        """Stepwise code must prevent dropping a var that anchors an interaction."""
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        dlg.list_dependent.addItem("Target")
        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")
        dlg.list_interactions.addItem("Age * Income")
        dlg.chk_stepwise.setChecked(True)
        dlg.cmb_criterion.setCurrentText("AIC (Bidirectional)")

        code = dlg.generate_code()
        assert "can_drop = True" in code
        assert "can_drop = False" in code

    def test_constituents_auto_added(self, qapp, numeric_df):
        """If an interaction is present but a constituent is missing from
        indep_vars, generate_code should auto-add it."""
        from quantia.ui.dialogs.regression import LinearRegressionDialog
        dlg = LinearRegressionDialog(numeric_df)

        dlg.list_dependent.addItem("Target")
        dlg.list_independent.addItem("Age")
        # Income intentionally NOT added
        dlg.list_interactions.addItem("Age * Income")
        dlg.chk_stepwise.setChecked(False)

        code = dlg.generate_code()
        # Income must appear in the model_vars
        assert "'Income'" in code


# ═══════════════════════════════════════════════════════════════════════════════
# 7. LogisticRegressionDialog – Interaction Terms
# ═══════════════════════════════════════════════════════════════════════════════

class TestLogisticRegressionInteractions:
    def test_add_interaction_pair(self, qapp, numeric_df):
        from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
        dlg = LogisticRegressionDialog(numeric_df)

        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")

        for i in range(dlg.list_independent.count()):
            dlg.list_independent.item(i).setSelected(True)

        dlg._add_interaction()
        assert dlg.list_interactions.count() == 1
        assert dlg.list_interactions.item(0).text() == "Age * Income"

    def test_code_gen_with_interaction(self, qapp, numeric_df):
        from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
        dlg = LogisticRegressionDialog(numeric_df)

        dlg.list_dependent.addItem("Target")
        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")
        dlg.list_interactions.addItem("Age * Income")
        dlg.chk_stepwise.setChecked(False)

        code = dlg.generate_code()
        assert "interaction_vars" in code
        assert "Age * Income" in code

    def test_stepwise_marginality(self, qapp, numeric_df):
        from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
        dlg = LogisticRegressionDialog(numeric_df)

        dlg.list_dependent.addItem("Target")
        dlg.list_independent.addItem("Age")
        dlg.list_independent.addItem("Income")
        dlg.list_interactions.addItem("Age * Income")
        dlg.chk_stepwise.setChecked(True)
        dlg.cmb_criterion.setCurrentText("AIC (Bidirectional)")

        code = dlg.generate_code()
        assert "if ' * ' in v:" in code
        assert "can_drop = True" in code

    def test_constituents_auto_added(self, qapp, numeric_df):
        from quantia.ui.dialogs.logistic_regression import LogisticRegressionDialog
        dlg = LogisticRegressionDialog(numeric_df)

        dlg.list_dependent.addItem("Target")
        dlg.list_independent.addItem("Age")
        # Income intentionally NOT added
        dlg.list_interactions.addItem("Age * Income")
        dlg.chk_stepwise.setChecked(False)

        code = dlg.generate_code()
        assert "'Income'" in code
