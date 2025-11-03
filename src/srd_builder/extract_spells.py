#!/usr/bin/env python3
"""PDF spell extraction for SRD 5.1.

Extracts raw spell entries from PDF using font analysis and layout detection.
Outputs verbatim text with metadata for downstream parsing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

from .constants import EXTRACTOR_VERSION

# Spell section pages (descriptions, not spell lists)
SPELL_START_PAGE = 114  # First page of spell descriptions
SPELL_END_PAGE = 194  # Last page of spell descriptions

# Font patterns identified from PDF analysis
SPELL_NAME_FONT = "GillSans-SemiBold"
SPELL_NAME_SIZE = 12.0
SPELL_LEVEL_FONT = "Cambria-Italic"
FIELD_LABEL_FONT = "Cambria-Bold"
HIGHER_LEVELS_FONT = "Cambria-BoldItalic"

# Extraction constants
FONT_SIZE_TOLERANCE = 0.5  # Tolerance for font size matching (points)
MIN_DESCRIPTION_LENGTH = 50  # Minimum description length to consider complete
MIN_HEADER_LENGTH = 30  # Minimum header length to consider complete
MIN_CLI_ARGS = 2  # Minimum command-line arguments required


@dataclass
class ExtractionConfig:
    """Configuration for PDF spell extraction."""

    page_start: int = SPELL_START_PAGE
    page_end: int = SPELL_END_PAGE

    # Font identification
    spell_name_font: str = SPELL_NAME_FONT
    spell_name_size: float = SPELL_NAME_SIZE
    spell_level_font: str = SPELL_LEVEL_FONT
    field_label_font: str = FIELD_LABEL_FONT

    # Quality thresholds
    expected_spell_count_min: int = 300


def extract_spells(pdf_path: Path) -> dict[str, Any]:
    """Extract spells from SRD PDF.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - spells: list of raw spell dicts
            - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    config = ExtractionConfig()

    # Calculate PDF hash for provenance
    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    doc = fitz.open(pdf_path)
    spells: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        # Extract spells from each page
        for page_num in range(config.page_start - 1, config.page_end):
            page_spells = _extract_page_spells(doc[page_num], page_num + 1, config)
            spells.extend(page_spells)

        # Merge multi-page spells
        spells = _merge_multipage_spells(spells)

        if len(spells) < config.expected_spell_count_min:
            warnings.append(
                f"Only extracted {len(spells)} spells, expected at least {config.expected_spell_count_min}"
            )

    finally:
        doc.close()

    return {
        "spells": spells,
        "_meta": {
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "pages_processed": config.page_end - config.page_start + 1,
            "spell_count": len(spells),
            "total_warnings": len(warnings),
            "extraction_warnings": warnings,
        },
    }


