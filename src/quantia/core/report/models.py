"""Data models for the Report Maker."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict


@dataclass
class ReportBlock:
    """Base class for all report components."""
    type: str
    x: float = 0.0
    y: float = 0.0
    width: float = 300.0
    height: float = 200.0
    page: int = 0
    z_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ReportBlock:
        btype = data.get("type")
        if btype == "text":
            return TextBlock(**{k: v for k, v in data.items() if k != "type"})
        elif btype == "plot":
            return PlotBlock(**{k: v for k, v in data.items() if k != "type"})
        elif btype == "table":
            return TableBlock(**{k: v for k, v in data.items() if k != "type"})
        raise ValueError(f"Unknown block type: {btype}")


@dataclass
class TextBlock(ReportBlock):
    """A block of custom text."""
    title: str = ""
    content: str = ""
    font_family: str = "Segoe UI"
    font_size: int = 10
    alignment: str = "Left"
    type: str = "text"


@dataclass
class PlotBlock(ReportBlock):
    """A block containing a plot."""
    plot_type: str = "Scatter"
    x_var: Optional[str] = None
    y_var: Optional[str] = None
    hue: Optional[str] = None
    title: str = ""
    type: str = "plot"


@dataclass
class TableBlock(ReportBlock):
    """A block containing a data table or statistical summary."""
    title: str = ""
    rows_limit: int = 20
    type: str = "table"


@dataclass
class ReportConfig:
    """Global report settings and collection of blocks."""
    title: str = "My Report"
    page_size: str = "A4"  # A4, Letter, or custom (e.g. "210mm 297mm")
    orientation: str = "portrait"  # portrait, landscape
    theme: str = "Light"
    num_pages: int = 1
    blocks: List[ReportBlock] = field(default_factory=list)

    def to_json(self) -> str:
        data = asdict(self)
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> ReportConfig:
        data = json.loads(json_str)
        blocks_data = data.pop("blocks", [])
        config = cls(**data)
        config.blocks = [ReportBlock.from_dict(b) for b in blocks_data]
        return config
