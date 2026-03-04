from pydantic import BaseModel, Field, field_validator
from typing import List

class BBox(BaseModel):
    x: float
    y: float
    w: float
    h: float

    @field_validator("x", "y", "w", "h")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Coordinates and dimensions must be positive")
        return v

class ProvenanceEntry(BaseModel):
    doc_id: str
    page_number: int
    bbox: BBox
    content_hash: str

class ProvenanceChain(BaseModel):
    entries: List[ProvenanceEntry] = Field(default_factory=list)
