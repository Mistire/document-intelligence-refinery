import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict
from src.models.index import PageIndex, IndexNode
from src.models.chunk import LDU

load_dotenv()

class PageIndexBuilder:
    def __init__(self):
        # OpenRouter is OpenAI-compatible!
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_URL"),
            model=os.getenv("MODEL_NAME"),
            default_headers={
                "HTTP-Referer": "https://localhost:3000", # Required by OpenRouter
                "X-Title": "Document Intelligence Refinery"
            }
        )
        
        self.summary_prompt = ChatPromptTemplate.from_template(
            "Summarize the following document slice into a single high-level sentence. "
            "Focus on the main topics and structural purpose (e.g., 'Overview of financial risks').\n\n"
            "CONTENT:\n{content}"
        )

    def build_index(self, doc_id: str, chunks: List[LDU]) -> PageIndex:
        print(f"🗺️ Building PageIndex for {doc_id}...")
        
        # Group chunks by header hierarchy
        header_groups: Dict[str, List[LDU]] = {}
        for chunk in chunks:
            # Create a unique key for the header hierarchy
            key = " > ".join(chunk.parent_headers) or "ROOT"
            if key not in header_groups:
                header_groups[key] = []
            header_groups[key].append(chunk)

        nodes = []
        for i, (header_key, group_chunks) in enumerate(header_groups.items()):
            print(f"   ✍️ Summarizing section: {header_key[:50]}...")
            
            # Use small slice of text to save tokens
            combined_text = "\n".join([c.content[:500] for c in group_chunks[:3]])
            summary = self._generate_summary(combined_text)
            
            nodes.append(IndexNode(
                id=f"{doc_id}_node_{i}",
                title=header_key.split(" > ")[-1],
                level=len(header_key.split(" > ")) - 1,
                summary=summary,
                page_start=1, # simplified
                page_end=1,   # simplified
                chunk_ids=[c.chunk_id for c in group_chunks]
            ))
            
        return PageIndex(doc_id=doc_id, root_nodes=nodes)

    def _generate_summary(self, text: str) -> str:
        chain = self.summary_prompt | self.llm
        response = chain.invoke({"content": text})
        return response.content.strip()
