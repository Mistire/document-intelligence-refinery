# Lessons Learned: Engineering the Document Intelligence Refinery

During the development of the refinery, several technical challenges were encountered that required architectural refinements and debugging.

## 1. The "List vs. Header" Ambiguity (Heuristic Failure)

### The Failure

During the initial implementation of the `SemanticChunker`, our header detection heuristic used line length and ending punctuation as triggers. However, this caused numbered lists (e.g., "1. Executive Summary") to be incorrectly classified as section headers, leading to a deep, fragmented PageIndex tree where every list item was its own section.

### The Fix

We introduced a **Negation Filter** in the heuristic. Before a block is considered a header, it must pass a list-marker regex check. If it starts with `1.`, `a.`, or a bullet point, it is strictly categorized as a `list` item. This ensured that the PageIndex correctly identifies the structural skeleton of the document without "drowning" in list content.

## 2. PageIndex NameError (Import Management)

### The Failure

A regression was introduced in `indexer.py` where the `re` module was called for URL/ID sanitization but was not imported. This was caught during unit testing of the hierarchical index building logic.

### The Fix

We enforced **Modular Testing** early. By running `pytest tests/test_indexing.py` before the full pipeline run, we caught the missing import in a controlled environment rather than failing a 160-page PDF extraction run, which would have incurred significant LLM token costs.

## 3. The "Stitching" Problem (Stage 2 to 3)

### The Failure

Initial EXTRACTIONS from `Docling` used inconsistent bounding box formats compared to standard PDF coordinates (Top-Left vs. Bottom-Left). This caused the "provenance" pointers to point to the wrong areas of the page when visualized.

### The Fix

We implemented a **Normalization Adapter** in the `LayoutAwareStrategy` that translates all engine-specific coordinates into a standard normalized (0-1000) (x, y, w, h) model stored in the `BBox` Pydantic schema. This ensures that the Stage 5 Query Agent can provide consistent citations regardless of which extraction engine was used (Strategy A, B, or C).
