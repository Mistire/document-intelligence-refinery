from abc import ABC, abstractmethod
from pathlib import Path

class BaseExtractionStrategy(ABC):
    @abstractmethod
    def extract(self, pdf_path: Path, output_dir: Path) -> Path:
        """Extracts content from PDF and returns path to the Markdown file."""
        pass
