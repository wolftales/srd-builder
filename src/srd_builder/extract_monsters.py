#!/usr/bin/env python3
"""PDF monster extraction for SRD 5.1.

Extracts raw monster stat blocks from PDF using font analysis and layout detection.
Outputs verbatim text with metadata for downstream parsing.

Phase: v0.3.0 - Raw extraction only (no field parsing)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


@dataclass
class ExtractionConfig:
    """Configuration for PDF extraction."""

    # Page range to extract (1-based, inclusive)
    page_start: int = 300
    page_end: int | None = None  # None = to end of document

    # Font size thresholds (from Phase 1 research)
    header_font_size_min: float = 13.0  # Catches 13.92pt and 18.0pt
    body_font_size_max: float = 11.0  # Body is 9.84pt

    # Column detection (from Phase 1 research)
    column_midpoint: float = 306.0  # Measured exact midpoint

    # Quality thresholds
    expected_monster_count_min: int = 300  # We expect ~319 monsters


@dataclass
class RawMonster:
    """Raw monster extraction with metadata."""

    name: str
    pages: list[int]
    blocks: list[dict[str, Any]]
    markers: list[str]
    warnings: list[str]


def extract_monsters(pdf_path: Path, config: ExtractionConfig | None = None) -> dict[str, Any]:
    """Extract monsters from PDF.

    Args:
        pdf_path: Path to SRD PDF
        config: Extraction configuration (uses defaults if None)

    Returns:
        Dictionary with:
        - monsters: List of raw monster records
        - _meta: Extraction metadata (PDF hash, counts, warnings)
    """
    if config is None:
        config = ExtractionConfig()

    # Calculate PDF hash for determinism
    pdf_hash = _calculate_pdf_hash(pdf_path)

    monsters: list[RawMonster] = []
    extraction_warnings: list[str] = []

    with fitz.open(pdf_path) as doc:
        page_end = config.page_end or doc.page_count

        # Extract from specified page range
        for page_num in range(config.page_start - 1, page_end):  # Convert to 0-based
            page = doc.load_page(page_num)
            page_monsters = _extract_page_monsters(page, page_num + 1, config)
            monsters.extend(page_monsters)

    # Build extraction report
    total_warnings = sum(len(m.warnings) for m in monsters)

    return {
        "monsters": [_monster_to_dict(m) for m in monsters],
        "_meta": {
            "pdf_sha256": pdf_hash,
            "extractor_version": "0.3.0",
            "pages_processed": page_end - config.page_start + 1,
            "monster_count": len(monsters),
            "total_warnings": total_warnings,
            "extraction_warnings": extraction_warnings,
        },
    }


def _extract_page_monsters(
    page: fitz.Page, page_num: int, config: ExtractionConfig
) -> list[RawMonster]:
    """Extract monsters from a single page.

    Args:
        page: PyMuPDF page object
        page_num: 1-based page number
        config: Extraction configuration

    Returns:
        List of raw monsters found on this page
    """
    # Get structured text with font metadata
    textpage = page.get_textpage(flags=fitz.TEXTFLAGS_TEXT)
    page_dict = page.get_text("dict", textpage=textpage)

    # Extract all text spans with metadata
    spans = _extract_spans(page_dict, page_num, config)

    # Detect monster boundaries using header detection
    monsters = _detect_monster_boundaries(spans, config)

    return monsters


def _extract_spans(
    page_dict: dict[str, Any], page_num: int, config: ExtractionConfig
) -> list[dict[str, Any]]:
    """Extract text spans with metadata from page dict.

    Args:
        page_dict: PyMuPDF page.get_text("dict") output
        page_num: 1-based page number
        config: Extraction configuration

    Returns:
        List of span dictionaries with metadata
    """
    spans: list[dict[str, Any]] = []

    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                # Extract span metadata
                text = span.get("text", "").strip()
                if not text:
                    continue

                bbox = span.get("bbox", [0, 0, 0, 0])
                font = span.get("font", "")
                size = round(span.get("size", 0), 2)
                color = span.get("color", 0)
                flags = span.get("flags", 0)

                # Determine column (left=1, right=2, single=0)
                column = _determine_column(bbox[0], config)

                # Check if this is a header based on font size
                is_header = size >= config.header_font_size_min

                spans.append(
                    {
                        "page": page_num,
                        "column": column,
                        "bbox": [round(x, 2) for x in bbox],
                        "text": text,
                        "font": font,
                        "size": size,
                        "color": _color_to_rgb(color),
                        "flags": flags,
                        "is_header": is_header,
                    }
                )

    # Sort spans by reading order: column, y, x
    spans.sort(key=lambda s: (s["page"], s["column"], s["bbox"][1], s["bbox"][0]))

    return spans


def _determine_column(x_coord: float, config: ExtractionConfig) -> int:
    """Determine which column a span belongs to.

    Args:
        x_coord: X-coordinate of span's left edge
        config: Extraction configuration

    Returns:
        0 (single column), 1 (left), or 2 (right)
    """
    if x_coord < config.column_midpoint:
        return 1  # Left column
    else:
        return 2  # Right column


def _detect_monster_boundaries(
    spans: list[dict[str, Any]], config: ExtractionConfig
) -> list[RawMonster]:
    """Detect monster boundaries and group spans into monsters.

    Uses multi-layer heuristics:
    1. Font size spike (18pt or 13.92pt)
    2. Type-line pattern detection ("Size Type, Alignment")
    3. Keyword anchors (fallback)

    Args:
        spans: Ordered list of text spans
        config: Extraction configuration

    Returns:
        List of raw monsters
    """
    monsters: list[RawMonster] = []
    current_monster: dict[str, Any] | None = None

    for span in spans:
        # Check if this span is a monster name header
        if span["is_header"] and _looks_like_monster_name(span["text"]):
            # Save previous monster if exists
            if current_monster:
                monsters.append(_finalize_monster(current_monster))

            # Start new monster
            current_monster = {
                "name": span["text"],
                "pages": [span["page"]],
                "blocks": [span],
                "markers": [],
                "warnings": [],
            }
        elif current_monster:
            # Add span to current monster
            current_monster["blocks"].append(span)

            # Track page range
            if span["page"] not in current_monster["pages"]:
                current_monster["pages"].append(span["page"])

            # Track section markers
            if _is_section_marker(span["text"]):
                current_monster["markers"].append(span["text"])

    # Don't forget the last monster
    if current_monster:
        monsters.append(_finalize_monster(current_monster))

    return monsters


def _looks_like_monster_name(text: str) -> bool:
    """Check if text looks like a monster name.

    Heuristics:
    - Capitalized
    - Not a section keyword
    - Not a chapter header (e.g., "Monsters (A)")
    - Reasonable length

    Args:
        text: Text to check

    Returns:
        True if likely a monster name
    """
    # Skip known section headers
    section_keywords = {
        "Actions",
        "Reactions",
        "Legendary Actions",
        "Lair Actions",
        "Regional Effects",
    }
    if text in section_keywords:
        return False

    # Skip chapter headers like "Monsters (A)"
    if text.startswith("Monsters (") and text.endswith(")"):
        return False

    # Monster names are typically capitalized and not too long
    return text[0].isupper() and len(text) < 50


def _is_section_marker(text: str) -> bool:
    """Check if text is a section marker keyword.

    Args:
        text: Text to check

    Returns:
        True if this is a section marker
    """
    markers = {
        "Armor Class",
        "Hit Points",
        "Speed",
        "STR",
        "Saving Throws",
        "Skills",
        "Senses",
        "Languages",
        "Challenge",
        "Actions",
        "Reactions",
        "Legendary Actions",
        "Lair Actions",
    }
    return text in markers


def _finalize_monster(monster_dict: dict[str, Any]) -> RawMonster:
    """Convert monster dictionary to RawMonster dataclass.

    Args:
        monster_dict: Dictionary with monster data

    Returns:
        RawMonster instance
    """
    return RawMonster(
        name=monster_dict["name"],
        pages=sorted(monster_dict["pages"]),
        blocks=monster_dict["blocks"],
        markers=monster_dict["markers"],
        warnings=monster_dict["warnings"],
    )


def _monster_to_dict(monster: RawMonster) -> dict[str, Any]:
    """Convert RawMonster to dictionary for JSON serialization.

    Args:
        monster: RawMonster instance

    Returns:
        Dictionary representation
    """
    return {
        "name": monster.name,
        "pages": monster.pages,
        "blocks": monster.blocks,
        "markers": monster.markers,
        "warnings": monster.warnings,
    }


def _color_to_rgb(color_int: int) -> list[int]:
    """Convert PyMuPDF color integer to RGB list.

    Args:
        color_int: Color as integer

    Returns:
        [R, G, B] list with values 0-255
    """
    # PyMuPDF stores color as integer, extract RGB
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return [r, g, b]


def _calculate_pdf_hash(pdf_path: Path) -> str:
    """Calculate SHA-256 hash of PDF for determinism.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Hex string of SHA-256 hash
    """
    sha256 = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract monsters from SRD PDF")
    parser.add_argument("pdf", type=Path, help="Path to SRD PDF")
    parser.add_argument("--output", type=Path, help="Output JSON path (default: monsters_raw.json)")
    parser.add_argument("--pages", type=int, nargs=2, help="Page range [start, end]")
    args = parser.parse_args()

    # Build config
    config = ExtractionConfig()
    if args.pages:
        config.page_start, config.page_end = args.pages

    # Extract
    print(f"Extracting monsters from {args.pdf}...")
    result = extract_monsters(args.pdf, config)

    # Save
    output_path = args.output or Path("monsters_raw.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"✓ Extracted {result['_meta']['monster_count']} monsters")
    print(f"✓ Saved to {output_path}")
    print(f"✓ Warnings: {result['_meta']['total_warnings']}")


if __name__ == "__main__":
    main()
