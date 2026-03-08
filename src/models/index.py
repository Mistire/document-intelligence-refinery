from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class IndexNode(BaseModel):
    id: str
    title: str
    level: int
    summary: str
    page_start: int
    page_end: int
    parent_id: Optional[str] = None
    child_nodes: List['IndexNode'] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)
    
    # Missing fields from challenge
    key_entities: List[str] = Field(default_factory=list)
    data_types_present: List[str] = Field(default_factory=list) # e.g., ["table", "figure"]

    @field_validator("page_end")
    @classmethod
    def validate_page_range(cls, v: int, info) -> int:
        if "page_start" in info.data and v < info.data["page_start"]:
            raise ValueError("page_end must be greater than or equal to page_start")
        return v

class PageIndex(BaseModel):
    doc_id: str
    root_nodes: List[IndexNode]
