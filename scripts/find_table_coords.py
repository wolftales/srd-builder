#!/usr/bin/env python3
"""Find coordinates for a specific table to help with migration from legacy_parser.

This tool analyzes a specific page region to determine optimal coordinates
and column boundaries for split_column pattern configuration.

Usage:
    # Find coordinates for a table on page 62
    python scripts/find_table_coords.py --page 62 --name exchange_rates

    # Analyze specific region
    python scripts/find_table_coords.py --page 62 --region 50,270,530,595
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import pymupdf as fitz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def analyze_table_region(
    pdf_path: Path,
    page_num: int,
    x_min: float | None = None,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
) -> dict:
    """Analyze a page region to find table structure.

    Args:
        pdf_path: Path to PDF
        page_num: 1-indexed page number
        x_min, x_max, y_min, y_max: Region bounds (None = full page)

    Returns:
        Dict with analysis results
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # Convert to 0-indexed

    # Get page dimensions
    page_width = page.rect.width
    page_height = page.rect.height

    # Default to left column if no region specified
    if x_min is None:
        x_min = 0
    if x_max is None:
        x_max = page_width / 2
    if y_min is None:
        y_min = 0
    if y_max is None:
        y_max = page_height

    # Extract all words in region
    all_words = page.get_text("words")
    region_words = [w for w in all_words if x_min <= w[0] < x_max and y_min <= w[1] <= y_max]

    # Group by Y coordinate (rows)
    by_row = defaultdict(list)
    for word in region_words:
        y = round(word[1])  # Round to nearest pixel
        by_row[y].append(word)

    # Analyze column structure by x-coordinate clustering
    x_positions = [w[0] for w in region_words]
    x_sorted = sorted(x_positions)

    # Find gaps in x-coordinates (potential column boundaries)
    gaps = []
    for i in range(len(x_sorted) - 1):
        gap_size = x_sorted[i + 1] - x_sorted[i]
        if gap_size > 10:  # Significant gap
            gap_mid = (x_sorted[i] + x_sorted[i + 1]) / 2
            gaps.append((gap_mid, gap_size))

    doc.close()

    return {
        "page": page_num,
        "page_dimensions": {"width": page_width, "height": page_height},
        "region": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max},
        "words_found": len(region_words),
        "rows": len(by_row),
        "by_row": dict(by_row),
        "x_range": (min(x_positions), max(x_positions)) if x_positions else (0, 0),
        "y_range": (
            (
                min(w[1] for w in region_words),
                max(w[3] for w in region_words),  # w[3] is y1 (bottom edge)
            )
            if region_words
            else (0, 0)
        ),
        "column_gaps": gaps,
    }


