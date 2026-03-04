from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class OriginType(str, Enum):
    NATIVE_DIGITAL = "native_digital"
    SCANNED_IMAGE = "scanned_image"
    MIXED = "mixed"
    FORM_FILLABLE = "form_fillable"

class LayoutComplexity(str, Enum):
    SINGLE_COLUMN = "single_column"
    MULTI_COLUMN = "multi_column"
    TABLE_HEAVY = "table_heavy"
    FIGURE_HEAVY = "figure_heavy"
    MIXED = "mixed"

class ExtractionCost(str, Enum):
    FAST_TEXT_SUFFICIENT = "fast_text_sufficient" # Strategy A
    NEEDS_LAYOUT_MODEL = "needs_layout_model"    # Strategy B
    NEEDS_VISION_MODEL = "needs_vision_model"    # Strategy C

class DocumentProfile(BaseModel):
    doc_id: str
    filename: str
    total_pages: int
    
    # The 5 Mandatory Dimensions
    origin_type: OriginType
    layout_complexity: LayoutComplexity
    language: str = "en"  # Default to english for now
    domain_hint: str = "general"
    extraction_cost: ExtractionCost
    
    # Metadata for debugging
    avg_char_density: float
    avg_image_ratio: float
    total_tables_found: int
    triage_timestamp: str
