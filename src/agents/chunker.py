import re
import hashlib
from pathlib import Path
from typing import List
from src.models.chunk import LDU
from src.models.extracted_document import ExtractedDocument
from src.models.provenance import BBox

class ChunkValidator:
    @staticmethod
    def validate_ldu(ldu: LDU) -> bool:
        """Verify semantic rules are respected."""
        # 1. Table integrity check
        if ldu.chunk_type == "table":
            if "|" not in ldu.content:
                return False
        # 2. List integrity
        if ldu.chunk_type == "list":
            if "\n" not in ldu.content and not re.match(r'^(\d+\.|[A-Za-z]\.|•|\-)\s+', ldu.content):
                return False
        # 3. Provenance check
        if not ldu.page_refs:
            return False
            
        return True

class SemanticChunker:
    def __init__(self, max_tokens: int = 1000):
        self.max_tokens = max_tokens
        self.validator = ChunkValidator()

    def _flush_buffer(self, chunks: List[LDU], buffer: List[str], pages: List[int], headers: List[str], doc_id: str):
        if not buffer:
            return
            
        full_content = " ".join(buffer) # Use space for merging regular text
        chunk_id = f"{doc_id}_text_{len(chunks)}"
        
        ldu = LDU(
            chunk_id=chunk_id,
            doc_id=doc_id,
            content=full_content,
            content_hash=hashlib.sha256(full_content.encode()).hexdigest(),
            page_refs=sorted(list(set(pages))),
            chunk_type="text",
            bbox=BBox(x=0, y=0, w=1000, h=1000), # Approximated for merged blocks
            parent_headers=list(headers)
        )
        
        # Resolve Cross-refs in the merged content
        refs = re.findall(r'(?:see|refer to|in)\s+(Table\s+\d+|Section\s+[\d\.]+|Figure\s+\d+)', full_content, re.I)
        if refs:
            ldu.source_metadata["cross_refs"] = list(set(refs))
            
        chunks.append(ldu)

    def chunk_document(self, doc: ExtractedDocument) -> List[LDU]:
        chunks = []
        current_headers = []
        
        # 1. Process Text Blocks with Header Detection and Merging
        i = 0
        merged_buffer = []
        buffer_page_refs = []
        
        while i < len(doc.text_blocks):
            block = doc.text_blocks[i]
            content = block.text.strip()
            
            if not content:
                i += 1
                continue

            # Header Detection
            is_list_item = re.match(r'^(\d+\.|[A-Za-z]\.|•|\-)\s+', content)
            is_potential_header = len(content) < 100 and not content.endswith(('.', '?', '!')) and not is_list_item
            
            # If we hit a new header, flush the buffer
            if is_potential_header and merged_buffer:
                self._flush_buffer(chunks, merged_buffer, buffer_page_refs, current_headers, doc.doc_id)
                merged_buffer = []
                buffer_page_refs = []

            if is_potential_header:
                current_headers = [content]

            # List Grouping
            if is_list_item:
                # Flush buffer before list
                if merged_buffer:
                    self._flush_buffer(chunks, merged_buffer, buffer_page_refs, current_headers, doc.doc_id)
                    merged_buffer = []
                    buffer_page_refs = []
                
                list_items = [content]
                page_refs = [block.page_number]
                bbox = block.bbox
                
                # Look ahead for more list items
                while i + 1 < len(doc.text_blocks):
                    next_block = doc.text_blocks[i + 1]
                    next_content = next_block.text.strip()
                    if re.match(r'^(\d+\.|[A-Za-z]\.|•|\-)\s+', next_content):
                        list_items.append(next_content)
                        if next_block.page_number not in page_refs:
                            page_refs.append(next_block.page_number)
                        i += 1
                    else:
                        break
                
                full_content = "\n".join(list_items)
                chunk_id = f"{doc.doc_id}_list_{len(chunks)}"
                chunks.append(LDU(
                    chunk_id=chunk_id,
                    doc_id=doc.doc_id,
                    content=full_content,
                    content_hash=hashlib.sha256(full_content.encode()).hexdigest(),
                    page_refs=page_refs,
                    chunk_type="list",
                    bbox=bbox,
                    parent_headers=list(current_headers)
                ))
            else:
                # Buffer regular text
                merged_buffer.append(content)
                if block.page_number not in buffer_page_refs:
                    buffer_page_refs.append(block.page_number)
                
                # If buffer exceeds ~1000 tokens (approx 4000 chars), flush
                if sum(len(c) for c in merged_buffer) > 4000:
                    self._flush_buffer(chunks, merged_buffer, buffer_page_refs, current_headers, doc.doc_id)
                    merged_buffer = []
                    buffer_page_refs = []
            i += 1
        
        # Final flush
        if merged_buffer:
            self._flush_buffer(chunks, merged_buffer, buffer_page_refs, current_headers, doc.doc_id)
            
        # 2. Process Tables (Already Preserved as Units)
        for table in doc.tables:
            table_content = " | ".join(table.headers) + "\n"
            table_content += "-" * 20 + "\n"
            for row in table.rows:
                table_content += " | ".join([str(c) for c in row]) + "\n"
            
            chunk_id = f"{doc.doc_id}_table_{len(chunks)}"
            chunks.append(LDU(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                content=table_content,
                content_hash=hashlib.sha256(table_content.encode()).hexdigest(),
                page_refs=[table.page_number],
                chunk_type="table",
                bbox=table.bbox,
                parent_headers=list(current_headers)
            ))

        # 3. Process Figures and Captions
        for figure in doc.figures:
            content = f"[FIGURE] {figure.caption or 'No caption available'}"
            chunk_id = f"{doc.doc_id}_figure_{len(chunks)}"
            chunks.append(LDU(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                content=content,
                content_hash=hashlib.sha256(content.encode()).hexdigest(),
                page_refs=[figure.page_number],
                chunk_type="figure",
                bbox=figure.bbox,
                parent_headers=list(current_headers),
                source_metadata={"caption": figure.caption}
            ))
            
        # Validate and return
        valid_chunks = [c for c in chunks if self.validator.validate_ldu(c)]
        print(f"✅ Chunking complete: {len(valid_chunks)} valid LDUs generated.")
        return valid_chunks
