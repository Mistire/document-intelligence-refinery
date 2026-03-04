import pdfplumber
import os
import json
from datetime import datetime
from pathlib import Path
from src.models.document_profile import DocumentProfile, OriginType, LayoutComplexity, ExtractionCost

class TriageAgent:
    def __init__(self, profiles_dir: str = ".refinery/profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Thresholds from our DOMAIN_NOTES.md
        self.SCAN_THRESHOLD = 100        # chars per page
        self.TABLE_HEAVY_THRESHOLD = 2   # tables per page
        self.IMAGE_DOMINANT_THRESHOLD = 0.5 # 50% area

    def triage(self, pdf_path: str) -> DocumentProfile:
        path = Path(pdf_path)
        doc_id = path.stem
        
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            
            total_chars = 0
            total_images_ratio = 0
            total_tables = 0
            scanned_pages_count = 0
            
            # --- FAST FULL-DOC SCAN ---
            # We check EVERY page because pdfplumber.pages is just a list of objects.
            # .extract_text() and .find_tables() are fast enough for a full pass.
            for page in pdf.pages:
                width, height = page.width, page.height
                area = width * height
                
                text = page.extract_text() or ""
                chars = len(text)
                total_chars += chars
                
                if chars < self.SCAN_THRESHOLD:
                    scanned_pages_count += 1
                
                # Image area
                img_area = sum(abs(img["x1"] - img["x0"]) * abs(img["top"] - img["bottom"]) 
                               for img in page.images)
                total_images_ratio += (img_area / area) if area > 0 else 0
                
                # Tables (very fast check)
                total_tables += len(page.find_tables())

            # Averages and Ratios
            avg_chars = total_chars / total_pages
            avg_img_ratio = total_images_ratio / total_pages
            
            # 1. Origin Type
            if scanned_pages_count == total_pages:
                origin = OriginType.SCANNED_IMAGE
            elif scanned_pages_count > 0:
                # If even 1 page is scanned, it's mixed
                origin = OriginType.MIXED
            else:
                origin = OriginType.NATIVE_DIGITAL
            
            # 2. Layout Complexity
            # If we find even 1 table in samples, it's likely table-heavy in production
            if total_tables > 0:
                layout = LayoutComplexity.TABLE_HEAVY
            elif avg_img_ratio > 0.2: # Lower threshold for figure_heavy
                layout = LayoutComplexity.FIGURE_HEAVY
            else:
                layout = LayoutComplexity.SINGLE_COLUMN
            
            # 3. Extraction Cost (The Strategy Route)
            # More aggressive escalation logic
            if origin == OriginType.SCANNED_IMAGE or avg_chars < 150:
                cost = ExtractionCost.NEEDS_VISION_MODEL # Strategy C
            elif origin == OriginType.MIXED or layout != LayoutComplexity.SINGLE_COLUMN or avg_img_ratio > 0.1:
                cost = ExtractionCost.NEEDS_LAYOUT_MODEL # Strategy B
            else:
                cost = ExtractionCost.FAST_TEXT_SUFFICIENT # Strategy A

            profile = DocumentProfile(
                doc_id=doc_id,
                filename=path.name,
                total_pages=total_pages,
                origin_type=origin,
                layout_complexity=layout,
                extraction_cost=cost,
                avg_char_density=avg_chars / (pdf.pages[0].width * pdf.pages[0].height),
                avg_image_ratio=avg_img_ratio,
                total_tables_found=total_tables,
                triage_timestamp=datetime.now().isoformat()
            )
            
            # Save to .refinery/profiles/
            self._save_profile(profile)
            return profile

    def _save_profile(self, profile: DocumentProfile):
        output_path = self.profiles_dir / f"{profile.doc_id}.json"
        with open(output_path, "w") as f:
            f.write(profile.model_dump_json(indent=2))
        print(f"Profile saved: {output_path}")
