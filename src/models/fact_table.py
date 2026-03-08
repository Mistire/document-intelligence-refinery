from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class FactEntry(BaseModel):
    key: str = Field(..., description="The name of the fact (e.g., 'Total Revenue')")
    value: str = Field(..., description="The value of the fact (e.g., '$4.2B')")
    unit: Optional[str] = Field(None, description="The unit of measurement")
    period: Optional[str] = Field(None, description="The time period (e.g., 'FY 2023')")
    page_number: int
    confidence: float
    source_text: str = Field(..., description="The exact text snippet this fact was extracted from")

class FactTable(BaseModel):
    doc_id: str
    facts: List[FactEntry] = []
