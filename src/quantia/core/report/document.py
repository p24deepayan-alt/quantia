"""Domain data models for Quantia Report Studio.

This module contains pure Python dataclasses representing the report document.
These models map directly to the JSON schema in the specification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class BlockType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    STATIC_TABLE = "static_table"
    BOUND_TABLE = "bound_table"
    APA_RESULT = "apa_result"
    BOUND_PLOT = "bound_plot"
    IMAGE = "image"
    SHAPE = "shape"
    CAPTION = "caption"
    PAGE_BREAK = "page_break"

class BindingKind(str, Enum):
    RESULT = "RESULT"
    PLOT = "PLOT"
    TABLE = "TABLE"
    DATAFRAME = "DATAFRAME"
    VARIABLE = "VARIABLE"

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Size:
    width: float
    height: float

@dataclass
class Margins:
    top: float
    bottom: float
    left: float
    right: float

@dataclass
class PageSize:
    name: str
    width_pt: float
    height_pt: float

@dataclass
class Binding:
    target_kind: BindingKind
    target_id: str
    target_path: Optional[str] = None
    content_hash: str = ""
    last_refreshed_at: Optional[datetime] = None
    auto_refresh: bool = False
    display_filter: Optional[Dict[str, Any]] = None

@dataclass
class BlockContent:
    """Base class for block-specific payloads."""
    pass

@dataclass
class TextContent(BlockContent):
    text: str = ""

@dataclass
class HeadingContent(BlockContent):
    text: str = ""
    level: int = 1

@dataclass
class BoundTableContent(BlockContent):
    table_style_id: str = "APATable"
    show_header: bool = True
    decimal_places: int = 3

@dataclass
class BoundPlotContent(BlockContent):
    export_dpi: int = 300

@dataclass
class Block:
    """Atomic unit of report content."""
    block_id: UUID = field(default_factory=uuid4)
    type: BlockType = BlockType.TEXT
    position: Point = field(default_factory=lambda: Point(0, 0))
    size: Size = field(default_factory=lambda: Size(300, 200))
    rotation: float = 0.0
    z_order: int = 0
    locked: bool = False
    hidden: bool = False
    opacity: float = 1.0
    paragraph_style_id: Optional[str] = "Body"
    content: Dict[str, Any] = field(default_factory=dict)
    binding: Optional[Binding] = None
    alt_text: Optional[str] = None

@dataclass
class Page:
    """A single physical page sheet."""
    page_id: UUID = field(default_factory=uuid4)
    index: int = 0
    size: Optional[PageSize] = None
    orientation: Optional[str] = None
    margins: Optional[Margins] = None
    master_page_id: Optional[UUID] = None
    blocks: List[Block] = field(default_factory=list)

@dataclass
class Document:
    """The root of a Quantia Report Studio document."""
    document_id: UUID = field(default_factory=uuid4)
    title: str = "Untitled Report"
    authors: List[str] = field(default_factory=list)
    citation_style: str = "apa7"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    page_size: PageSize = field(default_factory=lambda: PageSize("A4", 595.0, 842.0))
    default_orientation: str = "portrait"
    margins: Margins = field(default_factory=lambda: Margins(72.0, 72.0, 72.0, 72.0))
    pages: List[Page] = field(default_factory=list)
    document_variables: Dict[str, str] = field(default_factory=dict)
