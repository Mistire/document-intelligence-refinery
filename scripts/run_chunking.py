import sys
import json
from pathlib import Path
import jsonlines
from rich.console import Console
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from src.agents.chunker import SemanticChunker
from src.models.extracted_document import ExtractedDocument
from src.utils.vector_store import VectorStoreManager

console = Console()

def main():
    chunker = SemanticChunker()
    vector_store = VectorStoreManager()
    ledger_path = Path(".refinery/extraction_ledger.jsonl")
    output_dir = Path(".refinery/chunks")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not ledger_path.exists():
        return

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Specific doc_id to chunk")
    args = parser.parse_args()

    if args.file:
        entries = [{"doc_id": args.file}]
    else:
        # Count entries for progress bar
        entries = []
        with jsonlines.open(ledger_path) as reader:
            for entry in reader:
                entries.append(entry)

    total = len(entries)
    for i, entry in enumerate(entries):
        doc_id = entry["doc_id"]
        print(f"[WORKING] {doc_id}")
        print(f"[PROGRESS] {(i/total)*100}")
        sys.stdout.flush()

        # Location for refined extracted JSON
        extraction_path = Path(".refinery/extractions") / doc_id / "extracted.json"
        
        if not extraction_path.exists():
            continue
            
        with open(extraction_path, "r") as f:
            doc_data = json.load(f)
            doc = ExtractedDocument(**doc_data)
        
        chunks = chunker.chunk_document(doc)
        
        # Save chunks to .refinery/chunks/doc_id.json
        out_file = output_dir / f"{doc_id}.json"
        with open(out_file, "w") as f:
            json.dump([c.model_dump() for c in chunks], f, indent=2)
            
        # --- VECTOR INGESTION ---
        print(f"[WORKING] Ingesting {len(chunks)} chunks into ChromaDB for {doc_id}...")
        vector_store.ingest_chunks(chunks)

    print("[PROGRESS] 100")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
