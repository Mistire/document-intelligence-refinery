from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple
from src.models.extracted_document import ExtractedDocument

class BaseExtractionStrategy(ABC):
    @abstractmethod
    def extract(self, pdf_path: Path) -> Tuple[ExtractedDocument, float]:
        """
        Extracts content from PDF.
        Returns: Tuple of (Normalized ExtractedDocument, confidence_score)
        """
        pass
