import sys
import json
from pathlib import Path
from rich.console import Console
from pydantic import ValidationError

sys.path.append(str(Path(__file__).parent.parent))

from src.agents.indexer import PageIndexBuilder
from src.models.chunk import LDU

console = Console()

def main():
    indexer = PageIndexBuilder()
    chunks_dir = Path(".refinery/chunks")
    output_dir = Path(".refinery/indexes")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Specific doc_id to index")
    args = parser.parse_args()

    if args.file:
        chunk_files = [chunks_dir / f"{args.file}.json"]
    else:
        chunk_files = list(chunks_dir.glob("*.json"))
    total = len(chunk_files)
    
    for i, chunk_file in enumerate(chunk_files):
        doc_id = chunk_file.stem
        print(f"[WORKING] {doc_id}")
        print(f"[PROGRESS] {(i/total)*100}")
        sys.stdout.flush()
        
        try:
            with open(chunk_file, "r") as f:
                chunk_data = json.load(f)
                chunks = [LDU(**c) for c in chunk_data]
                
            index = indexer.build_index(doc_id, chunks)
            
            # Save index to .refinery/indexes/doc_id.json
            out_file = output_dir / f"{doc_id}.json"
            with open(out_file, "w") as f:
                f.write(index.model_dump_json(indent=2))
        except ValidationError as ve:
            print(f"[ERROR] Validation failed for {doc_id}: {ve}")
            # Continue to next file instead of crashing
            continue
        except Exception as e:
            print(f"[ERROR] Failed to process {doc_id}: {str(e)}")
            continue
            
    print("[PROGRESS] 100")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
