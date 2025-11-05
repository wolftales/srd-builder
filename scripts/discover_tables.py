#!/usr/bin/env python3
"""Discover all tables in SRD PDF using automated detection.

This script scans the PDF, detects tables using PyMuPDF, and generates
a report of candidates for extraction. This is the discovery phase that
feeds into table_targets.py.

Usage:
    python scripts/discover_tables.py [--pages START-END] [--output report.json]
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.srd_builder.table_indexer import TableIndexer


def discover_tables(pdf_path: Path, start_page: int = 1, end_page: int | None = None) -> dict:
    """Discover all tables in PDF.

    Args:
        pdf_path: Path to PDF file
        start_page: Starting page (1-indexed)
        end_page: Ending page (1-indexed), None = end of document

    Returns:
        Discovery report with table metadata
    """
    print(f"Scanning PDF: {pdf_path}")
    print(f"Page range: {start_page} to {end_page or 'end'}")
    print()

    indexer = TableIndexer(pdf_path)
    tables = indexer.discover_all_tables(
        start_page=start_page,
        end_page=end_page,
        include_equipment=True,
        use_auto_detection=True,
    )

    # Generate report
    report = indexer.generate_report()

    # Add analysis
    report["analysis"] = _analyze_discoveries(tables)

    return report


def _analyze_discoveries(tables: list) -> dict:
    """Analyze discovered tables for patterns.

    Args:
        tables: List of TableMetadata objects

    Returns:
        Analysis dict with insights
    """
    # Group by page ranges
    by_section = {
        "character_creation": [t for t in tables if 1 <= t.page <= 15],
        "classes": [t for t in tables if 16 <= t.page <= 50],
        "equipment": [t for t in tables if 62 <= t.page <= 73],
        "spells": [t for t in tables if 105 <= t.page <= 194],
        "combat": [t for t in tables if 195 <= t.page <= 250],
        "monsters": [t for t in tables if 261 <= t.page <= 394],
        "other": [t for t in tables if t.page > 394 or t.page < 1],
    }

    return {
        "by_section": {
            section: len(tables_list) for section, tables_list in by_section.items() if tables_list
        },
        "total_discovered": len(tables),
        "avg_rows": sum(t.row_count for t in tables) / len(tables) if tables else 0,
        "avg_cols": sum(t.column_count for t in tables) / len(tables) if tables else 0,
    }


def print_report(report: dict) -> None:
    """Print human-readable discovery report.

    Args:
        report: Discovery report dict
    """
    print("=" * 80)
    print("TABLE DISCOVERY REPORT")
    print("=" * 80)
    print()

    print(f"Total tables discovered: {report['total_tables']}")
    print(f"Pages with tables: {report['pages_with_tables']}")
    print(f"Page range: {report['page_range'][0]}-{report['page_range'][1]}")
    print()

    print("Analysis:")
    analysis = report["analysis"]
    print(
        f"  Average dimensions: {analysis['avg_rows']:.1f} rows × {analysis['avg_cols']:.1f} cols"
    )
    print()

    print("By section:")
    for section, count in sorted(analysis["by_section"].items()):
        print(f"  {section}: {count} tables")
    print()

    print("By page:")
    for page, count in sorted(report["tables_by_page"].items()):
        print(f"  Page {page}: {count} table(s)")
    print()

    print("Estimated table types:")
    for table_id, count in sorted(report["tables_by_id"].items()):
        if table_id != "unknown":
            print(f"  {table_id}: {count} instance(s)")
    unknown_count = report["tables_by_id"].get("unknown", 0)
    if unknown_count:
        print(f"  unknown: {unknown_count} (need manual review)")
    print()

    print("=" * 80)
    print("Next steps:")
    print("  1. Review discoveries (see --output for full details)")
    print("  2. Identify new tables to add to table_targets.py")
    print("  3. Assign categories using established taxonomy")
    print("  4. Run extraction build")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Discover tables in SRD PDF")
    parser.add_argument(
        "--pages",
        type=str,
        help="Page range to scan (e.g., '1-100' or '60-75')",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save detailed report to JSON file",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf"),
        help="Path to PDF file (default: rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf)",
    )

    args = parser.parse_args()

    # Parse page range
    start_page = 1
    end_page = None
    if args.pages:
        if "-" in args.pages:
            start_str, end_str = args.pages.split("-")
            start_page = int(start_str)
            end_page = int(end_str)
        else:
            start_page = int(args.pages)

    # Check PDF exists
    if not args.pdf.exists():
        print(f"Error: PDF not found at {args.pdf}", file=sys.stderr)
        print("Specify path with --pdf", file=sys.stderr)
        return 1

    # Run discovery
    try:
        report = discover_tables(args.pdf, start_page, end_page)
        print_report(report)

        # Save detailed report if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"\n✓ Detailed report saved to {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
