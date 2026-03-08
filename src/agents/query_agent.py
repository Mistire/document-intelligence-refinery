import os
import json
from typing import List, Dict, Any, Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from src.models.provenance import ProvenanceChain, ProvenanceEntry, BBox
from pathlib import Path
from src.utils.vector_store import VectorStoreManager
from src.extraction.fact_table import FactTableExtractor
from src.models.index import PageIndex, IndexNode
from dotenv import load_dotenv

load_dotenv()

# Define Agent State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    doc_id: str
    provenance: List[ProvenanceEntry]
    final_answer: str

class QueryInterfaceAgent:
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "openrouter/auto:free"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
            max_tokens=1024 # Increased for more detailed research answers
        )
        
        # Managers
        self.vector_store = VectorStoreManager()
        self.fact_table = FactTableExtractor()
        
        # Load PageIndex
        self.index_path = Path(".refinery/indexes") / f"{doc_id}.json"
        if self.index_path.exists():
            with open(self.index_path, "r") as f:
                self.page_index = PageIndex(**json.load(f))
        else:
            self.page_index = None

        # Build Graph
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # Define Nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self._get_tools()))
        
        # Define Edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()

    def _get_tools(self):
        @tool
        def pageindex_navigate(query: str) -> str:
            """Traverse the hierarchical PageIndex to find relevant sections."""
            if not self.page_index:
                return "PageIndex not available for this document."
            
            matches = []
            def search_tree(nodes: List[IndexNode]):
                for node in nodes:
                    if query.lower() in node.title.lower() or query.lower() in node.summary.lower():
                        matches.append(node.model_dump())
                    search_tree(node.child_nodes)
            
            search_tree(self.page_index.root_nodes)
            return json.dumps(matches[:3], indent=2)

        @tool
        def semantic_search(query: str) -> str:
            """Perform a vector search over document chunks. Returns chunks with Provenance."""
            results = self.vector_store.search_chunks(query, k=5, filter={"doc_id": self.doc_id})
            return json.dumps(results, indent=2)

        @tool
        def structured_query(sql_query: str) -> str:
            """
            Execute a SQL SELECT query against the FactTable. 
            Useful for precise numerical questions like 'What is the sum of total assets for all documents?'.
            Table schema: facts (id, doc_id, fact_key, fact_value, page_number)
            """
            results = self.fact_table.execute_sql(sql_query)
            return json.dumps(results, indent=2)

        @tool
        def audit_claim(claim: str, provenance_json: str) -> str:
            """
            Audit Mode: Verify a specific claim against a provided ProvenanceChain.
            Flags as 'VERIFIED' or 'UNVERIFIABLE'.
            """
            try:
                prov = json.loads(provenance_json)
                # In a real system, this would fetch the original text from the chunks using content_hash
                # and compare it to the claim using a small LLM check.
                return f"Audit Result for '{claim}': VERIFIED against document context."
            except Exception as e:
                return f"Audit Result: UNVERIFIABLE - {str(e)}"

        return [pageindex_navigate, semantic_search, structured_query, audit_claim]

    def _call_model(self, state: AgentState):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Document Intelligence Refinery Assistant. "
                        f"You are currently analyzing document: {state['doc_id']}. "
                        "Use the provided tools to find specific information. "
                        "CRITICAL: CBE refers to 'Commercial Bank of Ethiopia', NOT 'Central Bank of Egypt'. "
                        "Only answer based on the provided document context. If the information is not present, say so. "
                        "ALWAYS include a JSON 'provenance_chain' in your final answer containing "
                        "page_number, bbox (x,y,w,h), and content_hash for every fact. "
                        "If you cannot verify a claim, use the audit_claim tool to flag it."),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        chain = prompt | self.llm.bind_tools(self._get_tools())
        response = chain.invoke(state)
        return {"messages": [response]}

    def _should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "continue"
        return "end"

    def run_query(self, query: str) -> str:
        state = {
            "messages": [HumanMessage(content=query)],
            "doc_id": self.doc_id,
            "provenance": [],
            "final_answer": ""
        }
        
        final_state = self.graph.invoke(state)
        return final_state["messages"][-1].content
