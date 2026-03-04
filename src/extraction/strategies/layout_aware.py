from docling.document_converter import DocumentConverter
from pathlib import Path
from typing import Tuple
from .base import BaseExtractionStrategy
from src.models.extracted_document import ExtractedDocument, TextBlock, TableStructure
from src.models.provenance import BBox

class LayoutAwareStrategy(BaseExtractionStrategy):
    def __init__(self):
        self.converter = DocumentConverter()

    def extract(self, pdf_path: Path) -> Tuple[ExtractedDocument, float]:
        doc_id = pdf_path.stem
        extracted_doc = ExtractedDocument(doc_id=doc_id)
        
        # Convert using Docling
        result = self.converter.convert(str(pdf_path))
        doc = result.document
        
        # Extract Text Blocks from Docling's internal representation
        # Docling provides a rich structure. We iterate through its items.
        for i, item in enumerate(doc.texts):
            # item has .text and .prov (provenance)
            # Docling's BBox might need conversion
            bbox = BBox(x=0, y=0, w=0, h=0)
            page_num = 1
            
            if item.prov and len(item.prov) > 0:
                p = item.prov[0]
                page_num = p.page_no
                # Docling's bbox is often [x0, y0, x1, y1]
                if p.bbox:
                    bbox = BBox(
                        x=float(p.bbox.l),
                        y=float(p.bbox.t),
                        w=float(p.bbox.r - p.bbox.l),
                        h=float(p.bbox.b - p.bbox.t)
                    )

            extracted_doc.text_blocks.append(TextBlock(
                text=item.text,
                bbox=bbox,
                page_number=page_num
            ))

        # Extract Tables
        for table in doc.tables:
            page_num = 1
            if table.prov and len(table.prov) > 0:
                page_num = table.prov[0].page_no
            
            # Map Docling table to our TableStructure
            headers = [] # Docling tables have cells we can parse
            rows = []
            
            # Simplified mapping for now
            extracted_doc.tables.append(TableStructure(
                headers=["Table extracted by Docling"], # Placeholder for deeper parsing
                rows=[[cell.text for cell in row.cells] for row in table.data.rows],
                page_number=page_num
            ))

        # Confidence for Docling is high if it successfully converted
        confidence = 0.95 
        
        # Metadata
        extracted_doc.metadata["docling_conversion_time"] = result.pip_times.get("total", 0)
        
        return extracted_doc, confidence
