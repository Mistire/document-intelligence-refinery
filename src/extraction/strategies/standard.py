import pdfplumber
from pathlib import Path
from .base import BaseExtractionStrategy

class StandardExtractionStrategy(BaseExtractionStrategy):
    def extract(self, pdf_path: Path, output_dir: Path) -> Path:
        md_file = output_dir / f"{pdf_path.stem}_standard.md"
        
        with pdfplumber.open(pdf_path) as pdf:
            content = []
            for i, page in enumerate(pdf.pages):
                content.append(f"## Page {i+1}\n")
                content.append(page.extract_text() or "")
                content.append("\n\n")
            
            with open(md_file, "w") as f:
                f.write("".join(content))
        
        return md_file
