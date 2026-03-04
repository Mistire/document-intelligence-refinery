import os
import yaml
from pathlib import Path
from typing import Tuple, Dict, Any
from .base import BaseExtractionStrategy
from src.models.extracted_document import ExtractedDocument, TextBlock
from src.models.provenance import BBox
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

class VisionExtractor(BaseExtractionStrategy):
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.v_config = self.config["extraction"]
        
        # Initialize LLM via OpenRouter
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "openrouter/auto:free"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1")
        )

    def extract(self, pdf_path: Path) -> Tuple[ExtractedDocument, float]:
        doc_id = pdf_path.stem
        extracted_doc = ExtractedDocument(doc_id=doc_id)
        
        # In a real implementation, we would convert PDF pages to images
        # and send them to the VLM. 
        # For the prototype, we simulate or use a representative sample.
        
        # Budget tracking (Simplified)
        total_tokens = 0
        extracted_doc.metadata["vision_strategy_used"] = True
        extracted_doc.metadata["estimated_cost"] = 0.05 # Placeholder
        
        # Confidence is generally high for VLM if it returns structured data
        confidence = 0.90
        
        return extracted_doc, confidence
