
## 1. Extraction Strategy Decision Tree

Based on empirical analysis of the 4 corpus documents:

```mermaid
flowchart TD
    START["New Document"] --> CHECK_CHARS{"Avg char count per page > 100"}
    CHECK_CHARS -- "YES" --> CHECK_IMAGES{"Image area > 50% of page?"}
    CHECK_CHARS -- "NO" --> SCANNED["Scanned → Strategy C\n(Vision AI)"]
    CHECK_IMAGES -- "YES" --> MIXED["Mixed → Strategy B\n(Layout-Aware)"]
    CHECK_IMAGES -- "NO" --> CHECK_TABLES{"Tables detected > 2 per page?"}
    CHECK_TABLES -- "YES" --> TABLE_HEAVY["Table-Heavy → Strategy B"]
    CHECK_TABLES -- "NO" --> CHECK_COLUMNS{"Multi-column\nlayout?"}
    CHECK_COLUMNS -- "YES" --> MULTI_COL["Multi-Column → Strategy B"]
    CHECK_COLUMNS -- "NO" --> SIMPLE["Simple → Strategy A\n(Fast Text)"]
```

### Empirical Justification

* Class B had < 20 chars per page on average → scanned.
* Class A had mixed pages (0 chars + 1500+ chars) → hybrid.
* Class C had 3000–5000+ chars per page → clearly digital.
* Class D had consistent digital text but dense numeric tables.

Routing must happen at **page-level**, not only document-level.

---

## 2. Failure Modes Observed

---

### Class A — CBE Annual Report (Hybrid Digital)

**Observations:**

* Some pages (cover, final page) had zero extractable text.
* Core pages had 800–2000+ characters.
* Tables were detected in financial sections.
* Minor encoding artifacts (`Â`) present.

**Table Behavior:**

* Headers generally aligned with numeric data.
* Financial values extracted correctly.
* Multi-row headers occasionally split across rows.

**Layout Behavior:**

* Multi-column sections exist.
* Possible interleaving risk if naive text concatenation is used.

**Failure Modes:**

* Encoding artifacts require cleanup.
* Hybrid nature requires page-level OCR fallback.
* Multi-column pages may require layout-aware extraction.

**Conclusion:**
Strategy B (Layout-Aware) with selective OCR fallback.

---

### Class B — DBE Audit Report (Scanned)

This is the most critical discovery.

**Observations:**

* 6/7 sampled pages had zero characters.
* Image area ~100% per page.
* No tables detected.
* Extracted text layer effectively nonexistent.

**Failure Mode:**

* pdfplumber extraction fails completely.
* Table detection impossible.
* Downstream chunking would silently ingest empty content.

**Conclusion:**
Requires Strategy C (Vision AI / OCR).
Direct extraction is non-viable.

This document defines the OCR routing boundary.

---

### Class C — FTA Assessment (Clean Digital, Structured)

**Observations:**

* High character density (0.008–0.01).
* Thousands of characters per page.
* Multiple tables detected reliably.
* Clear hierarchical structure visible in text extraction.

**Table Behavior:**

* Extracted tables generally well-formed.
* Some small tables split across pages.
* Numeric values preserved accurately.

**Failure Modes:**

* Some small tables detected as 1-row artifacts.
* Minor header fragmentation in complex layouts.

**Conclusion:**
Strategy B (Layout-Aware) preferred for structured parsing.
Strategy A possible but may lose table structure.

---

### Class D — Tax Expenditure (Numeric-Heavy, Table-Dense)

**Observations:**

* Consistent digital text extraction.
* Dense numeric tables (10–12 columns).
* Multi-row headers split into fragments.
* Many empty cells in extracted output (header alignment artifacts).

**Table Behavior:**

* All numeric values appear present.
* Columns sometimes misaligned.
* Header rows fragmented across multiple rows.

**Failure Modes:**

* Complex table headers broken into separate rows.
* Blank cells where merged cells existed in PDF.
* Multi-page table continuity not preserved automatically.

**Conclusion:**
Strategy B required.
Post-processing logic needed for header reconstruction and column alignment.

---

## 3. Threshold Values (Empirically Determined)

| Metric                           | Threshold     | Rationale                                              |
| -------------------------------- | ------------- | ------------------------------------------------------ |
| `min_char_count_per_page`        | 100           | Below this, pages behave like scanned images (Class B) |
| `max_image_area_ratio`           | 0.50 (50%)    | Above this, page is image-dominated                    |
| `min_table_detection_per_sample` | 2 tables/page | Above this suggests table-heavy document               |
| `low_char_density`               | < 0.0005      | Strong signal of scanned page                          |
| `high_char_density`              | > 0.005       | Strong signal of digital structured page               |

These values are derived directly from observed distributions in Classes A–D.

---

## 4. Pipeline Architecture Diagram

```mermaid
flowchart TD
    DOC["Input Document"] --> TRIAGE["Stage 1: Triage Agent"]
    TRIAGE --> PROFILE["DocumentProfile"]
    PROFILE --> ROUTER["Stage 2: ExtractionRouter"]
    ROUTER --> A["Strategy A: Fast Text"]
    ROUTER --> B["Strategy B: Layout-Aware"]
    ROUTER --> C["Strategy C: Vision AI"]
    A & B & C --> ED["ExtractedDocument"]
    ED --> CHUNKER["Stage 3: Semantic Chunker"]
    CHUNKER --> LDUS["LDUs"]
    LDUS --> INDEXER["Stage 4: PageIndex Builder"]
    LDUS --> VS["Vector Store"]
    LDUS --> SQL["Fact Table"]
    INDEXER --> TREE["PageIndex Tree"]
    TREE --> AGENT["Stage 5: Query Agent"]
    VS --> AGENT
    SQL --> AGENT
    AGENT --> ANSWER["Answer + ProvenanceChain"]
```

Key Insight:
Extraction must precede semantic chunking. Poor extraction leads to garbage LDUs.

---

## 5. Cost Analysis (Estimated)

| Strategy         | Cost per Page | Cost for 161-page Doc | When Used                       |
| ---------------- | ------------- | --------------------- | ------------------------------- |
| A (Fast Text)    | ~$0.00        | ~$0.00                | Clean digital, simple layout    |
| B (Layout-Aware) | ~$0.002       | ~$0.32                | Multi-column, structured tables |
| C (Vision AI)    | ~$0.03–0.10   | ~$4.83–16.10          | Scanned, image-based PDFs       |

Observation:

* Running Strategy C on all documents would be wasteful.
* Class B justifies OCR cost.
* Others do not.

Routing significantly reduces compute cost.

---

## 6. Tools Evaluated

| Tool       | Tested | Notes                                                        |
| ---------- | ------ | ------------------------------------------------------------ |
| pdfplumber | ✅      | Fast, reliable for digital PDFs, bbox support, good baseline |
| Docling    | ❌      | Not evaluated in Phase 0                                     |
| MinerU     | ❌      | Not evaluated in Phase 0                                     |

Future evaluation needed for:

* Complex table reconstruction
* Multi-column reading order preservation
* OCR accuracy comparison

---

# Final Phase 0 Conclusion

The corpus is structurally heterogeneous.

Key findings:

1. OCR is mandatory for scanned documents (Class B).
2. Hybrid documents require page-level routing (Class A).
3. Digital structured reports benefit from layout-aware extraction (Class C, D).
4. Table extraction quality varies significantly and requires post-processing logic.
5. Extraction strategy must be adaptive and cost-aware.

