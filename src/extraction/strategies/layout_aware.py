from docling.document_converter import DocumentConverter
from pathlib import Path
from .base import BaseExtractionStrategy

class LayoutAwareStrategy(BaseExtractionStrategy):
    def __init__(self):
        self.converter = DocumentConverter()

    def extract(self, pdf_path: Path, output_dir: Path) -> Path:
        md_file = output_dir / f"{pdf_path.stem}_layout.md"
        
        # Convert using Docling
        result = self.converter.convert(str(pdf_path))
        markdown_content = result.document.export_to_markdown()
        
        with open(md_file, "w") as f:
            f.write(markdown_content)
            
        return md_file
