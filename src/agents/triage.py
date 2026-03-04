import pdfplumber
import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict
from src.models.document_profile import DocumentProfile, OriginType, LayoutComplexity, ExtractionCost

class TriageAgent:
    def __init__(self, config_path: str = "config.yaml", profiles_dir: str = ".refinery/profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Load Config (Requested)
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.t_config = self.config["triage"]
        self.domain_keywords = self.config["domain_keywords"]

    def triage(self, pdf_path: str) -> DocumentProfile:
        path = Path(pdf_path)
        doc_id = path.stem
        
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            
            total_chars = 0
            total_images_ratio = 0
            total_tables = 0
            scanned_pages_count = 0
            
            full_text = ""

            for page in pdf.pages:
                width, height = page.width, page.height
                area = width * height
                
                text = page.extract_text() or ""
                full_text += text + "\n"
                chars = len(text)
                total_chars += chars
                
                if chars < self.t_config["min_char_count_per_page"]:
                    scanned_pages_count += 1
                
                # Image area
                img_area = sum(abs(img["x1"] - img["x0"]) * abs(img["top"] - img["bottom"]) 
                               for img in page.images)
                total_images_ratio += (img_area / area) if area > 0 else 0
                total_tables += len(page.find_tables())

            avg_chars = total_chars / total_pages
            avg_img_ratio = total_images_ratio / total_pages
            
            # Confidence Calculation (Simplified for now)
            confidences = {"origin_type": 1.0, "layout_complexity": 0.9, "domain_hint": 0.8}
            
            # 1. Origin Type
            if scanned_pages_count == total_pages:
                origin = OriginType.SCANNED_IMAGE
            elif scanned_pages_count > 0:
                origin = OriginType.MIXED
                confidences["origin_type"] = 0.85
            else:
                origin = OriginType.NATIVE_DIGITAL
            
            # 2. Layout Complexity
            if total_tables >= self.t_config["min_table_detection"]:
                layout = LayoutComplexity.TABLE_HEAVY
            elif avg_img_ratio > self.t_config["max_image_area_ratio"]:
                layout = LayoutComplexity.FIGURE_HEAVY
            else:
                layout = LayoutComplexity.SINGLE_COLUMN
            
            # 3. Domain Hint (Keyword Based)
            domain = "general"
            for d, keywords in self.domain_keywords.items():
                if any(k in full_text.lower() for k in keywords):
                    domain = d
                    break

            # 4. Extraction Cost
            if origin == OriginType.SCANNED_IMAGE or avg_chars < self.t_config["min_char_count_per_page"]:
                cost = ExtractionCost.NEEDS_VISION_MODEL
            elif origin == OriginType.MIXED or layout != LayoutComplexity.SINGLE_COLUMN:
                cost = ExtractionCost.NEEDS_LAYOUT_MODEL
            else:
                cost = ExtractionCost.FAST_TEXT_SUFFICIENT

            profile = DocumentProfile(
                doc_id=doc_id,
                filename=path.name,
                total_pages=total_pages,
                origin_type=origin,
                layout_complexity=layout,
                domain_hint=domain,
                extraction_cost=cost,
                confidence_scores=confidences,
                avg_char_density=avg_chars / (pdf.pages[0].width * pdf.pages[0].height),
                avg_image_ratio=avg_img_ratio,
                total_tables_found=total_tables,
                triage_timestamp=datetime.now().isoformat()
            )
            
            self._save_profile(profile)
            return profile

    def _save_profile(self, profile: DocumentProfile):
        output_path = self.profiles_dir / f"{profile.doc_id}.json"
        with open(output_path, "w") as f:
            f.write(profile.model_dump_json(indent=2))
        print(f"Profile saved: {output_path}")
