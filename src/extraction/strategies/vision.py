import base64
import fitz # PyMuPDF
import io
import json
import os
import yaml
from pathlib import Path
from typing import Tuple, Dict, Any, List
from .base import BaseExtractionStrategy
from src.models.extracted_document import ExtractedDocument, TextBlock, TableStructure
from src.models.provenance import BBox
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

class VisionExtractor(BaseExtractionStrategy):
    def __init__(self, config_path: str = "config.yaml"):
        if not Path(config_path).exists():
            self.v_config = {"max_vision_pages": 5} # Fallback
        else:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                self.v_config = config.get("extraction", {"max_vision_pages": 5})
        
        # Initialize LLM via OpenRouter
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "openrouter/auto:free"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
            max_tokens=4096
        )

    def extract(self, pdf_path: Path, max_pages: int = None, **kwargs) -> Tuple[ExtractedDocument, float]:
        doc_id = pdf_path.stem
        extracted_doc = ExtractedDocument(doc_id=doc_id)
        
        # Priority: argument > config > default(5)
        limit = max_pages or self.v_config.get("max_pages_per_doc", 5)
        
        doc = fitz.open(str(pdf_path))
        num_pages = min(len(doc), limit)
        
        print(f"👁️ Vision Extraction for {doc_id} (Processing {num_pages} pages)...")
        
        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # High res
            img_data = pix.tobytes("png")
            
            # Encode to base64
            base64_image = base64.b64encode(img_data).decode('utf-8')
            
            # Formulate the prompt
            prompt = (
                "Extract ALL text and tables from this document page image. "
                "Return a JSON object with two keys: 'text_blocks' and 'tables'. "
                "Each text block MUST have 'text' and 'bbox' (x, y, w, h normalized 0-1000). "
                "Each table MUST have 'headers', 'rows', and 'bbox'. "
                "If no tables exist, return an empty list [] for 'tables'. "
                "Ensure that 'text_blocks' is NOT empty if there is text visible on the page. "
                "DO NOT include any explanation or markdown tags, JUST the raw JSON."
            )
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                    },
                ]
            )
            
            try:
                response = self.llm.invoke([message])
                # Clean response (sometimes VLMs add ```json ... ```)
                raw_json = response.content.strip()
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("\n", 1)[1].rsplit("\n", 1)[0]
                
                try:
                    page_data = json.loads(raw_json)
                except json.JSONDecodeError:
                    print(f"⚠️ Failed to parse JSON from VLM: {raw_json[:100]}...")
                    continue
                
                # Normalize BBoxes and add to document (Simplified normalization for now)
                for tb in page_data.get("text_blocks", []):
                    # In a real system, we'd map VLM coordinates to PDF points. 
                    # For now, we trust the VLM or use dummy BBoxes if missing.
                    b = tb.get("bbox", {"x": 0, "y": 0, "w": 0, "h": 0})
                    extracted_doc.text_blocks.append(TextBlock(
                        text=tb["text"],
                        bbox=BBox(**b),
                        page_number=page_num + 1
                    ))
                
                for table in page_data.get("tables", []):
                    b = table.get("bbox", {"x": 0, "y": 0, "w": 0, "h": 0})
                    extracted_doc.tables.append(TableStructure(
                        headers=table.get("headers", []),
                        rows=table.get("rows", []),
                        bbox=BBox(**b),
                        page_number=page_num + 1
                    ))
                    
            except Exception as e:
                print(f"⚠️ Vision page {page_num+1} failed: {str(e)}")
        
        doc.close()
        
        extracted_doc.metadata["vision_strategy_used"] = True
        
        # Heuristic Confidence: If we found nothing on a document Triage said was interesting, confidence is 0
        confidence = 0.90 if (len(extracted_doc.text_blocks) > 0 or len(extracted_doc.tables) > 0) else 0.0
        
        return extracted_doc, confidence
