import os
from pathlib import Path
from typing import List, Dict, Any
from src.models.chunk import LDU
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

class VectorStoreManager:
    _embeddings_cache = None

    def __init__(self, persist_directory: str = ".refinery/chroma"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.vector_store_instance = None

    @property
    def embeddings(self):
        if VectorStoreManager._embeddings_cache is None:
            print("🚀 Loading embedding model (first-time only)...")
            from langchain_huggingface import HuggingFaceEmbeddings
            VectorStoreManager._embeddings_cache = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
        return VectorStoreManager._embeddings_cache

    @property
    def vector_store(self):
        if self.vector_store_instance is None:
            self.vector_store_instance = Chroma(
                collection_name="refinery_chunks",
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_directory)
            )
        return self.vector_store_instance

    def ingest_chunks(self, chunks: List[LDU]):
        print(f"📥 Ingesting {len(chunks)} chunks into ChromaDB...")
        
        texts = [c.content for c in chunks]
        metadatas = []
        for c in chunks:
            # Metadata for filter/provenance
            meta = {
                "doc_id": c.doc_id,
                "chunk_id": c.chunk_id,
                "chunk_type": c.chunk_type,
                "page_refs": ",".join(map(str, c.page_refs)),
                "content_hash": c.content_hash,
                "parent_headers": ",".join(c.parent_headers) if c.parent_headers else "None"
            }
            # Add bbox as string if exists
            if c.bbox:
                meta["bbox"] = f"{c.bbox.x},{c.bbox.y},{c.bbox.w},{c.bbox.h}"
            metadatas.append(meta)
            
        ids = [c.chunk_id for c in chunks]
        
        self.vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        print(f"   -> Successfully ingested.")

    def search_chunks(self, query: str, k: int = 5, filter: Dict = None) -> List[Dict]:
        """Search for relevant chunks with optional filtering."""
        results = self.vector_store.similarity_search(query, k=k, filter=filter)
        return [
            {
                "content": r.page_content,
                "metadata": r.metadata
            }
            for r in results
        ]
