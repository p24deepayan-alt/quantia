"""Tests for the Report Studio persistence layer."""

import pytest
from uuid import uuid4
from datetime import datetime

from quantia.core.report.document import (
    Document, Page, Block, Binding, PageSize, Margins, Size, Point,
    BlockType, BindingKind
)
from quantia.persistence.report.serializer import ReportSerializer

def test_document_serialization_roundtrip():
    # Setup test document
    doc = Document(title="Test Report", authors=["Alice", "Bob"])
    page = Page(index=0)
    
    # Add a text block
    text_block = Block(
        type=BlockType.TEXT,
        position=Point(100.5, 200.5),
        size=Size(400, 300),
        content={"text": "Hello World"}
    )
    
    # Add a bound plot block
    bound_block = Block(
        type=BlockType.BOUND_PLOT,
        binding=Binding(
            target_kind=BindingKind.PLOT,
            target_id="plot_123",
            content_hash="abc123hash"
        )
    )
    
    page.blocks = [text_block, bound_block]
    doc.pages = [page]
    
    # Serialize to JSON
    json_str = ReportSerializer.to_json(doc)
    
    # Check that schema_version is injected
    assert '"schema_version": "1.0"' in json_str
    
    # Deserialize back to Document
    doc2 = ReportSerializer.from_json(json_str)
    
    # Assert values survived the roundtrip
    assert doc2.title == "Test Report"
    assert doc2.authors == ["Alice", "Bob"]
    assert len(doc2.pages) == 1
    
    p = doc2.pages[0]
    assert len(p.blocks) == 2
    
    b1 = p.blocks[0]
    assert b1.type == BlockType.TEXT
    assert b1.position.x == 100.5
    assert b1.content["text"] == "Hello World"
    
    b2 = p.blocks[1]
    assert b2.type == BlockType.BOUND_PLOT
    assert b2.binding is not None
    assert b2.binding.target_kind == BindingKind.PLOT
    assert b2.binding.target_id == "plot_123"
    assert b2.binding.content_hash == "abc123hash"
