#!/usr/bin/env python3
"""Investigate spell PDF structure to inform refactoring decisions.

This script analyzes:
1. Font metadata (sizes, names) for semantic pattern detection
2. Spell boundary contamination (like conditions had)
3. Paragraph spacing patterns for segmentation
4. Column layout detection

Run this before refactoring extract_spells.py and parse_spells.py to validate
assumptions about what needs fixing.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pymupdf

# Spell pages from extraction_metadata.py
SPELL_START_PAGE = 117
SPELL_END_PAGE = 186


def analyze_font_metadata(pdf_path: Path, sample_pages: list[int] | None = None) -> dict:
    """Analyze font usage patterns across spell pages.

    Args:
        pdf_path: Path to SRD PDF
        sample_pages: Specific pages to analyze (default: first 3 spell pages)

    Returns:
        Dict with font frequency, size distribution, and semantic patterns
    """
    sample_pages = sample_pages or [SPELL_START_PAGE, SPELL_START_PAGE + 1, SPELL_START_PAGE + 2]

    doc = pymupdf.open(pdf_path)
    font_stats = defaultdict(lambda: {"count": 0, "sizes": set(), "sample_text": []})
    size_distribution = defaultdict(int)

    for page_num in sample_pages:
        page = doc[page_num - 1]  # PyMuPDF is 0-indexed
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:  # Skip non-text blocks
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_name = span.get("font", "unknown")
                    font_size = round(span.get("size", 0), 1)
                    text = span.get("text", "").strip()

                    if text:
                        font_stats[font_name]["count"] += 1
                        font_stats[font_name]["sizes"].add(font_size)
                        if len(font_stats[font_name]["sample_text"]) < 3:
                            font_stats[font_name]["sample_text"].append(text[:50])

                        size_distribution[font_size] += 1

    doc.close()

    # Convert sets to lists for JSON serialization
    for font_data in font_stats.values():
        font_data["sizes"] = sorted(list(font_data["sizes"]))

    return {
        "sample_pages": sample_pages,
        "font_families": dict(font_stats),
        "size_distribution": dict(sorted(size_distribution.items())),
        "analysis": {
            "most_common_font": max(font_stats.items(), key=lambda x: x[1]["count"])[0],
            "unique_sizes": sorted(size_distribution.keys(), reverse=True),
            "likely_spell_name_size": max(size_distribution.keys()) if size_distribution else None,
        },
    }


def check_spell_boundaries(raw_spells_path: Path) -> dict:
    """Check if spell boundaries are contaminated (like conditions were).

    Args:
        raw_spells_path: Path to spells_raw.json

    Returns:
        Dict with contamination findings
    """
    if not raw_spells_path.exists():
        return {"error": f"File not found: {raw_spells_path}"}

    data = json.loads(raw_spells_path.read_text(encoding="utf-8"))
    spells = data.get("spells", [])

    contamination_cases = []

    for i in range(len(spells) - 1):
        current = spells[i]
        next_spell = spells[i + 1]

        current_name = current.get("name", "")
        next_name = next_spell.get("name", "")
        current_text = current.get("text", "")

        # Check if current spell's text contains the next spell's name
        if next_name and next_name in current_text:
            # Find position in text
            text_lines = current_text.split("\n")
            for line_idx, line in enumerate(text_lines):
                if next_name in line:
                    contamination_cases.append(
                        {
                            "spell_index": i,
                            "spell_name": current_name,
                            "contaminant": next_name,
                            "line_number": line_idx + 1,
                            "line_content": line.strip()[:100],
                        }
                    )
                    break

    return {
        "total_spells": len(spells),
        "contamination_count": len(contamination_cases),
        "contaminated": contamination_cases[:10],  # Show first 10
        "clean": len(contamination_cases) == 0,
    }


def analyze_paragraph_spacing(pdf_path: Path, sample_page: int = 119) -> dict:
    """Analyze vertical spacing to detect paragraph breaks.

    Args:
        pdf_path: Path to SRD PDF
        sample_page: Page to analyze (default: 119, has multi-paragraph spells)

    Returns:
        Dict with spacing statistics and threshold recommendations
    """
    doc = pymupdf.open(pdf_path)
    page = doc[sample_page - 1]
    blocks = page.get_text("dict")["blocks"]

    line_positions = []

    for block in blocks:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            # Get bounding box
            bbox = line.get("bbox", [0, 0, 0, 0])
            y_position = bbox[1]  # Top Y coordinate
            line_height = bbox[3] - bbox[1]
            text = "".join(span.get("text", "") for span in line.get("spans", []))

            line_positions.append(
                {"y": y_position, "height": line_height, "text": text.strip()[:50]}
            )

    doc.close()

    # Sort by Y position (top to bottom)
    line_positions.sort(key=lambda x: x["y"])

    # Calculate gaps between consecutive lines
    gaps = []
    for i in range(len(line_positions) - 1):
        current = line_positions[i]
        next_line = line_positions[i + 1]
        gap = next_line["y"] - (current["y"] + current["height"])
        gaps.append(
            {
                "gap": round(gap, 2),
                "after_text": current["text"],
                "before_text": next_line["text"],
            }
        )

    gap_values = [g["gap"] for g in gaps]
    avg_gap = sum(gap_values) / len(gap_values) if gap_values else 0

    # Find large gaps (likely paragraph breaks)
    large_gaps = [g for g in gaps if g["gap"] > avg_gap * 1.5]

    return {
        "page": sample_page,
        "line_count": len(line_positions),
        "gap_stats": {
            "min": round(min(gap_values), 2) if gap_values else 0,
            "avg": round(avg_gap, 2),
            "max": round(max(gap_values), 2) if gap_values else 0,
        },
        "large_gaps_count": len(large_gaps),
        "large_gaps": large_gaps[:5],  # Show first 5
        "recommended_threshold": round(avg_gap * 1.5, 2),
    }


def check_column_layout(pdf_path: Path, sample_page: int = 118) -> dict:
    """Detect if spell pages use single or two-column layout.

    Args:
        pdf_path: Path to SRD PDF
        sample_page: Page to analyze

    Returns:
        Dict with column detection results
    """
    doc = pymupdf.open(pdf_path)
    page = doc[sample_page - 1]
    page_width = page.rect.width
    blocks = page.get_text("dict")["blocks"]

    x_positions = []

    for block in blocks:
        if block.get("type") != 0:
            continue

        bbox = block.get("bbox", [0, 0, 0, 0])
        x_left = bbox[0]
        x_right = bbox[2]
        width = x_right - x_left

        x_positions.append(
            {
                "x_left": round(x_left, 2),
                "x_right": round(x_right, 2),
                "width": round(width, 2),
            }
        )

    doc.close()

    # Cluster by x_left position
    left_positions = [x["x_left"] for x in x_positions]
    left_avg = sum(left_positions) / len(left_positions) if left_positions else 0

    # Count positions in left vs right half
    midpoint = page_width / 2
    left_half = [x for x in x_positions if x["x_left"] < midpoint]
    right_half = [x for x in x_positions if x["x_left"] >= midpoint]

    return {
        "page": sample_page,
        "page_width": round(page_width, 2),
        "block_count": len(x_positions),
        "left_half_blocks": len(left_half),
        "right_half_blocks": len(right_half),
        "avg_x_left": round(left_avg, 2),
        "layout": "two-column" if len(right_half) > 3 else "single-column",
    }


def main():
    """Run all investigations and save results."""
    # Find PDF
    pdf_path = Path("rulesets/srd_5_1/raw").glob("*.pdf")
    pdf_path = next(pdf_path, None)

    if not pdf_path:
        print("Error: No PDF found in rulesets/srd_5_1/raw/")
        return 1

    print(f"Analyzing spell structure in {pdf_path.name}...\n")

    results = {}

    # 1. Font metadata
    print("1. Analyzing font metadata...")
    results["font_metadata"] = analyze_font_metadata(pdf_path)
    print(f"   Found {len(results['font_metadata']['font_families'])} font families")

    # 2. Boundary contamination
    print("2. Checking spell boundaries...")
    raw_spells_path = Path("rulesets/srd_5_1/raw/spells_raw.json")
    results["boundary_check"] = check_spell_boundaries(raw_spells_path)
    if results["boundary_check"].get("clean"):
        print("   ✓ No boundary contamination found")
    else:
        print(f"   ⚠ Found {results['boundary_check']['contamination_count']} contaminated spells")

    # 3. Paragraph spacing
    print("3. Analyzing paragraph spacing...")
    results["paragraph_spacing"] = analyze_paragraph_spacing(pdf_path)
    print(f"   Recommended threshold: {results['paragraph_spacing']['recommended_threshold']}px")

    # 4. Column layout
    print("4. Checking column layout...")
    results["column_layout"] = check_column_layout(pdf_path)
    print(f"   Layout: {results['column_layout']['layout']}")

    # Save results
    output_path = Path("scripts/spell_investigation_results.json")
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print(f"\n✓ Results saved to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
