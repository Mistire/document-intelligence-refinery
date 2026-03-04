"""
Phase 0: Table Extraction Quality Check
========================================
Test how well pdfplumber extracts tables from each document.
"""

import pdfplumber
from pathlib import Path

DATA_DIR = Path("data")


def check_tables(filename, pages_to_check):
    """Extract and display tables from specific pages."""
    filepath = DATA_DIR / filename
    print(f"\n📄 {filename}")
    print(f"   Checking pages: {pages_to_check}")

    with pdfplumber.open(filepath) as pdf:
        for page_num in pages_to_check:
            if page_num >= len(pdf.pages):
                print(f"   Page {page_num + 1}: does not exist")
                continue

            page = pdf.pages[page_num]
            tables = page.extract_tables()

            if not tables:
                print(f"   Page {page_num + 1}: No tables found")
                continue

            for i, table in enumerate(tables):
                print(f"\n   Page {page_num + 1}, Table {i + 1}:")
                print(f"   Rows: {len(table)}, Columns: {len(table[0]) if table else 0}")

                # Print first 3 rows
                for row_idx, row in enumerate(table[:3]):
                    cleaned = [str(cell)[:20] if cell else "" for cell in row]
                    print(f"   Row {row_idx}: {cleaned}")

                if len(table) > 3:
                    print(f"   ... ({len(table) - 3} more rows)")


# Test key pages where you expect tables
# (you'll need to adjust page numbers after first exploration)
check_tables("CBE ANNUAL REPORT 2023-24.pdf", [19, 21, 22, 31, 32])
check_tables("tax_expenditure_ethiopia_2021_22.pdf", [17, 18, 19, 20, 24])
check_tables("fta_performance_survey_final_report_2022.pdf", [26, 27, 28, 48, 86])
check_tables("Audit Report - 2023.pdf", [8, 10, 11, 12, 13])  # Expect: "No tables found"
