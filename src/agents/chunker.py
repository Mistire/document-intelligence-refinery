import re
import hashlib
from pathlib import Path
from typing import List
from src.models.chunk import LDU
from src.models.extracted_document import ExtractedDocument
from src.models.provenance import BBox

class SemanticChunker:
    def __init__(self, max_tokens: int = 1000):
        self.max_tokens = max_tokens

    def chunk_document(self, doc: ExtractedDocument) -> List[LDU]:
        chunks = []
        
        # 1. Process Text Blocks
        # For simplicity in this refinement, we group text blocks into logical units.
        # Here we treat each distinct block from the extraction as a candidate chunk.
        for block in doc.text_blocks:
            content = block.text.strip()
            if not content:
                continue
                
            chunk_id = f"{doc.doc_id}_text_{len(chunks)}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            chunks.append(LDU(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                content=content,
                content_hash=content_hash,
                page_refs=[block.page_number],
                chunk_type="text",
                bbox=block.bbox
            ))
            
        # 2. Process Tables
        for table in doc.tables:
            # Reconstruct a markdown-like representation for table content
            table_content = " | ".join(table.headers) + "\n"
            table_content += "-" * len(table_content) + "\n"
            for row in table.rows:
                table_content += " | ".join([str(c) for c in row]) + "\n"
            
            chunk_id = f"{doc.doc_id}_table_{len(chunks)}"
            content_hash = hashlib.sha256(table_content.encode()).hexdigest()
            
            chunks.append(LDU(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                content=table_content,
                content_hash=content_hash,
                page_refs=[table.page_number],
                chunk_type="table",
                bbox=table.bbox
            ))
            
        return chunks
