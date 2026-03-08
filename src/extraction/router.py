import yaml
import json
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
        cumulative_cost = 0.0
        budget_limit = self.e_config.get("document_budget_usd", 1.0)
        
        # We allow up to 2 escalations
        for _ in range(3):
            # Budget Check
            if cumulative_cost > budget_limit:
                print(f"Budget limit exceeded for {profile.doc_id} (${cumulative_cost:.4f} > ${budget_limit:.4f}). Stopping.")
                break

            strategy = self.strategies[current_strategy_label]
            console_msg = f"Running Strategy {current_strategy_label} for {profile.doc_id}..."
            # Try to use rich console if available, else print
            try:
                from rich.console import Console
                Console().print(f"[yellow]{console_msg}[/yellow]")
            except:
                print(console_msg)
            
            max_pages = self.e_config.get("max_pages_per_doc")
            doc, confidence = strategy.extract(
                pdf_path, 
                max_pages=max_pages,
                is_scanned=(profile.origin_type == "scanned")
            )
            
            # Estimate Cost (Simple heuristic)
            if current_strategy_label == "C":
                # Assume Vision is roughly $0.05 per page
                cumulative_cost += (doc.metadata.get("page_count", 0) * 0.05)
            elif current_strategy_label == "B":
                cumulative_cost += 0.01 
            
            # Threshold Check
            threshold = self.e_config.get(f"confidence_threshold_{current_strategy_label.lower()}", 0.8)
            
            if confidence >= threshold:
                print(f"Strategy {current_strategy_label} succeeded with confidence {confidence:.2f}")
                final_doc = doc
                final_doc.metadata["final_strategy"] = current_strategy_label
                final_doc.metadata["total_cost_usd"] = cumulative_cost
                break
            else:
                print(f"Strategy {current_strategy_label} low confidence ({confidence:.2f} < {threshold}). Escalating...")
                if current_strategy_label == "A":
                    current_strategy_label = "B"
                elif current_strategy_label == "B":
                    current_strategy_label = "C"
                else:
                    # Already at C, nothing left to escalate to
                    final_doc = doc
                    final_doc.metadata["final_strategy"] = "C (Final Fallback)"
                    final_doc.metadata["total_cost_usd"] = cumulative_cost
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
        
        # --- UPDATE CENTRAL LEDGER (Step 2 Compliance) ---
        ledger_path = Path("extraction_ledger.jsonl")
        ledger_entry = {
            "doc_id": doc.doc_id,
            "final_strategy": doc.metadata.get("final_strategy"),
            "total_cost_usd": doc.metadata.get("total_cost_usd", 0.0),
            "timestamp": doc.metadata.get("extraction_timestamp"),
            "tables_found": len(doc.tables),
            "text_blocks": len(doc.text_blocks)
        }
        with open(ledger_path, "a") as f:
            f.write(json.dumps(ledger_entry) + "\n")
            
        print(f"Extraction saved: {output_path}")
        print(f"Ledger updated: {ledger_path}")
