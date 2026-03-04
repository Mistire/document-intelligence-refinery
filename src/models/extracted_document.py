from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from src.models.provenance import BBox

class TextBlock(BaseModel):
    text: str
    bbox: BBox
    page_number: int

class TableStructure(BaseModel):
    headers: List[str]
    rows: List[List[Any]]
    bbox: Optional[BBox] = None
    page_number: int

class Figure(BaseModel):
    caption: Optional[str] = None
    bbox: BBox
    page_number: int

class ExtractedDocument(BaseModel):
    doc_id: str
    text_blocks: List[TextBlock] = Field(default_factory=list)
    tables: List[TableStructure] = Field(default_factory=list)
    figures: List[Figure] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
