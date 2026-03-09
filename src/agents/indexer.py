import re
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
            max_tokens=4096,
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
        
        sections: Dict[str, IndexNode] = {}
        root_nodes = []
        
        # 1. Group chunks into hierarchical sections
        for chunk in chunks:
            # Determine the section path (default to "Overview" if no headers)
            path = chunk.parent_headers if chunk.parent_headers else ["Overview"]
            
            # For each level in the path, ensure a node exists
            parent_id = None
            for level, title in enumerate(path):
                # Unique ID for the section at this level
                node_id = f"{doc_id}_{'_'.join([re.sub(r'\W+', '', t) for t in path[:level+1]])}"
                
                if node_id not in sections:
                    node = IndexNode(
                        id=node_id,
                        title=title,
                        level=level,
                        summary="Generating...", 
                        page_start=chunk.page_refs[0],
                        page_end=chunk.page_refs[-1],
                        parent_id=parent_id,
                        chunk_ids=[],
                        key_entities=[],
                        data_types_present=[]
                    )
                    sections[node_id] = node
                    if parent_id:
                        # Append reference to the existing section object
                        sections[parent_id].child_nodes.append(node)
                    else:
                        root_nodes.append(node)
                
                # Update node metadata
                node = sections[node_id]
                node.page_start = min(node.page_start, chunk.page_refs[0])
                node.page_end = max(node.page_end, chunk.page_refs[-1])
                
                # Check if chunk belongs exactly to this leaf or we just pass through
                if level == len(path) - 1:
                    if chunk.chunk_id not in node.chunk_ids:
                        node.chunk_ids.append(chunk.chunk_id)
                
                if chunk.chunk_type not in node.data_types_present:
                    node.data_types_present.append(chunk.chunk_type)
                
                parent_id = node_id
            
        # 2. Post-process: Generate summaries and extract entities in parallel
        from concurrent.futures import ThreadPoolExecutor
        
        chunk_map = {c.chunk_id: c for c in chunks}
        nodes_to_process = list(sections.values())
        
        def process_node(node):
            # Combine text from direct chunks and potentially child chunks for context
            all_chunk_ids = list(node.chunk_ids)
            
            if all_chunk_ids:
                combined_text = ""
                for cid in all_chunk_ids[:3]: # Sample for summary
                    combined_text += chunk_map[cid].content[:500] + "\n"
                
                node.summary = self._generate_summary(combined_text)
                # Heuristic Entity Extraction (Capitalized words)
                entities = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', combined_text)
                node.key_entities = list(set(entities))[:8]
            else:
                node.summary = "Structural section containing sub-chapters."
            return node

        print(f"⚡ Parallelizing summary generation for {len(nodes_to_process)} nodes...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(process_node, nodes_to_process))
        
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
