"""Workspace Management Module.

Handles saving, loading, and tracking the state of a Quantia workspace,
including datasets, scripts, undo/redo history, and metadata.
"""

from __future__ import annotations

import io
import json
import zipfile
from collections import deque
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl


class Workspace:
    """Represents a Quantia project workspace."""

    def __init__(self, max_history: int = 50) -> None:
        self.dataframe: pd.DataFrame | pl.DataFrame = pd.DataFrame()
        self.script: str = ""
        self.undo_stack: deque[pd.DataFrame | pl.DataFrame] = deque(maxlen=max_history)
        self.redo_stack: deque[pd.DataFrame | pl.DataFrame] = deque(maxlen=max_history)
        self.metadata: dict[str, Any] = {
            "version": "1.0",
            "name": "Untitled"
        }
        self.filepath: Path | None = None
        self._max_history = max_history

    def set_dataframe(self, df: pd.DataFrame | pl.DataFrame) -> None:
        """Set the current dataframe, clearing redo stack if changed."""
        self.dataframe = df

    def push_undo_state(self, df: pd.DataFrame | pl.DataFrame) -> None:
        """Push a dataframe state to the undo stack."""
        self.undo_stack.append(df.copy() if isinstance(df, pd.DataFrame) else df.clone())

    def record_state_change(self, old_df: pd.DataFrame | pl.DataFrame, new_df: pd.DataFrame | pl.DataFrame) -> None:
        """Push old state to undo stack, clear redo stack, and update current dataframe."""
        self.push_undo_state(old_df)
        self.redo_stack.clear()
        self.dataframe = new_df

    def undo(self) -> pd.DataFrame | pl.DataFrame | None:
        """Pop from undo stack, push current to redo stack, return previous state."""
        if not self.undo_stack:
            return None
        self.redo_stack.append(self.dataframe.copy() if isinstance(self.dataframe, pd.DataFrame) else self.dataframe.clone())
        prev_df = self.undo_stack.pop()
        self.dataframe = prev_df
        return prev_df

    def redo(self) -> pd.DataFrame | pl.DataFrame | None:
        """Pop from redo stack, push current to undo stack, return next state."""
        if not self.redo_stack:
            return None
        self.undo_stack.append(self.dataframe.copy() if isinstance(self.dataframe, pd.DataFrame) else self.dataframe.clone())
        next_df = self.redo_stack.pop()
        self.dataframe = next_df
        return next_df

    def clear(self) -> None:
        """Clear all data and history."""
        self.dataframe = pd.DataFrame()
        self.script = ""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.filepath = None

    def save(self, path: Path | str) -> None:
        """Serialize the workspace to a .quantia zip archive."""
        path_obj = Path(path)
        with zipfile.ZipFile(path_obj, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Metadata
            zf.writestr("metadata.json", json.dumps(self.metadata))

            # Dataframe
            if len(self.dataframe) > 0:
                df_bytes = io.BytesIO()
                if isinstance(self.dataframe, pl.DataFrame):
                    self.dataframe.write_parquet(df_bytes)
                else:
                    self.dataframe.to_parquet(df_bytes)
                zf.writestr("data.parquet", df_bytes.getvalue())

            # Script
            zf.writestr("script.py", self.script)

            # Undo stack
            for i, df in enumerate(self.undo_stack):
                df_bytes = io.BytesIO()
                if isinstance(df, pl.DataFrame):
                    df.write_parquet(df_bytes)
                else:
                    df.to_parquet(df_bytes)
                zf.writestr(f"undo_{i}.parquet", df_bytes.getvalue())

            # Redo stack
            for i, df in enumerate(self.redo_stack):
                df_bytes = io.BytesIO()
                if isinstance(df, pl.DataFrame):
                    df.write_parquet(df_bytes)
                else:
                    df.to_parquet(df_bytes)
                zf.writestr(f"redo_{i}.parquet", df_bytes.getvalue())
                
        self.filepath = path_obj

    @classmethod
    def load(cls, path: Path | str, max_history: int = 50) -> "Workspace":
        """Load a workspace from a .quantia zip archive."""
        workspace = cls(max_history=max_history)
        path_obj = Path(path)
        workspace.filepath = path_obj

        with zipfile.ZipFile(path_obj, "r") as zf:
            namelist = zf.namelist()
            
            if "metadata.json" in namelist:
                workspace.metadata = json.loads(zf.read("metadata.json"))

            if "data.parquet" in namelist:
                df_bytes = io.BytesIO(zf.read("data.parquet"))
                workspace.dataframe = pd.read_parquet(df_bytes)
            
            if "script.py" in namelist:
                workspace.script = zf.read("script.py").decode("utf-8")

            # Sorting by length then string to ensure undo_2, undo_10 works correctly.
            def extract_idx(name: str, prefix: str) -> int:
                try:
                    return int(name[len(prefix):-8]) # 'undo_X.parquet'
                except ValueError:
                    return -1

            undo_files = [n for n in namelist if n.startswith("undo_") and n.endswith(".parquet")]
            undo_files.sort(key=lambda n: extract_idx(n, "undo_"))
            for n in undo_files:
                df_bytes = io.BytesIO(zf.read(n))
                workspace.undo_stack.append(pd.read_parquet(df_bytes))

            redo_files = [n for n in namelist if n.startswith("redo_") and n.endswith(".parquet")]
            redo_files.sort(key=lambda n: extract_idx(n, "redo_"))
            for n in redo_files:
                df_bytes = io.BytesIO(zf.read(n))
                workspace.redo_stack.append(pd.read_parquet(df_bytes))

        return workspace