def print_analysis(analysis: dict, table_name: str | None = None) -> None:
    """Print human-readable analysis with recommended config."""
    print("=" * 80)
    if table_name:
        print(f"TABLE COORDINATE ANALYSIS: {table_name}")
    else:
        print("TABLE COORDINATE ANALYSIS")
    print("=" * 80)
    print()

    print(f"Page: {analysis['page']}")
    print(
        f"Page dimensions: {analysis['page_dimensions']['width']:.0f} x {analysis['page_dimensions']['height']:.0f}"
    )
    print()

    region = analysis["region"]
    print("Search region:")
    print(
        f"  X: {region['x_min']:.0f} to {region['x_max']:.0f} (width: {region['x_max'] - region['x_min']:.0f})"
    )
    print(
        f"  Y: {region['y_min']:.0f} to {region['y_max']:.0f} (height: {region['y_max'] - region['y_min']:.0f})"
    )
    print()

    print(f"Words found: {analysis['words_found']}")
    print(f"Rows detected: {analysis['rows']}")
    print()

    x_range = analysis["x_range"]
    y_range = analysis["y_range"]
    print("Content bounds:")
    print(f"  X: {x_range[0]:.1f} to {x_range[1]:.1f} (width: {x_range[1] - x_range[0]:.1f})")
    print(f"  Y: {y_range[0]:.1f} to {y_range[1]:.1f} (height: {y_range[1] - y_range[0]:.1f})")
    print()

    # Show first few rows
    print("First 5 rows:")
    for y, words in sorted(analysis["by_row"].items())[:5]:
        text = " ".join([w[4] for w in sorted(words, key=lambda w: w[0])])
        print(f"  Y={y}: {text[:70]}{'...' if len(text) > 70 else ''}")
    print()

    # Column gap analysis
    if analysis["column_gaps"]:
        print("Detected column gaps (potential boundaries):")
        for gap_mid, gap_size in sorted(analysis["column_gaps"])[:10]:
            print(f"  x={gap_mid:.1f} (gap: {gap_size:.1f}px)")
        print()

    # Generate recommended config
    print("=" * 80)
    print("RECOMMENDED CONFIG (add to table_metadata.py):")
    print("=" * 80)
    print()

    # Calculate recommended region with padding
    x_min_rec = max(0, int(x_range[0] - 5))
    x_max_rec = int(x_range[1] + 5)
    y_min_rec = max(0, int(y_range[0] - 5))
    y_max_rec = int(y_range[1] + 5)

    name = table_name or "your_table"
    print(f'    "{name}": {{')
    print('        "pattern_type": "split_column",')
    print('        "source": "srd",')
    print(f'        "pages": [{analysis["page"]}],')
    print('        "headers": ["TODO", "TODO", "TODO"],  # ← Fill in from PDF')
    print('        "regions": [')
    print(
        f'            {{"x_min": {x_min_rec}, "x_max": {x_max_rec}, "y_min": {y_min_rec}, "y_max": {y_max_rec}}},'
    )
    print("        ],")

    # Suggest column boundaries based on gaps
    if len(analysis["column_gaps"]) >= 2:
        # Use the most significant gaps as boundaries
        boundaries = [int(g[0] - region["x_min"]) for g in sorted(analysis["column_gaps"])[:5]]
        boundaries_str = ", ".join(str(b) for b in boundaries)
        print(f'        "column_boundaries": [{boundaries_str}],  # ← Adjust as needed')
    else:
        print('        # "column_boundaries": [60, 120, 180],  # ← Add if multi-column')

    print('        "chapter": "TODO",  # ← Fill in chapter name')
    print('        "data_driven": True,')
    print('        "confirmed": False,  # Mark True after validation')
    print(f'        "validation": {{"expected_rows": {analysis["rows"]}}},')
    print('        "notes": "TODO - describe table",')
    print("    },")
    print()

    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Copy config above to table_metadata.py")
    print("2. Fill in headers by looking at PDF")
    print("3. Adjust column_boundaries if needed")
    print("4. Run: make tables")
    print("5. Validate: compare output to legacy parser")
    print("6. Mark confirmed: True when validated")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Find table coordinates for migration")
    parser.add_argument(
        "--page",
        type=int,
        required=True,
        help="Page number (1-indexed)",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Table name (e.g., 'exchange_rates')",
    )
    parser.add_argument(
        "--region",
        type=str,
        help="Region bounds as 'x_min,x_max,y_min,y_max' (default: left column)",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf"),
        help="Path to PDF file",
    )

    args = parser.parse_args()

    # Check PDF exists
    if not args.pdf.exists():
        print(f"Error: PDF not found at {args.pdf}", file=sys.stderr)
        return 1

    # Parse region if provided
    x_min = x_max = y_min = y_max = None
    if args.region:
        try:
            x_min, x_max, y_min, y_max = map(float, args.region.split(","))
        except ValueError:
            print("Error: --region must be 'x_min,x_max,y_min,y_max'", file=sys.stderr)
            return 1

    # Run analysis
    try:
        analysis = analyze_table_region(args.pdf, args.page, x_min, x_max, y_min, y_max)
        print_analysis(analysis, args.name)
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
