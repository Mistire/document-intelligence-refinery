"""
Phase 0: Document Exploration Script
=====================================
Goal: Understand the differences between your 4 test documents
by measuring character density, image coverage, and text extractability.
"""

import pdfplumber
import os
import json
from pathlib import Path

DATA_DIR = Path("data")

# The 4 required corpus documents
CORPUS = {
    "Class A - CBE Annual Report": "CBE ANNUAL REPORT 2023-24.pdf",
    "Class B - DBE Audit (Scanned)": "Audit Report - 2023.pdf",
    "Class C - FTA Assessment": "fta_performance_survey_final_report_2022.pdf",
    "Class D - Tax Expenditure": "tax_expenditure_ethiopia_2021_22.pdf",
}


def analyze_page(page):
    """Analyze a single page and return metrics."""
    width = page.width
    height = page.height
    page_area = width * height

    # Extract text
    text = page.extract_text() or ""
    char_count = len(text)

    # Character density = characters / page area (in points)
    char_density = char_count / page_area if page_area > 0 else 0

    # Count images and their total area
    images = page.images
    image_count = len(images)
    image_area = 0
    for img in images:
        img_w = abs(img["x1"] - img["x0"])
        img_h = abs(img["top"] - img["bottom"])
        image_area += img_w * img_h

    image_ratio = image_area / page_area if page_area > 0 else 0

    # Tables detected
    tables = page.find_tables()
    table_count = len(tables)

    return {
        "page_area": round(page_area, 2),
        "char_count": char_count,
        "char_density": round(char_density, 6),
        "image_count": image_count,
        "image_area_ratio": round(image_ratio, 4),
        "table_count": table_count,
        "text_preview": text[:200].replace("\n", " ") if text else "[NO TEXT]",
    }


def analyze_document(name, filename):
    """Analyze all pages of a document."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"  ❌ File not found: {filepath}")
        return None

    print(f"\n{'='*70}")
    print(f"  📄 {name}")
    print(f"  File: {filename}")
    print(f"{'='*70}")

    with pdfplumber.open(filepath) as pdf:
        total_pages = len(pdf.pages)
        print(f"  Total pages: {total_pages}")

        # Analyze first 5 pages, middle page, and last page
        sample_pages = [0, 1, 2, 3, 4]
        if total_pages > 10:
            sample_pages.append(total_pages // 2)  # middle
        if total_pages > 5:
            sample_pages.append(total_pages - 1)    # last

        # Remove duplicates and out-of-range
        sample_pages = sorted(set(p for p in sample_pages if p < total_pages))

        # Aggregate metrics
        total_chars = 0
        total_images = 0
        total_tables = 0
        pages_with_no_text = 0

        for page_num in sample_pages:
            page = pdf.pages[page_num]
            metrics = analyze_page(page)

            total_chars += metrics["char_count"]
            total_images += metrics["image_count"]
            total_tables += metrics["table_count"]
            if metrics["char_count"] < 10:
                pages_with_no_text += 1

            print(f"\n  --- Page {page_num + 1} ---")
            print(f"  Characters:    {metrics['char_count']}")
            print(f"  Char density:  {metrics['char_density']}")
            print(f"  Images:        {metrics['image_count']}")
            print(f"  Image ratio:   {metrics['image_area_ratio']:.1%}")
            print(f"  Tables found:  {metrics['table_count']}")
            print(f"  Text preview:  {metrics['text_preview'][:100]}...")

        # Summary
        print(f"\n  📊 SUMMARY for {name}:")
        print(f"  Total pages sampled:    {len(sample_pages)}")
        print(f"  Pages with no text:     {pages_with_no_text}")
        print(f"  Total chars (sampled):  {total_chars}")
        print(f"  Total images (sampled): {total_images}")
        print(f"  Total tables (sampled): {total_tables}")

        # Classification guess
        if pages_with_no_text > len(sample_pages) * 0.5:
            origin_guess = "scanned_image"
        elif pages_with_no_text > 0:
            origin_guess = "mixed"
        else:
            origin_guess = "native_digital"

        if total_tables > 3:
            layout_guess = "table_heavy"
        elif total_images > 5:
            layout_guess = "figure_heavy"
        else:
            layout_guess = "single_column or multi_column"

        print(f"  🏷️  Origin guess:  {origin_guess}")
        print(f"  🏷️  Layout guess:  {layout_guess}")

    return {
        "name": name,
        "filename": filename,
        "total_pages": total_pages,
        "origin_guess": origin_guess,
        "layout_guess": layout_guess,
    }


def main():
    print("=" * 70)
    print("  PHASE 0: Document Exploration")
    print("  Analyzing the 4 corpus documents with pdfplumber")
    print("=" * 70)

    results = []
    for name, filename in CORPUS.items():
        result = analyze_document(name, filename)
        if result:
            results.append(result)

    # Final comparison
    print(f"\n\n{'='*70}")
    print("  📋 FINAL COMPARISON")
    print(f"{'='*70}")
    print(f"  {'Document':<35} {'Pages':<8} {'Origin':<18} {'Layout'}")
    print(f"  {'-'*35} {'-'*8} {'-'*18} {'-'*20}")
    for r in results:
        print(f"  {r['name']:<35} {r['total_pages']:<8} {r['origin_guess']:<18} {r['layout_guess']}")

    print("\n  ✅ Save your observations in DOMAIN_NOTES.md!")


if __name__ == "__main__":
    main()
