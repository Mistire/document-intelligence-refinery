from pydantic import BaseModel, Field
from typing import List, Optional

class IndexNode(BaseModel):
    id: str
    title: str
    level: int
    summary: str
    page_start: int
    page_end: int
    parent_id: Optional[str] = None
    child_ids: List[str] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)

class PageIndex(BaseModel):
    doc_id: str
    root_nodes: List[IndexNode]
