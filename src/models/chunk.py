from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from src.models.provenance import BBox

class LDU(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    content_hash: str  # Added for verification
    
    # Hierarchical Metadata
    parent_headers: List[str] = Field(default_factory=list)
    page_refs: List[int] = Field(default_factory=list) # Replaces page_range
    
    # Structural Type
    chunk_type: str  # e.g., "text", "table", "list", "image_caption"
    
    # Spatial Metadata (Requested)
    bbox: Optional[BBox] = None
    
    # For Provenance
    source_metadata: Dict = Field(default_factory=dict)
