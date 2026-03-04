import yaml
from pathlib import Path
from typing import Dict, Any
from src.models.document_profile import DocumentProfile, ExtractionCost
from src.models.extracted_document import ExtractedDocument
from .strategies.standard import StandardExtractionStrategy
from .strategies.layout_aware import LayoutAwareStrategy
from .strategies.vision import VisionExtractor

class ExtractionRouter:
    def __init__(self, config_path: str = "config.yaml"):
        # Load Config (Requested)
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.e_config = self.config["extraction"]
        
        self.strategies = {
            "A": StandardExtractionStrategy(),
            "B": LayoutAwareStrategy(),
            "C": VisionExtractor(config_path=config_path)
        }

    def route_and_extract(self, profile: DocumentProfile) -> ExtractedDocument:
        pdf_path = Path("data") / profile.filename
        
        # Initial Strategy Selection from Triage
        # Map cost enum to our A/B/C internal labels
        cost_map = {
            ExtractionCost.FAST_TEXT_SUFFICIENT: "A",
            ExtractionCost.NEEDS_LAYOUT_MODEL: "B",
            ExtractionCost.NEEDS_VISION_MODEL: "C"
        }
        
        start_strategy = cost_map.get(profile.extraction_cost, "A")
        
        # --- ESCALATION GUARD (A -> B -> C) ---
        current_strategy_label = start_strategy
        final_doc = None
        
        # We allow up to 2 escalations
        for _ in range(3):
            strategy = self.strategies[current_strategy_label]
            print(f"🔄 Running Strategy {current_strategy_label} for {profile.doc_id}...")
            
            doc, confidence = strategy.extract(pdf_path)
            
            # Threshold Check
            threshold = self.e_config.get(f"confidence_threshold_{current_strategy_label.lower()}", 0.8)
            
            if confidence >= threshold:
                print(f"✅ Strategy {current_strategy_label} succeeded with confidence {confidence:.2f}")
                final_doc = doc
                final_doc.metadata["final_strategy"] = current_strategy_label
                break
            else:
                print(f"⚠️ Strategy {current_strategy_label} low confidence ({confidence:.2f} < {threshold}). Escalating...")
                if current_strategy_label == "A":
                    current_strategy_label = "B"
                elif current_strategy_label == "B":
                    current_strategy_label = "C"
                else:
                    # Already at C, nothing left to escalate to
                    final_doc = doc
                    final_doc.metadata["final_strategy"] = "C (Final Fallback)"
                    break
        
        # Save structured JSON
        self._save_extraction(final_doc)
        return final_doc

    def _save_extraction(self, doc: ExtractedDocument):
        output_dir = Path(".refinery/extractions") / doc.doc_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "extracted.json"
        with open(output_path, "w") as f:
            f.write(doc.model_dump_json(indent=2))
        print(f"📦 Extraction saved: {output_path}")
