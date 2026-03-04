import re
from pathlib import Path
from typing import List
from src.models.chunk import LDU

class SemanticChunker:
    def __init__(self, max_chars: int = 1500):
        self.max_chars = max_chars

    def chunk_document(self, doc_id: str, markdown_content: str) -> List[LDU]:
        # Rule 1: Break into sections by Headers (#, ##)
        sections = re.split(r'(^#+\s.*)', markdown_content, flags=re.MULTILINE)
        
        chunks = []
        current_headers = []
        
        for section in sections:
            if not section.strip():
                continue
            
            # Update header hierarchy
            if section.startswith('#'):
                header_text = section.strip()
                level = header_text.count('#')
                # Reset headers below this level
                current_headers = current_headers[:level-1] + [header_text]
                continue
            
            # Protect Tables: Split sections further, but don't break tables
            # A simple table regex: lines starting with | and containing |
            sub_parts = self._split_preserving_tables(section)
            
            for part in sub_parts:
                if not part.strip():
                    continue
                
                # Determine type
                ctype = "text"
                if part.strip().startswith('|'):
                    ctype = "table"
                elif part.strip().startswith('- ') or part.strip().startswith('* '):
                    ctype = "list"
                
                chunks.append(LDU(
                    chunk_id=f"{doc_id}_{len(chunks)}",
                    doc_id=doc_id,
                    content=part.strip(),
                    parent_headers=current_headers.copy(),
                    chunk_type=ctype
                ))
        
        return chunks

    def _split_preserving_tables(self, text: str) -> List[str]:
        # This is a simplified regex-based split that looks for table blocks
        # and treats them as atomic units.
        table_pattern = r'(\n\|.*\|\n(?:\|.*\|\n)*)'
        parts = re.split(table_pattern, text)
        return parts
