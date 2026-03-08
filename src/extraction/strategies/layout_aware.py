from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pathlib import Path
from typing import Tuple
from .base import BaseExtractionStrategy
from src.models.extracted_document import ExtractedDocument, TextBlock, TableStructure
from src.models.provenance import BBox

class LayoutAwareStrategy(BaseExtractionStrategy):
    def __init__(self):
        self.converter = DocumentConverter()

    def extract(self, pdf_path: Path, max_pages: int = None, **kwargs) -> Tuple[ExtractedDocument, float]:
        print(f"🚀 Refinery Layout Strategy [v1.1-robust] active for: {pdf_path.name}")
        doc_id = pdf_path.stem
        extracted_doc = ExtractedDocument(doc_id=doc_id)
        
        # Convert using Docling with page limits and OCR optimization
        pipeline_options = PdfPipelineOptions()
        is_scanned = kwargs.get("is_scanned", False)
        
        # Heuristic: Only do OCR if the document is scanned or specifically requested
        pipeline_options.do_ocr = is_scanned
        pipeline_options.do_table_structure = True # Always want tables structured
        
        if max_pages:
            # We will pass this to converter.convert() instead
            pass
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(
            str(pdf_path),
            page_range=(1, max_pages) if max_pages else (1, 9999)
        )
        doc = result.document
        
        # Filter items by page number if max_pages is set
        def filtered_items(items):
            if not max_pages:
                return items
            return [it for it in items if it.prov and len(it.prov) > 0 and it.prov[0].page_no <= max_pages]
        
        # Extract Text Blocks from Docling's internal representation
        # Docling provides a rich structure. We iterate through its items.
        for i, item in enumerate(filtered_items(doc.texts)):
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
                        x=max(0.0, float(p.bbox.l)),
                        y=max(0.0, float(p.bbox.t)),
                        w=max(0.0, float(p.bbox.r - p.bbox.l)),
                        h=max(0.0, float(p.bbox.b - p.bbox.t))
                    )

            extracted_doc.text_blocks.append(TextBlock(
                text=item.text,
                bbox=bbox,
                page_number=page_num
            ))

        # Extract Tables
        for table in filtered_items(doc.tables):
            page_num = 1
            if table.prov and len(table.prov) > 0:
                page_num = table.prov[0].page_no
            
            # Use export_to_dataframe for robust table extraction
            try:
                # Pass 'doc' to avoid deprecation warning
                df = table.export_to_dataframe(doc=doc)
                # Ensure headers are strings for Pydantic validation
                headers = [str(col) for col in df.columns.tolist()]
                rows = df.values.tolist()
            except Exception as e:
                print(f"⚠️ Table extraction failed: {e}")
                headers = ["Extraction Failed"]
                rows = []
            
            extracted_doc.tables.append(TableStructure(
                headers=headers,
                rows=rows,
                page_number=page_num
            ))

        # Confidence for Docling is high if it successfully converted
        # Confidence: High if structure was successfully found
        if len(extracted_doc.tables) > 0 or len(extracted_doc.text_blocks) > 0:
            confidence = 0.90
        else:
            confidence = 0.10 # Complete failure to find structure, escalate to C
        
        # Metadata - Defensive check for pip_times
        conv_time = 0
        try:
            if hasattr(result, "pip_times") and result.pip_times:
                conv_time = result.pip_times.get("total", 0)
        except:
            pass
        extracted_doc.metadata["docling_conversion_time"] = conv_time
        extracted_doc.metadata["refinery_version"] = "v1.1-robust-tables"
        
        return extracted_doc, confidence
