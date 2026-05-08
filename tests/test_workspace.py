import os
from pathlib import Path
import pandas as pd
import pytest

from quantia.core.workspace import Workspace


@pytest.fixture
def temp_workspace_file(tmp_path: Path):
    return tmp_path / "test.quantia"


def test_workspace_initialization():
    ws = Workspace()
    assert len(ws.dataframe) == 0
    assert ws.script == ""
    assert len(ws.undo_stack) == 0
    assert len(ws.redo_stack) == 0
    assert ws.metadata["version"] == "1.0"


def test_workspace_undo_redo():
    ws = Workspace()
    
    df1 = pd.DataFrame({"A": [1, 2]})
    df2 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    df3 = pd.DataFrame({"A": [1, 2], "B": [3, 4], "C": [5, 6]})
    
    ws.dataframe = df1
    ws.record_state_change(df1, df2)
    assert len(ws.dataframe.columns) == 2
    assert len(ws.undo_stack) == 1
    
    ws.record_state_change(df2, df3)
    assert len(ws.dataframe.columns) == 3
    assert len(ws.undo_stack) == 2
    assert len(ws.redo_stack) == 0
    
    # Undo
    prev = ws.undo()
    assert prev is not None
    assert len(prev.columns) == 2
    assert len(ws.dataframe.columns) == 2
    assert len(ws.undo_stack) == 1
    assert len(ws.redo_stack) == 1
    
    # Redo
    next_df = ws.redo()
    assert next_df is not None
    assert len(next_df.columns) == 3
    assert len(ws.dataframe.columns) == 3
    assert len(ws.undo_stack) == 2
    assert len(ws.redo_stack) == 0


def test_workspace_save_load(temp_workspace_file):
    ws = Workspace()
    ws.dataframe = pd.DataFrame({"A": [1, 2, 3]})
    ws.script = "print('hello')"
    ws.metadata["name"] = "Test Project"
    
    # Push to undo stack
    df_old = pd.DataFrame({"A": [1, 2]})
    ws.push_undo_state(df_old)
    
    ws.save(temp_workspace_file)
    assert temp_workspace_file.exists()
    
    ws_loaded = Workspace.load(temp_workspace_file)
    assert len(ws_loaded.dataframe) == 3
    assert ws_loaded.script == "print('hello')"
    assert ws_loaded.metadata["name"] == "Test Project"
    assert len(ws_loaded.undo_stack) == 1
    assert len(ws_loaded.undo_stack[0]) == 2


def test_workspace_clear():
    ws = Workspace()
    ws.dataframe = pd.DataFrame({"A": [1]})
    ws.script = "test"
    ws.push_undo_state(pd.DataFrame())
    
    ws.clear()
    assert len(ws.dataframe) == 0
    assert ws.script == ""
    assert len(ws.undo_stack) == 0
    assert len(ws.redo_stack) == 0
    assert ws.filepath is None
