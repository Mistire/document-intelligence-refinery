import sqlite3
import os
import json
from pathlib import Path
from typing import List, Dict, Any
from src.models.extracted_document import ExtractedDocument
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class FactTableExtractor:
    def __init__(self, db_path: str = ".refinery/fact_table.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "openrouter/auto:free"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
            max_tokens=4096
        )

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT,
                    fact_key TEXT,
                    fact_value TEXT,
                    page_number INTEGER,
                    context TEXT,
                    extraction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def extract_and_store(self, doc: ExtractedDocument):
        print(f"📊 Extracting structural facts for {doc.doc_id} into SQLite...")
        
        # Combine tables and some text for fact extraction
        context = ""
        for table in doc.tables[:3]: # Sample tables
            context += f"Table (Page {table.page_number}): " + " | ".join(table.headers) + "\n"
            for row in table.rows[:5]:
                context += " | ".join([str(c) for c in row]) + "\n"
        
        if not context:
            print("   -> No structural data found for FactTable.")
            return

        prompt = ChatPromptTemplate.from_template(
            "Extract key numerical or financial facts from the following document data. "
            "Return a JSON list of objects, each with 'key', 'value', and 'page_number'. "
            "Focus on high-value facts like 'Total Revenue', 'Fiscal Year', 'Date of Audit'.\n\n"
            "DATA:\n{context}"
        )
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({"context": context})
            
            # Clean and parse JSON
            raw_json = response.content.strip()
            if raw_json.startswith("```"):
                raw_json = raw_json.split("\n", 1)[1].rsplit("\n", 1)[0]
            
            facts = json.loads(raw_json)
            
            with sqlite3.connect(self.db_path) as conn:
                for fact in facts:
                    conn.execute("""
                        INSERT INTO facts (doc_id, fact_key, fact_value, page_number, context)
                        VALUES (?, ?, ?, ?, ?)
                    """, (doc.doc_id, fact['key'], fact['value'], fact['page_number'], context[:500]))
                conn.commit()
            
            print(f"   -> Stored {len(facts)} facts in FactTable.")
            
        except Exception as e:
            print(f"⚠️ Fact extraction failed: {str(e)}")

    def query_facts(self, query_str: str) -> List[Dict]:
        """Simple keyword-based SQL search for facts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM facts WHERE fact_key LIKE ? OR fact_value LIKE ?
            """, (f"%{query_str}%", f"%{query_str}%"))
            return [dict(row) for row in cursor.fetchall()]

    def execute_sql(self, sql_query: str) -> List[Dict]:
        """Execute a structured SQL query against the facts table."""
        if not sql_query.lower().strip().startswith("select"):
            return [{"error": "Only SELECT queries are allowed."}]
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute(sql_query)
                return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                return [{"error": str(e)}]