def _extract_page_spells(  # noqa: C901
    page: fitz.Page, page_num: int, config: ExtractionConfig
) -> list[dict[str, Any]]:
    """Extract spell entries from a single page.

    Args:
        page: PyMuPDF page object
        page_num: 1-based page number
        config: Extraction configuration

    Returns:
        List of spell dictionaries
    """
    # Get structured text with font metadata
    textpage = page.get_textpage(flags=fitz.TEXTFLAGS_TEXT)
    page_dict = page.get_text("dict", textpage=textpage)

    spells: list[dict[str, Any]] = []
    current_spell: dict[str, Any] | None = None
    current_section = ""  # "header" or "description"

    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue

                font = span.get("font", "")
                size = span.get("size", 0)

                # Detect spell name (12pt GillSans-SemiBold)
                if (
                    config.spell_name_font in font
                    and abs(size - config.spell_name_size) < FONT_SIZE_TOLERANCE
                ):
                    # Save previous spell
                    if current_spell:
                        spells.append(current_spell)

                    # Start new spell
                    current_spell = {
                        "name": text,
                        "level_and_school": "",
                        "header_text": "",
                        "description_text": "",
                        "page": page_num,
                    }
                    current_section = "header"

                # Detect spell level/school (italic after name)
                elif (
                    current_spell
                    and not current_spell["level_and_school"]
                    and config.spell_level_font in font
                ):
                    current_spell["level_and_school"] = text

                # Detect "At Higher Levels" section
                elif HIGHER_LEVELS_FONT in font:
                    if current_spell:
                        current_spell["description_text"] += f" {text}"

                # Field labels (bold) - part of header
                elif config.field_label_font in font:
                    if not current_spell:
                        # Start a continuation spell (no name)
                        current_spell = {
                            "name": "",
                            "level_and_school": "",
                            "header_text": "",
                            "description_text": "",
                            "page": page_num,
                        }
                        current_section = "header"

                    if current_section == "header":
                        current_spell["header_text"] += f" {text}"
                    else:
                        current_spell["description_text"] += f" {text}"

                # Regular text - header until we see description markers
                else:
                    if not current_spell:
                        # Start a continuation spell (no name)
                        current_spell = {
                            "name": "",
                            "level_and_school": "",
                            "header_text": "",
                            "description_text": "",
                            "page": page_num,
                        }
                        current_section = "header"

                    # Header includes: Casting Time, Range, Components, Duration
                    if current_section == "header":
                        current_spell["header_text"] += f" {text}"
                        # Switch to description after Duration
                        if "Duration:" in current_spell["header_text"]:
                            current_section = "description"
                    else:
                        current_spell["description_text"] += f" {text}"

    # Don't forget last spell on page
    if current_spell:
        spells.append(current_spell)

    return spells


def _merge_multipage_spells(spells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge spells that span multiple pages.

    Detects incomplete spells (missing description or short text) and merges
    with following content until a complete spell is formed.

    Args:
        spells: List of spell dictionaries from all pages

    Returns:
        List with multi-page spells merged
    """
    if not spells:
        return []

    merged: list[dict[str, Any]] = []
    i = 0

    while i < len(spells):
        current = spells[i].copy()
        current["pages"] = [current["page"]]

        # If current spell has no name, it's a continuation - merge into previous
        if not current.get("name", "").strip() and merged:
            # Merge with previous spell
            prev = merged[-1]
            prev["header_text"] += " " + current.get("header_text", "")
            prev["description_text"] += " " + current.get("description_text", "")
            if current["page"] not in prev["pages"]:
                prev["pages"].append(current["page"])
            i += 1
            continue

        # Check if spell looks incomplete (very short or no description)
        desc_len = len(current.get("description_text", "").strip())
        header_len = len(current.get("header_text", "").strip())

        # If spell has name but minimal content, AND there's a following nameless spell, merge forward
        if i + 1 < len(spells):
            next_spell = spells[i + 1]
            next_has_name = bool(next_spell.get("name", "").strip())

            # Merge if: current incomplete AND next has no name (continuation)
            if (
                desc_len < MIN_DESCRIPTION_LENGTH or header_len < MIN_HEADER_LENGTH
            ) and not next_has_name:
                # Merge with next spell's content
                current["header_text"] += " " + next_spell.get("header_text", "")
                current["description_text"] += " " + next_spell.get("description_text", "")
                if next_spell["page"] not in current["pages"]:
                    current["pages"].append(next_spell["page"])
                i += 1  # Skip the merged spell

        # Only add spells with names (filter out orphaned continuations)
        if current.get("name", "").strip():
            merged.append(current)
        i += 1

    return merged


def main() -> None:  # pragma: no cover
    """CLI entry point for spell extraction."""
    import sys

    if len(sys.argv) != MIN_CLI_ARGS:
        print(f"Usage: {sys.argv[0]} <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    result = extract_spells(pdf_path)

    print(f"Extracted {result['_meta']['spell_count']} spells")
    print(f"Warnings: {result['_meta']['total_warnings']}")

    # Show first few spells as samples
    for spell in result["spells"][:3]:
        print(f"\n{spell['name']}")
        print(f"  {spell['level_and_school']}")
        print(f"  Header: {spell['header_text'][:80]}...")
        print(f"  Desc: {spell['description_text'][:80]}...")


if __name__ == "__main__":  # pragma: no cover
    main()
