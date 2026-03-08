import pytest
import os
from unittest.mock import MagicMock, patch
from src.agents.indexer import PageIndexBuilder
from src.models.chunk import LDU
from src.models.provenance import BBox

@pytest.fixture
def mock_llm():
    with patch('src.agents.indexer.ChatOpenAI') as mock:
        yield mock

def test_build_index_hierarchy(mock_llm):
    # Setup mock LLM response
    mock_instance = mock_llm.return_value
    mock_response = MagicMock()
    mock_response.content = "This is a summary."
    mock_instance.invoke.return_value = mock_response

    indexer = PageIndexBuilder()
    chunks = [
        LDU(
            chunk_id="c1", doc_id="test", content="Intro text", 
            content_hash="h1", page_refs=[1], chunk_type="text",
            parent_headers=["Section 1"]
        ),
        LDU(
            chunk_id="c2", doc_id="test", content="Subsection text", 
            content_hash="h2", page_refs=[1], chunk_type="text",
            parent_headers=["Section 1", "Subsection A"]
        ),
        LDU(
            chunk_id="c3", doc_id="test", content="Table data", 
            content_hash="h3", page_refs=[2], chunk_type="table",
            parent_headers=["Section 2"]
        )
    ]
    
    index = indexer.build_index("test", chunks)
    
    # Root nodes should be "Section 1" and "Section 2" (if we use first header as root)
    # Actually, my implementation builds path levels.
    assert len(index.root_nodes) == 2
    titles = [n.title for n in index.root_nodes]
    assert "Section 1" in titles
    assert "Section 2" in titles
    
    s1 = next(n for n in index.root_nodes if n.title == "Section 1")
    assert len(s1.child_nodes) == 1
    assert s1.child_nodes[0].title == "Subsection A"
    assert "text" in s1.data_types_present
    
    s2 = next(n for n in index.root_nodes if n.title == "Section 2")
    assert "table" in s2.data_types_present
    assert s2.page_start == 2

def test_build_index_summary_and_entities(mock_llm):
    mock_instance = mock_llm.return_value
    mock_response = MagicMock()
    mock_response.content = "A summary of CBE Annual Report."
    mock_instance.invoke.return_value = mock_response

    indexer = PageIndexBuilder()
    chunks = [
        LDU(
            chunk_id="c1", doc_id="test", content="The Commercial Bank of Ethiopia (CBE) report for 2024.", 
            content_hash="h1", page_refs=[1], chunk_type="text",
            parent_headers=["Financials"]
        )
    ]
    
    index = indexer.build_index("test", chunks)
    node = index.root_nodes[0]
    assert node.summary == "A summary of CBE Annual Report."
    assert "Commercial" in node.key_entities or "Bank" in node.key_entities
