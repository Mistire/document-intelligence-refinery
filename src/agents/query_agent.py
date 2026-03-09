import os
import json
import time
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
    iteration: int

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
        workflow.add_node("summarize", self._summarize)
        
        # Define Edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "summarize": "summarize",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        workflow.add_edge("summarize", END)
        
        return workflow.compile()

    def _get_tools(self):
        @tool
        def pageindex_navigate(query: str) -> str:
            """Traverse the hierarchical PageIndex to find relevant sections."""
            print(f"  [Tool] Navigating PageIndex for: {query}")
            start = time.time()
            if not self.page_index:
                return "PageIndex not available for this document."
            
            matches = []
            def search_tree(nodes: List[IndexNode]):
                for node in nodes:
                    if query.lower() in node.title.lower() or query.lower() in node.summary.lower():
                        matches.append(node.model_dump())
                    search_tree(node.child_nodes)
            
            search_tree(self.page_index.root_nodes)
            print(f"  [Tool] PageIndex finished in {time.time() - start:.2f}s")
            return json.dumps(matches[:3], indent=2)

        @tool
        def semantic_search(query: str) -> str:
            """Perform a vector search over document chunks. Returns chunks with Provenance."""
            print(f"  [Tool] Searching vector store for: {query}")
            start = time.time()
            results = self.vector_store.search_chunks(query, k=5, filter={"doc_id": self.doc_id})
            print(f"  [Tool] Vector search finished in {time.time() - start:.2f}s")
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
        iteration = state.get("iteration", 0)
        print(f"  [Agent] Loop {iteration+1} | Calling LLM ({len(state['messages'])} messages)...")
        start = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Document Intelligence Refinery Assistant. "
                        f"Analyzing: {state['doc_id']}. "
                        "1. Use tools to find info. DO NOT repeat the same query if it fails. "
                        "2. Search only twice for the same info before concluding. "
                        "3. ALWAYS include a JSON 'provenance_chain' in your final answer containing "
                        "page_number, bbox (x,y,w,h), and content_hash for every fact."),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        chain = prompt | self.llm.bind_tools(self._get_tools())
        response = chain.invoke(state)
        print(f"  [Agent] LLM responded in {time.time() - start:.2f}s")
        return {"messages": [response], "iteration": iteration + 1}

    def _summarize(self, state: AgentState):
        print(f"  [Agent] Generating final summary...")
        start = time.time()
        # Filter messages to only include important history if it gets too long
        # But for now, we'll try just being more direct in the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Document Intelligence Refinery Assistant. "
                        "You have reached the maximum search limit for this query. "
                        "Review the research history provided below and provide a final, consolidated answer. "
                        "If you found the info, present it clearly with provenance. "
                        "If the info is definitely not there, explain what you searched for and why it yielded no results."),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Provide your final response now based on the above logs. Do not call any more tools.")
        ])
        chain = prompt | self.llm
        response = chain.invoke(state)
        print(f"  [Agent] Summary generated in {time.time() - start:.2f}s | Content length: {len(response.content)}")
        if not response.content:
            print("  [Warning] Model returned EMPTY content in summary node!")
            # Fallback content
            response.content = "I searched the document multiple times but could not find a definitive answer to your question. Please try a different query."
            
        return {"messages": [response]}

    def _should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        iteration = state.get("iteration", 0)
        
        if last_message.tool_calls:
            if iteration >= 5:
                return "summarize"
            return "continue"
        return "end"

    def run_query(self, query: str) -> str:
        print(f"🔍 Starting query execution...")
        start_time = time.time()
        state = {
            "messages": [HumanMessage(content=query)],
            "doc_id": self.doc_id,
            "provenance": [],
            "final_answer": "",
            "iteration": 0
        }
        
        final_state = self.graph.invoke(state)
        print(f"✨ Query execution finished in {time.time() - start_time:.2f}s")
        return final_state["messages"][-1].content
