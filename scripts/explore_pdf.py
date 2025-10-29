#!/usr/bin/env python3
"""Dump font/column metrics for a sample of pages."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean

import fitz  # PyMuPDF


def inspect_page(page: fitz.Page) -> dict:
    """Analyze font sizes, column positions for a single page."""
    textpage = page.get_textpage()
    data = page.get_text("dict", textpage=textpage)
    fonts: Counter[tuple[str, float]] = Counter()
    column_edges: list[float] = []

    for block in data["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                font = span.get("font", "")
                size = span.get("size", 0.0)
                fonts[(font, round(size, 2))] += len(text)
                if not (bbox := span.get("bbox")) or len(bbox) < 4:
                    continue
                column_edges.append(bbox[0])

    midpoint = page.rect.width / 2
    left = [value for value in column_edges if value < midpoint]
    right = [value for value in column_edges if value >= midpoint]

    return {
        "page": page.number + 1,
        "midpoint": round(midpoint, 2),
        "fonts": [(f"{font} @ {size}pt", count) for (font, size), count in fonts.most_common(10)],
        "left_col_avg": round(mean(left), 2) if left else 0,
        "right_col_avg": round(mean(right), 2) if right else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze PDF font sizes and column layout")
    parser.add_argument("pdf", type=Path, help="Path to SRD PDF")
    parser.add_argument(
        "--pages", nargs="*", type=int, help="1-based page numbers to inspect (default: all)"
    )
    parser.add_argument("--output", type=Path, help="Save JSON report to file")
    args = parser.parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")

    with fitz.open(args.pdf) as doc:
        pages = args.pages or range(1, min(doc.page_count + 1, 11))  # Default: first 10 pages
        report = [inspect_page(doc.load_page(page_number - 1)) for page_number in pages]

    output_json = json.dumps(report, indent=2)

    if args.output:
        args.output.write_text(output_json)
        print(f"Report saved to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
