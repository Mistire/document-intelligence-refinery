import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from src.agents.triage import TriageAgent
from src.extraction.router import ExtractionRouter
from src.agents.chunker import SemanticChunker
from src.agents.indexer import PageIndexBuilder
from src.extraction.fact_table import FactTableExtractor
from src.utils.vector_store import VectorStoreManager
from src.agents.query_agent import QueryInterfaceAgent

def validate_doc(pdf_path: str, query: str = "What is the main subject of this document?"):
    path = Path(pdf_path)
    doc_id = path.stem
    print(f"\n[START] Starting Full Refinery Pipeline for: {doc_id}")
    
    # Stage 1: Triage
    triage = TriageAgent()
    profile = triage.triage(pdf_path)
    print(f"[OK] Stage 1: Triage Complete ({profile.origin_type}, {profile.extraction_cost})")
    
    # Stage 2: Extraction
    router = ExtractionRouter()
    doc = router.route_and_extract(profile)
    print(f"[OK] Stage 2: Extraction Complete (Strategy: {doc.metadata.get('final_strategy')})")
    
    # Stage 3: Chunking
    chunker = SemanticChunker()
    chunks = chunker.chunk_document(doc)
    print(f"[OK] Stage 3: Chunking Complete ({len(chunks)} chunks generated)")
    
    # Stage 4: Indexing
    indexer = PageIndexBuilder()
    index = indexer.build_index(doc_id, chunks)
    print(f"[OK] Stage 4: Indexing Complete ({len(index.root_nodes)} root nodes)")
    
    # Data Layer: FactTable & Vector Store
    fact_table = FactTableExtractor()
    fact_table.extract_and_store(doc)
    
    vector_store = VectorStoreManager()
    vector_store.ingest_chunks(chunks)
    print("[OK] Data Layer: FactTable and Vector Store updated.")
    
    # Stage 5: Query
    agent = QueryInterfaceAgent(doc_id)
    print(f"[QUERY] Querying: {query}")
    answer = agent.run_query(query)
    print(f"\n[AI] ANSWER:\n{answer}")

if __name__ == "__main__":
    # Test with a small file if available
    data_dir = Path("data")
    pdfs = list(data_dir.glob("*.pdf"))
    if pdfs:
        validate_doc(str(pdfs[0]))
    else:
        print("[ERROR] No PDF found in 'data/' directory to validate.")
