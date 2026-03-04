from pathlib import Path
from src.models.document_profile import DocumentProfile, ExtractionCost
from .strategies.standard import StandardExtractionStrategy
from .strategies.layout_aware import LayoutAwareStrategy

class ExtractionRouter:
    def __init__(self):
        self.strategies = {
            ExtractionCost.FAST_TEXT_SUFFICIENT: StandardExtractionStrategy(),
            ExtractionCost.NEEDS_LAYOUT_MODEL: LayoutAwareStrategy(),
            ExtractionCost.NEEDS_VISION_MODEL: LayoutAwareStrategy() # Use Docling for now (it has OCR)
        }

    def route(self, profile: DocumentProfile) -> Path:
        strategy = self.strategies.get(profile.extraction_cost)
        if not strategy:
            raise ValueError(f"Unknown extraction cost: {profile.extraction_cost}")
        
        # Determine output directory
        output_dir = Path(".refinery/extractions") / profile.doc_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = Path("data") / profile.filename
        return strategy.extract(pdf_path, output_dir)
