#!/usr/bin/env python3
"""Discover Y-coordinate ranges for table extraction.

This script helps find the exact Y-coordinate boundaries for tables in PDF files,
making it easier to migrate to new SRD versions.

Usage:
    python scripts/discover_table_coordinates.py <pdf_path> <table_name> <page1> [page2...]

Example:
    python scripts/discover_table_coordinates.py \\
        rulesets/srd_5_1/SRD_CC_v5.1.pdf \\
        armor \\
        63 64
"""

import sys
from collections import defaultdict
from pathlib import Path

import pymupdf


def discover_coordinates(pdf_path: str, table_name: str, pages: list[int]) -> None:
    """Find optimal Y-coordinate ranges for a table.

    Args:
        pdf_path: Path to PDF file
        table_name: Name of table (for display only)
        pages: List of page numbers (1-indexed)
    """
    print(f"\n{'=' * 70}")
    print(f"Table: {table_name}")
    print(f"PDF: {pdf_path}")
    print(f"Pages: {pages}")
    print(f"{'=' * 70}\n")

    doc = pymupdf.open(pdf_path)

    # Common cost/currency markers for filtering
    currency_markers = {"gp", "sp", "cp", "lb.", "oz."}

    for page_num in pages:
        page = doc[page_num - 1]  # Convert to 0-indexed
        words = page.get_text("words")

        # Group words by Y-coordinate (rows)
        rows_dict = defaultdict(list)
        for word in words:
            x0, y0, x1, y1, text, *_ = word
            y_key = round(y0, 1)
            rows_dict[y_key].append((x0, text))

        # Find all Y-coordinates
        all_y = sorted(rows_dict.keys())

        # Find rows with cost markers (likely data rows)
        data_rows = []
        for y_pos in all_y:
            row_words = [w[1] for w in sorted(rows_dict[y_pos], key=lambda w: w[0])]
            if any(marker in row_words for marker in currency_markers):
                data_rows.append((y_pos, row_words))

        print(f"Page {page_num}:")
        print(f"  Total Y-coordinates: {len(all_y)}")
        print(f"  Full Y range: {min(all_y):.1f} to {max(all_y):.1f}")

        if data_rows:
            data_y = [y for y, _ in data_rows]
            print(f"  Data rows found: {len(data_rows)}")
            print(f"  Data Y range: {min(data_y):.1f} to {max(data_y):.1f}")
            print(
                f"  Suggested range (with buffer): y_min={int(min(data_y) - 5)}, y_max={int(max(data_y) + 5)}"
            )
            print(
                f"  Suggested range (rounded): y_min={int(min(data_y) // 10) * 10}, y_max={int((max(data_y) + 10) // 10) * 10}"
            )

            print("\n  Sample data rows (first 3):")
            for y_pos, row_words in data_rows[:3]:
                row_text = " ".join(row_words[:8])  # First 8 words
                if len(row_words) > 8:
                    row_text += "..."
                print(f"    Y={y_pos:.1f}: {row_text}")

            print("\n  Sample data rows (last 3):")
            for y_pos, row_words in data_rows[-3:]:
                row_text = " ".join(row_words[:8])
                if len(row_words) > 8:
                    row_text += "..."
                print(f"    Y={y_pos:.1f}: {row_text}")
        else:
            print("  No data rows found (no currency markers)")
            print("\n  All rows (first 5):")
            for y_pos in all_y[:5]:
                row_words = [w[1] for w in sorted(rows_dict[y_pos], key=lambda w: w[0])]
                row_text = " ".join(row_words[:8])
                if len(row_words) > 8:
                    row_text += "..."
                print(f"    Y={y_pos:.1f}: {row_text}")

        print()

    doc.close()

    print(f"\n{'=' * 70}")
    print("Next steps:")
    print("1. Update parser in text_table_parser.py with suggested Y-ranges")
    print("2. Add ±10 buffer if table spans page edges")
    print("3. Run build to verify all rows extracted")
    print(f"{'=' * 70}\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]
    table_name = sys.argv[2]
    pages = [int(p) for p in sys.argv[3:]]

    # Validate PDF exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    discover_coordinates(pdf_path, table_name, pages)


if __name__ == "__main__":
    main()
