import sys
import json
import jsonlines
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.extraction.router import ExtractionRouter
from src.extraction.ledger import ExtractionLedger
from src.models.document_profile import DocumentProfile

def main():
    router = ExtractionRouter()
    ledger = ExtractionLedger()
    profiles_dir = Path(".refinery/profiles")
    # Load existing ledger entries to avoid re-processing
    completed_ids = set()
    if ledger.ledger_path.exists():
        with jsonlines.open(ledger.ledger_path) as reader:
            for entry in reader:
                if entry.get("status") == "completed":
                    completed_ids.add(entry["doc_id"])

    for profile_path in profiles_dir.glob("*.json"):
        with open(profile_path, "r") as f:
            profile_data = json.load(f)
            profile = DocumentProfile(**profile_data)
        
        if profile.doc_id in completed_ids:
            print(f"✅ Skipping {profile.doc_id} (already in ledger)")
            continue
            
        print(f"🏗️ Processing {profile.doc_id} via {profile.extraction_cost}...")
        
        try:
            doc = router.route_and_extract(profile)
            ledger.record_success(
                profile.doc_id, 
                doc.metadata.get("final_strategy", "unknown"), 
                Path(".refinery/extractions") / profile.doc_id / "extracted.json"
            )
        except Exception as e:
            print(f"❌ Failed to extract {profile.doc_id}: {str(e)}")

if __name__ == "__main__":
    main()
