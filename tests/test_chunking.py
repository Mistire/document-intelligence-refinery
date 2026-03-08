import pytest
from src.agents.chunker import SemanticChunker
from src.models.extracted_document import ExtractedDocument, TextBlock, TableStructure, Figure
from src.models.provenance import BBox

def test_chunk_document_basic():
    chunker = SemanticChunker()
    doc = ExtractedDocument(
        doc_id="test_doc",
        text_blocks=[
            TextBlock(text="Introduction", bbox=BBox(x=10, y=10, w=100, h=20), page_number=1),
            TextBlock(text="This is a paragraph.", bbox=BBox(x=10, y=40, w=200, h=50), page_number=1),
        ]
    )
    
    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 2
    assert chunks[0].content == "Introduction"
    assert chunks[0].parent_headers == ["Introduction"]
    assert chunks[1].content == "This is a paragraph."
    assert chunks[1].parent_headers == ["Introduction"]

def test_chunk_document_list_grouping():
    chunker = SemanticChunker()
    doc = ExtractedDocument(
        doc_id="test_doc",
        text_blocks=[
            TextBlock(text="My List", bbox=BBox(x=10, y=10, w=100, h=20), page_number=1),
            TextBlock(text="1. Item One", bbox=BBox(x=10, y=40, w=200, h=20), page_number=1),
            TextBlock(text="2. Item Two", bbox=BBox(x=10, y=60, w=200, h=20), page_number=1),
            TextBlock(text="Regular text", bbox=BBox(x=10, y=80, w=200, h=20), page_number=1),
        ]
    )
    
    chunks = chunker.chunk_document(doc)
    # 1. My List (Header)
    # 2. 1. Item One + 2. Item Two (List)
    # 3. Regular text
    assert len(chunks) == 3
    assert chunks[1].chunk_type == "list"
    assert "Item One" in chunks[1].content
    assert "Item Two" in chunks[1].content
    assert chunks[1].parent_headers == ["My List"]

def test_chunk_document_tables_and_figures():
    chunker = SemanticChunker()
    doc = ExtractedDocument(
        doc_id="test_doc",
        text_blocks=[
            TextBlock(text="Data Section", bbox=BBox(x=10, y=10, w=100, h=20), page_number=1),
        ],
        tables=[
            TableStructure(
                headers=["Col1", "Col2"],
                rows=[["Val1", "Val2"]],
                bbox=BBox(x=10, y=40, w=300, h=100),
                page_number=1
            )
        ],
        figures=[
            Figure(
                caption="Figure 1: Test Figure",
                bbox=BBox(x=10, y=150, w=300, h=200),
                page_number=1
            )
        ]
    )
    
    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 3 # Header, Table, Figure
    assert any(c.chunk_type == "table" for c in chunks)
    assert any(c.chunk_type == "figure" for c in chunks)
    
    figure_chunk = next(c for c in chunks if c.chunk_type == "figure")
    assert "Test Figure" in figure_chunk.content
    assert figure_chunk.parent_headers == ["Data Section"]
