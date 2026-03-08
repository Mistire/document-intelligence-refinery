import sys
import json
import jsonlines
from pathlib import Path
from rich.console import Console
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from src.extraction.router import ExtractionRouter
from src.extraction.ledger import ExtractionLedger
from src.models.document_profile import DocumentProfile
from src.extraction.fact_table import FactTableExtractor

console = Console()

def main():
    router = ExtractionRouter()
    ledger = ExtractionLedger()
    fact_extractor = FactTableExtractor()
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Specific doc_id to extract")
    args = parser.parse_args()

    profiles_dir = Path(".refinery/profiles")
    if args.file:
        profiles = [profiles_dir / f"{args.file}.json"]
    else:
        profiles = list(profiles_dir.glob("*.json"))
    
    completed_ids = set()
    total = len(profiles)
    
    for i, profile_path in enumerate(profiles):
        with open(profile_path, "r") as f:
            profile_data = json.load(f)
            profile = DocumentProfile(**profile_data)
        
        print(f"[WORKING] {profile.doc_id}")
        print(f"[PROGRESS] {(i/total)*100}")
        sys.stdout.flush()

        if profile.doc_id in completed_ids:
            continue
            
        try:
            doc = router.route_and_extract(profile)
            fact_extractor.extract_and_store(doc)
            ledger.record_success(
                profile.doc_id, 
                doc.metadata.get("final_strategy", "unknown"), 
                Path(".refinery/extractions") / profile.doc_id / "extracted.json"
            )
        except Exception as e:
            # Errors can be printed, orchestrator will capture
            print(f"[ERROR] {profile.doc_id}: {str(e)}")

    print("[PROGRESS] 100")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
