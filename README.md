![Refinery Banner](image.png)

# Document Intelligence Refinery

Production-grade agentic pipeline for document extraction, semantic chunking, and provenance-tracked querying. Built for the 10Academy Week 3 Challenge.

## Overview

The **Document Intelligence Refinery** is designed to solve the "last mile" problem of enterprise intelligence: extracting structured, verifiable data from heterogeneous document formats (digital PDFs, scanned images, complex layouts).

### Key Features

- **Triage Agent**: Automatically classifies documents by origin (digital/scanned) and layout complexity.
- **Multi-Strategy Extraction**: Routes documents to the most cost-effective extraction method (Fast Text, Layout-Aware, or Vision AI).
- **Semantic Chunking**: Implements the **Logical Document Unit (LDU)** pattern to preserve table structure and section context.
- **PageIndex Builder**: Generates a hierarchical navigation tree with AI-powered section summaries.
- **Provenance-First Design**: Every chunk and index node maintains spatial metadata and content hashes for 100% traceability.

## Setup

1. **Clone the repository**:

   ```bash
   git clone <repo-url>
   cd document-intelligence-refinery
   ```

2. **Environment Variables**:
   Create a `.env` file in the root directory:

   ```env
   OPENROUTER_API_KEY=your_key_here
   OPENROUTER_URL="https://openrouter.ai/api/v1"
   MODEL_NAME="openrouter/auto:free"
   ```

3. **Install Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Project Structure

- `src/models/`: Pydantic schemas for data integrity.
- `src/agents/`: Core logic for Triage, Extraction, and Indexing.
- `scripts/`: Execution scripts for running the pipeline stages.
- `.refinery/`: Local storage for profiles, extractions, chunks, and indexes.

## Usage

### Unified Pipeline Orchestrator (Recommended)

The fastest way to process the entire corpus with full visibility and timing:

```bash
python3 run_pipeline.py
```

This script coordinates Triage, Extraction (A/B/C), Semantic Chunking, and PageIndex building with progress tracking.

### Query Interface & Audit Mode

Once the pipeline completes, use the agentic interface in Stage 5:

```python
from src.agents.query_agent import QueryInterfaceAgent
agent = QueryInterfaceAgent(doc_id="cbe_report")
answer = agent.run_query("What are the total assets?")
print(answer)
```

### Manual Stage Execution

For granular control, run stages individually:

- `python3 scripts/run_triage.py`
- `python3 scripts/run_extraction.py`
- `python3 scripts/run_chunking.py`
- `python3 scripts/run_indexing.py`

## Documentation

- [INTERIM_REPORT.md](./INTERIM_REPORT.md): Detailed analysis of failure modes and architecture.
- [DOMAIN_NOTES.md](./DOMAIN_NOTES.md): Phase 0 research and decision matrix.
