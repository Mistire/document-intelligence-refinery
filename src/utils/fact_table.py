import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any
from src.models.fact_table import FactEntry

class FactTableManager:
    def __init__(self, db_path: str = ".refinery/refinery_facts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT,
                    fact_key TEXT,
                    fact_value TEXT,
                    unit TEXT,
                    period TEXT,
                    page_number INTEGER,
                    confidence REAL,
                    source_text TEXT
                )
            """)
            conn.commit()

    def store_facts(self, doc_id: str, facts: List[FactEntry]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for fact in facts:
                cursor.execute("""
                    INSERT INTO facts (doc_id, fact_key, fact_value, unit, period, page_number, confidence, source_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, fact.key, fact.value, fact.unit, fact.period, 
                    fact.page_number, fact.confidence, fact.source_text
                ))
            conn.commit()

    def query_facts(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute a structured SQL query against the facts table."""
        # Sanitize/Validate slightly - in production we'd use a more robust parser
        if not sql_query.lower().strip().startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                return [{"error": str(e)}]
