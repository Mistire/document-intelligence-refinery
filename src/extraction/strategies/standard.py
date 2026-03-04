import pdfplumber
import hashlib
from pathlib import Path
from typing import Tuple
from .base import BaseExtractionStrategy
from src.models.extracted_document import ExtractedDocument, TextBlock
from src.models.provenance import BBox

class StandardExtractionStrategy(BaseExtractionStrategy):
    def extract(self, pdf_path: Path) -> Tuple[ExtractedDocument, float]:
        doc_id = pdf_path.stem
        extracted_doc = ExtractedDocument(doc_id=doc_id)
        
        total_pages = 0
        pages_with_text = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text()
                
                if text:
                    pages_with_text += 1
                    # In a real implementation, we would extract individual words/blocks with BBoxes.
                    # For Standard (Strategy A), we treat the whole page as a block for simplicity 
                    # unless we want to do word-level extraction.
                    # pdfplumber.extract_words() gives BBoxes.
                    
                    words = page.extract_words()
                    for word in words:
                        extracted_doc.text_blocks.append(TextBlock(
                            text=word["text"],
                            bbox=BBox(
                                x=float(word["x0"]),
                                y=float(word["top"]),
                                w=float(word["x1"] - word["x0"]),
                                h=float(word["bottom"] - word["top"])
                            ),
                            page_number=page_num
                        ))

        # Confidence = ratio of pages that had at least some text
        confidence = pages_with_text / total_pages if total_pages > 0 else 0.0
        
        # Penalize confidence if many words are single characters or weird symbols
        # (Heuristic: simple digital PDFs usually extract cleanly)
        
        return extracted_doc, confidence
