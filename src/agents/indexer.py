import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Optional
from src.models.index import PageIndex, IndexNode
from src.models.chunk import LDU

load_dotenv()

class PageIndexBuilder:
    def __init__(self):
        # OpenRouter is OpenAI-compatible
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_URL"),
            model=os.getenv("MODEL_NAME"),
            default_headers={
                "HTTP-Referer": "https://localhost:3000",
                "X-Title": "Document Intelligence Refinery"
            }
        )
        
        self.summary_prompt = ChatPromptTemplate.from_template(
            "Summarize the following document slice into a single high-level sentence. "
            "Focus on the main topics and structural purpose.\n\n"
            "CONTENT:\n{content}"
        )

    def build_index(self, doc_id: str, chunks: List[LDU]) -> PageIndex:
        print(f"🗺️ Building PageIndex for {doc_id} with recursive linking...")
        
        # 1. Group chunks by page for simple hierarchical discovery
        # (In a more complex version, we'd use header hierarchy if available)
        page_groups: Dict[int, List[LDU]] = {}
        for chunk in chunks:
            p = chunk.page_refs[0] if chunk.page_refs else 1
            if p not in page_groups:
                page_groups[p] = []
            page_groups[p].append(chunk)
            
        # 2. Build root nodes (one per page for this prototype)
        root_nodes = []
        sorted_pages = sorted(page_groups.keys())
        
        for i, page_num in enumerate(sorted_pages):
            group_chunks = page_groups[page_num]
            
            # Use small slice to save tokens
            combined_text = "\n".join([c.content[:400] for c in group_chunks[:2]])
            summary = self._generate_summary(combined_text)
            
            node = IndexNode(
                id=f"{doc_id}_page_{page_num}",
                title=f"Page {page_num}",
                level=0,
                summary=summary,
                page_start=page_num,
                page_end=page_num,
                chunk_ids=[c.chunk_id for c in group_chunks]
            )
            root_nodes.append(node)
            
        return PageIndex(doc_id=doc_id, root_nodes=root_nodes)

    def _generate_summary(self, text: str) -> str:
        if not text.strip():
            return "Empty or non-textual page content."
            
        try:
            chain = self.summary_prompt | self.llm
            response = chain.invoke({"content": text})
            return response.content.strip()
        except Exception as e:
            print(f"⚠️ Summary failed: {str(e)}")
            return "Summary unavailable."
