import json
import jsonlines
from pathlib import Path
from datetime import datetime

class ExtractionLedger:
    def __init__(self, ledger_path: str = ".refinery/extraction_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def record_success(self, doc_id: str, strategy: str, markdown_path: Path):
        entry = {
            "doc_id": doc_id,
            "strategy": strategy,
            "output_path": str(markdown_path),
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        with jsonlines.open(self.ledger_path, mode='a') as writer:
            writer.write(entry)
        print(f"📖 Ledger updated: {doc_id}")
