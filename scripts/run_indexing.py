import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.indexer import PageIndexBuilder
from src.models.chunk import LDU

def main():
    indexer = PageIndexBuilder()
    chunks_dir = Path(".refinery/chunks")
    output_dir = Path(".refinery/indexes")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for chunk_file in chunks_dir.glob("*.json"):
        doc_id = chunk_file.stem
        print(f"🏗️ Indexing {doc_id}...")
        
        with open(chunk_file, "r") as f:
            chunk_data = json.load(f)
            chunks = [LDU(**c) for c in chunk_data]
            
        index = indexer.build_index(doc_id, chunks)
        
        # Save index to .refinery/indexes/doc_id.json
        out_file = output_dir / f"{doc_id}.json"
        with open(out_file, "w") as f:
            f.write(index.model_dump_json(indent=2))
            
    print("\n✨ PageIndex Building Complete!")

if __name__ == "__main__":
    main()
