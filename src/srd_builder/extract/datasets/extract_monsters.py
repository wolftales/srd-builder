#!/usr/bin/env python3
"""PDF monster extraction for SRD 5.1.

Extracts raw monster stat blocks from PDF using font analysis and layout detection.
Outputs verbatim text with metadata for downstream parsing.

Phase: v0.3.0 - Raw extraction only (no field parsing)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF — kept for fitz.Page type hints

from ...constants import EXTRACTOR_VERSION
from ...utils.pdf_layout import (
    FONT_SIZE_TOLERANCE,
    Y_COORDINATE_TOLERANCE,
    extract_columnar_spans,
    merge_spans_into_lines,
    span_matches_predicate,
)
from ...utils.pdf_probe import open_pdf, pdf_sha256

# Extraction tolerances. Y/font-size tolerances are imported from utils.pdf_layout
# (kept re-exported here so existing call sites referencing them via this module
# continue to work). The remaining constants are monster-specific.
MAX_VERTICAL_GAP = 30  # Maximum vertical gap between text blocks (points)
MAX_MONSTER_NAME_LENGTH = 50  # Maximum reasonable monster name length (characters)

# Re-export for backward compat with any tests that import these from here.
__all__ = [
    "FONT_SIZE_TOLERANCE",
    "Y_COORDINATE_TOLERANCE",
    "MAX_VERTICAL_GAP",
    "MAX_MONSTER_NAME_LENGTH",
]


@dataclass
class ExtractionConfig:
    """Configuration for PDF extraction."""

    # Page range to extract (1-based, inclusive)
    page_start: int = 261  # "Monsters (A)" starts here
    page_end: int = 403  # Include "Appendix MM-B: Nonplayer Characters" (395-403)

    # Font size thresholds (from Phase 1/2 research - CORRECTED!)
    category_font_size: float = 13.92  # Category headers like "Elementals"
    monster_name_font_size: float = 12.0  # Individual monster names (CORRECTED from 9.84!)
    header_font_size_min: float = 13.0  # General header threshold

    # Font patterns (from Phase 1/2 research)
    monster_name_font: str = "Calibri-Bold"  # 12.0pt Calibri-Bold (monster names)
    size_type_font: str = "Calibri-Italic"  # Size/type line follows name
    trait_name_font: str = "Calibri-BoldItalic"  # Trait names like "Air Form" (NOT monster names!)

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
    pdf_hash = pdf_sha256(pdf_path)

    monsters: list[RawMonster] = []
    extraction_warnings: list[str] = []

    # Collect ALL lines from ALL pages first (fixes cross-page monsters)
    all_lines: list[dict[str, Any]] = []

    with open_pdf(pdf_path) as doc:
        page_end = config.page_end or doc.page_count

        # Extract lines from all pages
        for page_num in range(config.page_start - 1, page_end):  # Convert to 0-based
            page = doc.load_page(page_num)
            page_lines = _extract_page_lines(page, page_num + 1, config)
            all_lines.extend(page_lines)

    # Detect monster boundaries across ALL pages (handles cross-page monsters)
    monsters = _detect_monster_boundaries(all_lines, config)

    # Build extraction report
    total_warnings = sum(len(m.warnings) for m in monsters)

    return {
        "monsters": [_monster_to_dict(m) for m in monsters],
        "_meta": {
            "pdf_filename": pdf_path.name,
            "pdf_sha256": pdf_hash,
            "extractor_version": EXTRACTOR_VERSION,
            "pages_processed": page_end - config.page_start + 1,
            "monster_count": len(monsters),
            "total_warnings": total_warnings,
            "extraction_warnings": extraction_warnings,
        },
    }


def _extract_page_lines(
    page: fitz.Page, page_num: int, config: ExtractionConfig
) -> list[dict[str, Any]]:
    """Extract column-aware merged lines from a single page."""
    spans = extract_columnar_spans(
        page,
        page_num,
        column_midpoint=config.column_midpoint,
        header_size_min=config.header_font_size_min,
    )
    return merge_spans_into_lines(spans)


def _detect_monster_boundaries(
    lines: list[dict[str, Any]], config: ExtractionConfig
) -> list[RawMonster]:
    """Detect monster boundaries and group lines into monsters.

    Uses font pattern detection on merged lines (not fragmented spans):
    1. 9.84pt Calibri-Bold = Individual monster names
    2. 13.92pt GillSans-SemiBold = Category headers (skip these)
    3. Validates with size/type line (Calibri-Italic within 20pt Y-distance)

    Args:
        lines: Ordered list of merged text lines
        config: Extraction configuration

    Returns:
        List of raw monsters
    """
    monsters: list[RawMonster] = []
    current_monster: dict[str, Any] | None = None

    for i, line in enumerate(lines):
        # Check if this is an individual monster name (9.84pt Calibri-Bold)
        if _is_monster_name_line(line, config):
            # Validate with lookahead: next Italic line should be size/type
            if _has_size_type_line_following(lines, i, config):
                # Save previous monster if exists
                if current_monster:
                    monsters.append(_finalize_monster(current_monster))

                # Start new monster - include ALL original spans from this line
                # Clean name: remove tabs, newlines, multiple spaces
                clean_name = " ".join(line["text"].split())

                current_monster = {
                    "name": clean_name,
                    "pages": [line["page"]],
                    "blocks": line["spans"],  # Use original spans
                    "markers": [],
                    "warnings": [],
                }
        elif current_monster:
            # Add all spans from this line to current monster
            current_monster["blocks"].extend(line["spans"])

            # Track page range
            if line["page"] not in current_monster["pages"]:
                current_monster["pages"].append(line["page"])

            # Track section markers
            if _is_section_marker(line["text"]):
                current_monster["markers"].append(line["text"])

    # Don't forget the last monster
    if current_monster:
        monsters.append(_finalize_monster(current_monster))

    return monsters


def _is_monster_name_line(line: dict[str, Any], config: ExtractionConfig) -> bool:
    """Check if line is a monster name (9.84pt Calibri-Bold).

    Args:
        line: Merged line dictionary
        config: Extraction configuration

    Returns:
        True if this looks like a monster name
    """
    # Font + size predicate: exact Calibri-Bold match with a small size
    # tolerance window around config.monster_name_font_size.
    name_predicate = {
        "font_exact": config.monster_name_font,
        "size_min": config.monster_name_font_size - FONT_SIZE_TOLERANCE,
        "size_max": config.monster_name_font_size + FONT_SIZE_TOLERANCE,
    }
    if not span_matches_predicate(line, name_predicate):
        return False

    # Must not be a stat block field keyword
    stat_fields = {
        "Speed",
        "Armor Class",
        "Hit Points",
        "STR",
        "DEX",
        "CON",
        "INT",
        "WIS",
        "CHA",
        "Saving Throws",
        "Skills",
        "Senses",
        "Languages",
        "Challenge",
        "Damage Resistances",
        "Damage Immunities",
        "Damage Vulnerabilities",
        "Condition Immunities",
    }
    if line["text"] in stat_fields:
        return False

    # Must not be an "Actions" header
    if line["text"] in {"Actions", "Reactions", "Legendary Actions"}:
        return False

    return True


def _has_size_type_line_following(
    lines: list[dict[str, Any]], current_index: int, config: ExtractionConfig
) -> bool:
    """Check if a size/type line (Calibri-Italic) follows within reasonable distance.

    Args:
        lines: All merged lines
        current_index: Index of potential monster name line
        config: Extraction configuration

    Returns:
        True if validated by following size/type line
    """
    if current_index >= len(lines) - 1:
        return False

    current_line = lines[current_index]
    current_y = current_line["bbox"][1]  # Top Y coordinate

    # Look ahead up to 30pt Y-distance for size/type line
    for i in range(current_index + 1, min(current_index + 20, len(lines))):
        next_line = lines[i]
        next_y = next_line["bbox"][1]

        # Stop if we've gone too far vertically
        if next_y - current_y > MAX_VERTICAL_GAP:
            break

        # Check if this is a size/type line (Calibri-Italic with size keywords)
        if span_matches_predicate(next_line, {"font_exact": config.size_type_font}):
            size_keywords = {
                "Tiny",
                "Small",
                "Medium",
                "Large",
                "Huge",
                "Gargantuan",
            }
            text_lower = next_line["text"]
            if any(keyword in text_lower for keyword in size_keywords):
                return True

    # No size/type line found - might still be valid, but less confident
    return False


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
    return text[0].isupper() and len(text) < MAX_MONSTER_NAME_LENGTH


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
