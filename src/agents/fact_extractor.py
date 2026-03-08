import json
import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.models.extracted_document import ExtractedDocument
from src.models.fact_table import FactEntry

class FactExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "openrouter/auto:free"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
            max_tokens=512
        )

    def extract_facts(self, doc: ExtractedDocument) -> List[FactEntry]:
        """Extract key facts from the document text and tables."""
        # We process the top pages or table-heavy areas
        # For demonstration, we'll take a subset of the first few tables/text
        content_sample = ""
        for table in doc.tables[:3]:
            content_sample += f"Table (Page {table.page_number}):\n{json.dumps(table.rows[:10])}\n"
        
        for block in doc.text_blocks[:10]:
            content_sample += f"(Page {block.page_number}): {block.text[:500]}\n"

        prompt = f"""
        Extract key numerical or financial facts from the following document content.
        Focus on: Revenue, Assets, Dates, Percentages, and key metrics.
        Return ONLY a JSON list of objects matching this schema:
        {{
            "key": "Fact description",
            "value": "Value string",
            "unit": "currency or unit",
            "period": "Time period if any",
            "page_number": int,
            "confidence": float (0-1),
            "source_text": "text snippet"
        }}
        
        Content:
        {content_sample}
        """

        messages = [
            SystemMessage(content="You are a financial data extractor. Output ONLY valid JSON."),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            data = json.loads(response.content)
            # Handle list vs single object
            if isinstance(data, dict):
                data = [data]
            
            facts = []
            for item in data:
                try:
                    facts.append(FactEntry(**item))
                except:
                    continue
            return facts
        except Exception as e:
            print(f"Error extracting facts: {e}")
            return []
