"""
Phase 0: Docling Exploration Script
=====================================
Goal: Run Docling on the same 4 corpus documents that were analyzed
with pdfplumber, and compare output quality — especially for tables,
multi-column layouts, and reading order reconstruction.

Install first:  pip install docling
"""

import json
import time
from pathlib import Path

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
except ImportError:
    print("❌ Docling is not installed. Run: pip install docling")
    exit(1)

DATA_DIR = Path("data")
OUTPUT_DIR = Path(".refinery/docling_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Same 4 corpus documents as pdfplumber exploration
CORPUS = {
    "Class A - CBE Annual Report": "CBE ANNUAL REPORT 2023-24.pdf",
    "Class B - DBE Audit (Scanned)": "Audit Report - 2023.pdf",
    "Class C - FTA Assessment": "fta_performance_survey_final_report_2022.pdf",
    "Class D - Tax Expenditure": "tax_expenditure_ethiopia_2021_22.pdf",
}


def analyze_with_docling(name: str, filename: str):
    """Convert a document with Docling and analyze the output."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"  ❌ File not found: {filepath}")
        return None

    print(f"\n{'='*70}")
    print(f"  📄 {name}")
    print(f"  File: {filename}")
    print(f"{'='*70}")

    converter = DocumentConverter()

    start_time = time.time()
    try:
        result = converter.convert(str(filepath))
    except Exception as e:
        print(f"  ❌ Docling conversion failed: {e}")
        return {
            "name": name,
            "filename": filename,
            "status": "FAILED",
            "error": str(e),
        }
    elapsed = time.time() - start_time
    print(f"  ⏱️  Conversion time: {elapsed:.1f}s")

    doc = result.document

    # ------------------------------------------------------------------
    # 1. Export to Markdown and save
    # ------------------------------------------------------------------
    md_text = doc.export_to_markdown()
    md_path = OUTPUT_DIR / f"{Path(filename).stem}_docling.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"  💾 Markdown saved: {md_path}  ({len(md_text)} chars)")

    # ------------------------------------------------------------------
    # 2. Count structural elements
    # ------------------------------------------------------------------
    tables = list(doc.tables)
    pictures = list(doc.pictures)

    table_count = len(tables)
    picture_count = len(pictures)
    total_text_len = len(md_text)

    print(f"\n  📊 Structural Elements:")
    print(f"  Tables detected:  {table_count}")
    print(f"  Pictures found:   {picture_count}")
    print(f"  Markdown length:  {total_text_len} chars")

    # ------------------------------------------------------------------
    # 3. Show first 3 tables (if any)
    # ------------------------------------------------------------------
    if table_count > 0:
        print(f"\n  📋 Sample Tables (first {min(3, table_count)}):")
        for i, table in enumerate(tables[:3]):
            try:
                table_md = table.export_to_markdown()
                # Show first 500 chars of the table markdown
                preview = table_md[:500]
                print(f"\n  --- Table {i+1} ---")
                for line in preview.split("\n")[:8]:
                    print(f"  {line}")
                if len(table_md) > 500:
                    print(f"  ... ({len(table_md)} total chars)")
            except Exception as e:
                print(f"  --- Table {i+1}: Could not export ({e})")
    else:
        print(f"\n  ⚠️  No tables detected by Docling.")

    # ------------------------------------------------------------------
    # 4. Show first 500 chars of markdown (text quality check)
    # ------------------------------------------------------------------
    print(f"\n  📝 Markdown Preview (first 500 chars):")
    for line in md_text[:500].split("\n"):
        print(f"  {line}")
    if total_text_len > 500:
        print(f"  ... ({total_text_len} total chars)")

    # ------------------------------------------------------------------
    # 5. Show a middle section (to check reading order quality)
    # ------------------------------------------------------------------
    if total_text_len > 2000:
        mid = total_text_len // 2
        mid_text = md_text[mid : mid + 400]
        print(f"\n  📝 Middle Section Preview (chars {mid}–{mid+400}):")
        for line in mid_text.split("\n"):
            print(f"  {line}")

    return {
        "name": name,
        "filename": filename,
        "status": "OK",
        "conversion_time_s": round(elapsed, 1),
        "markdown_length": total_text_len,
        "table_count": table_count,
        "picture_count": picture_count,
    }


def main():
    print("=" * 70)
    print("  PHASE 0: Docling Exploration")
    print("  Converting the 4 corpus documents with Docling")
    print("  (This may take several minutes per document)")
    print("=" * 70)

    results = []
    for name, filename in CORPUS.items():
        result = analyze_with_docling(name, filename)
        if result:
            results.append(result)

    # ------------------------------------------------------------------
    # Final comparison table
    # ------------------------------------------------------------------
    print(f"\n\n{'='*70}")
    print("  📋 DOCLING vs PDFPLUMBER COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(
        f"  {'Document':<35} {'Status':<8} {'Time':<8} "
        f"{'Tables':<8} {'MD Len':<10}"
    )
    print(f"  {'-'*35} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")
    for r in results:
        status = r.get("status", "?")
        time_s = r.get("conversion_time_s", "?")
        tables = r.get("table_count", "?")
        md_len = r.get("markdown_length", "?")
        print(
            f"  {r['name']:<35} {status:<8} {time_s!s:<8} "
            f"  {tables!s:<8} {md_len!s:<10}"
        )

    # Save summary as JSON
    summary_path = OUTPUT_DIR / "docling_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  💾 Summary saved: {summary_path}")

    print("\n  ✅ Compare Docling output vs pdfplumber output!")
    print("     Look at: .refinery/docling_output/*_docling.md")
    print("     Key questions:")
    print("     - Did Docling extract text from Class B (scanned)?")
    print("     - Are Class A tables better structured?")
    print("     - Is reading order correct for multi-column pages?")


if __name__ == "__main__":
    main()
