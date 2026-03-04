from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class LDU(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    
    # Hierarchical Metadata
    parent_headers: List[str] = Field(default_factory=list)
    page_range: List[int] = Field(default_factory=list)
    
    # Structural Type
    chunk_type: str  # e.g., "text", "table", "list", "image_caption"
    
    # For Provenance
    source_metadata: Dict = Field(default_factory=dict)
