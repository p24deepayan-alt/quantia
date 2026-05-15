"""Persistence layer for Quantia Report Studio.

Handles serialization and deserialization of the Document domain model.
"""

from __future__ import annotations

import json
from uuid import UUID
from datetime import datetime
from typing import Any, Dict

from quantia.core.report.document import (
    Document, Page, Block, Binding, PageSize, Margins, Size, Point,
    BlockType, BindingKind
)

class ReportEncoder(json.JSONEncoder):
    """Custom JSON Encoder for Report Studio domain models."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (BlockType, BindingKind)):
            return obj.value
        if hasattr(obj, "__dataclass_fields__"):
            return {k: getattr(obj, k) for k in obj.__dataclass_fields__}
        return super().default(obj)

class ReportSerializer:
    """Handles converting between JSON strings and Document objects."""

    @staticmethod
    def to_json(doc: Document) -> str:
        """Serialize a Document to a JSON string."""
        data = ReportEncoder().default(doc)
        data["schema_version"] = "1.0"
        return json.dumps(data, indent=2, cls=ReportEncoder)

    @staticmethod
    def from_json(json_str: str) -> Document:
        """Deserialize a JSON string into a Document."""
        data = json.loads(json_str)
        return ReportSerializer._dict_to_document(data)

    @staticmethod
    def _dict_to_document(data: Dict[str, Any]) -> Document:
        doc = Document(
            document_id=UUID(data.get("document_id", str(Document().document_id))),
            title=data.get("title", "Untitled Report"),
            authors=data.get("authors", []),
            citation_style=data.get("citation_style", "apa7"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            modified_at=data.get("modified_at", datetime.now().isoformat()),
            page_size=ReportSerializer._dict_to_pagesize(data.get("page_size", {})),
            default_orientation=data.get("default_orientation", "portrait"),
            margins=ReportSerializer._dict_to_margins(data.get("margins", {})),
            document_variables=data.get("document_variables", {})
        )
        
        doc.pages = [ReportSerializer._dict_to_page(p) for p in data.get("pages", [])]
        return doc

    @staticmethod
    def _dict_to_pagesize(data: Dict[str, Any]) -> PageSize:
        return PageSize(
            name=data.get("name", "A4"),
            width_pt=data.get("width_pt", 595.0),
            height_pt=data.get("height_pt", 842.0)
        )

    @staticmethod
    def _dict_to_margins(data: Dict[str, Any]) -> Margins:
        return Margins(
            top=data.get("top", 72.0),
            bottom=data.get("bottom", 72.0),
            left=data.get("left", 72.0),
            right=data.get("right", 72.0)
        )

    @staticmethod
    def _dict_to_page(data: Dict[str, Any]) -> Page:
        page = Page(
            page_id=UUID(data.get("page_id", str(Page().page_id))),
            index=data.get("index", 0),
            size=ReportSerializer._dict_to_pagesize(data["size"]) if "size" in data and data["size"] else None,
            orientation=data.get("orientation"),
            margins=ReportSerializer._dict_to_margins(data["margins"]) if "margins" in data and data["margins"] else None,
            master_page_id=UUID(data["master_page_id"]) if data.get("master_page_id") else None,
        )
        page.blocks = [ReportSerializer._dict_to_block(b) for b in data.get("blocks", [])]
        return page

    @staticmethod
    def _dict_to_block(data: Dict[str, Any]) -> Block:
        binding_data = data.get("binding")
        binding = None
        if binding_data:
            binding = Binding(
                target_kind=BindingKind(binding_data.get("target_kind", "RESULT")),
                target_id=binding_data.get("target_id", ""),
                target_path=binding_data.get("target_path"),
                content_hash=binding_data.get("content_hash", ""),
                last_refreshed_at=datetime.fromisoformat(binding_data["last_refreshed_at"]) if binding_data.get("last_refreshed_at") else None,
                auto_refresh=binding_data.get("auto_refresh", False),
                display_filter=binding_data.get("display_filter")
            )

        pos_data = data.get("position", {})
        size_data = data.get("size", {})

        return Block(
            block_id=UUID(data.get("block_id", str(Block().block_id))),
            type=BlockType(data.get("type", "text")),
            position=Point(pos_data.get("x", 0.0), pos_data.get("y", 0.0)),
            size=Size(size_data.get("width", 300.0), size_data.get("height", 200.0)),
            rotation=data.get("rotation", 0.0),
            z_order=data.get("z_order", 0),
            locked=data.get("locked", False),
            hidden=data.get("hidden", False),
            opacity=data.get("opacity", 1.0),
            paragraph_style_id=data.get("paragraph_style_id", "Body"),
            content=data.get("content", {}),
            binding=binding,
            alt_text=data.get("alt_text")
        )
