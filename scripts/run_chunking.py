import sys
import json
from pathlib import Path
import jsonlines
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.chunker import SemanticChunker

def main():
    chunker = SemanticChunker()
    ledger_path = Path(".refinery/extraction_ledger.jsonl")
    output_dir = Path(".refinery/chunks")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not ledger_path.exists():
        print("❌ Ledger not found. Run Phase 2 first!")
        return

    with jsonlines.open(ledger_path) as reader:
        for entry in reader:
            doc_id = entry["doc_id"]
            md_path = Path(entry["output_path"])
            
            if not md_path.exists():
                print(f"⚠️ Markdown not found for {doc_id}")
                continue
                
            print(f"🧩 Chunking {doc_id}...")
            with open(md_path, "r") as f:
                content = f.read()
            
            chunks = chunker.chunk_document(doc_id, content)
            
            # Save chunks to .refinery/chunks/doc_id.json
            out_file = output_dir / f"{doc_id}.json"
            with open(out_file, "w") as f:
                json.dump([c.model_dump() for c in chunks], f, indent=2)
            
            print(f"   -> Generated {len(chunks)} chunks.")

if __name__ == "__main__":
    main()
