import pdfplumber
import hashlib
from pathlib import Path
from typing import Tuple
from .base import BaseExtractionStrategy
from src.models.extracted_document import ExtractedDocument, TextBlock
from src.models.provenance import BBox

class StandardExtractionStrategy(BaseExtractionStrategy):
    def extract(self, pdf_path: Path, max_pages: int = None, **kwargs) -> Tuple[ExtractedDocument, float]:
        doc_id = pdf_path.stem
        extracted_doc = ExtractedDocument(doc_id=doc_id)
        
        total_pages = 0
        pages_with_text = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            all_pages = pdf.pages
            if max_pages:
                all_pages = all_pages[:max_pages]
            
            total_pages = len(all_pages)
            total_conf = 0.0
            for i, page in enumerate(all_pages):
                page_num = i + 1
                text = page.extract_text()
                
                # Dynamic Confidence per page
                total_conf += self._get_page_confidence(page)

                if text:
                    pages_with_text += 1
                if text:
                    pages_with_text += 1
                    # Extract text as a single block per page to avoid word-level fragmentation
                    # Provenance is maintained at the page level for now.
                    extracted_doc.text_blocks.append(TextBlock(
                        text=text,
                        bbox=BBox(x=0, y=0, w=1000, h=1000), # Full page for now
                        page_number=page_num
                    ))

        confidence = total_conf / total_pages if total_pages > 0 else 0.0
        return extracted_doc, float(confidence)

    def _get_page_confidence(self, page) -> float:
        """Helper to calculate confidence for a single page."""
        text = page.extract_text() or ""
        if not text.strip():
            return 0.0
            
        tables = page.find_tables()
        if len(tables) > 0:
            return 0.6 # Low confidence if tables exist; Strategy B is better
            
        return 1.0
