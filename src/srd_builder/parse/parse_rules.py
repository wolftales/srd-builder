#!/usr/bin/env python3
"""Rules parsing for SRD 5.1.

Structures raw text blocks into hierarchical rule outlines.
Returns unnormalized dicts for downstream postprocessing.

This module implements the PARSE stage:
- Builds outline tree from font tiers and header stack
- Detects paragraphs vs headers using font metadata
- Attaches page provenance
- Returns structured dicts WITHOUT ids/simple_names (added in postprocess)
"""

from __future__ import annotations

from typing import Any

# Font pattern constants (discovered from PDF analysis of combat/spellcasting chapters)
CHAPTER_HEADER_SIZE = 25.0  # Large headers like "Using Ability Scores" (25.9pt)
SECTION_HEADER_SIZE = 17.0  # Section headers (18.0pt)
SUBSECTION_HEADER_SIZE = 13.0  # Subsection headers (13.9pt)
BODY_TEXT_SIZE = 9.8  # Normal paragraph text
FONT_SIZE_TOLERANCE = 1.5  # Tolerance for font size matching


def parse_rules(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse raw rules text blocks into structured rule entities.

    PARSE STAGE: Structure extraction only (NO normalization, NO IDs).

    Takes text blocks with font metadata and builds hierarchical outline.
    Returns unnormalized dicts - postprocess stage adds id/simple_name.

    Args:
        raw_data: Dictionary with text_blocks and sections from extract_rules()

    Returns:
        List of rule dicts WITHOUT id/simple_name (structure only):
            - name: str (display name from header text)
            - category: str (chapter name)
            - subcategory: str | None (section name)
            - text: list[str] (paragraphs)
            - page: int (first page)
            - source: str (always "SRD 5.1")
    """
    text_blocks = raw_data.get("text_blocks", [])
    sections = raw_data.get("sections", [])

    if not text_blocks:
        return []

    # Build section name mapping for category assignment
    section_map = {s["name"]: s["description"] for s in sections}

    # Identify headers and group paragraphs
    headers = _identify_headers(text_blocks)
    grouped = _group_paragraphs_under_headers(text_blocks, headers)

    # Build flat rule list with hierarchy metadata
    rules = _build_rule_list(grouped, section_map)

    return rules


def _identify_headers(text_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Identify header blocks using font metadata.

    Args:
        text_blocks: Text blocks with font_name, font_size, is_bold

    Returns:
        List of header blocks with tier assignments and list index
    """
    headers = []
    current_header = None

    for idx, block in enumerate(text_blocks):
        font_size = block.get("font_size", 0)
        is_bold = block.get("is_bold", False)
        text = block.get("text", "").strip()
        block_idx = block.get("block_idx", 0)

        # Skip empty or very short blocks
        if not text or len(text) < 3:
            continue

        # Skip page numbers and system references
        if text.isdigit() or "System" in text or "Reference" in text:
            continue

        # Classify header tier by font size
        tier = None
        if font_size >= CHAPTER_HEADER_SIZE - FONT_SIZE_TOLERANCE:
            tier = "chapter"
        elif font_size >= SECTION_HEADER_SIZE - FONT_SIZE_TOLERANCE and is_bold:
            tier = "section"
        elif font_size >= SUBSECTION_HEADER_SIZE - FONT_SIZE_TOLERANCE and is_bold:
            tier = "subsection"

        if tier:
            # Check if this continues the previous header (same block, sequential line)
            if (
                current_header
                and current_header["block_idx"] == block_idx
                and current_header["tier"] == tier
            ):
                # Append to existing header text
                current_header["text"] += " " + text
            else:
                # Save previous header if exists
                if current_header:
                    headers.append(current_header)

                # Start new header (store list index for grouping)
                current_header = {
                    "text": text,
                    "tier": tier,
                    "page": block.get("page", 0),
                    "block_idx": block_idx,
                    "list_idx": idx,  # Add list index for grouping
                }

    # Don't forget the last header
    if current_header:
        headers.append(current_header)

    return headers


def _group_paragraphs_under_headers(
    text_blocks: list[dict[str, Any]], headers: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Group paragraph blocks under their parent headers.

    Args:
        text_blocks: All text blocks
        headers: Identified header blocks with list_idx

    Returns:
        Grouped structures with headers and paragraphs
    """
    if not headers:
        return []

    # Create header lookup by list index
    header_indices = {h["list_idx"]: h for h in headers}

    grouped = []
    current_header = None
    current_paragraphs: list[str] = []

    for idx, block in enumerate(text_blocks):
        text = block.get("text", "").strip()
        font_size = block.get("font_size", 0)

        # Check if this block is a header
        if idx in header_indices:
            # Save previous header with its paragraphs
            if current_header and current_paragraphs:
                grouped.append(
                    {
                        "name": current_header["text"],
                        "tier": current_header["tier"],
                        "page": current_header["page"],
                        "text": current_paragraphs,
                    }
                )

            # Start new header
            current_header = header_indices[idx]
            current_paragraphs = []
        elif current_header and text:
            # Skip page numbers, system references, bullets
            if text.isdigit() or "System" in text or text == "•":
                continue

            # Only collect body text (not headers)
            if font_size < SECTION_HEADER_SIZE - FONT_SIZE_TOLERANCE:
                # Clean up text (remove extra \r characters from PDF extraction)
                cleaned = text.replace(" \r  ", " ").replace("\r", " ").strip()
                if cleaned:
                    current_paragraphs.append(cleaned)

    # Don't forget the last header
    if current_header and current_paragraphs:
        grouped.append(
            {
                "name": current_header["text"],
                "tier": current_header["tier"],
                "page": current_header["page"],
                "text": current_paragraphs,
            }
        )

    return grouped


def _build_outline_tree(grouped_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build hierarchical outline from grouped header/paragraph blocks.

    DEPRECATED: Merged into _build_rule_list() for simpler implementation.

    Args:
        grouped_blocks: Headers with associated paragraphs

    Returns:
        Flattened list of rule entities (hierarchy via parent_id)
    """
    # This function is kept for API compatibility but is no longer used
    # _build_rule_list() handles the outline building directly
    return []


def _build_rule_list(
    grouped: list[dict[str, Any]], section_map: dict[str, str]
) -> list[dict[str, Any]]:
    """Build flat list of rules with hierarchy metadata.

    Args:
        grouped: Grouped headers with paragraphs
        section_map: Mapping of section names to descriptions

    Returns:
        List of rule dicts with category, subcategory, page, text
    """
    rules = []
    current_chapter = None
    current_section = None

    for entry in grouped:
        tier = entry["tier"]
        name = entry["name"]
        page = entry["page"]
        text = entry["text"]

        if tier == "chapter":
            # Chapter becomes category
            current_chapter = name
            current_section = None
        elif tier == "section":
            # Section becomes subcategory
            current_section = name
        elif tier == "subsection":
            # Subsection is a separate rule
            pass

        # Only create rule entries for sections and subsections with content
        if tier in ("section", "subsection") and text:
            rule: dict[str, Any] = {
                "name": name,
                "category": current_chapter or "General Rules",
                "page": page,
                "source": "SRD 5.1",
                "text": text,
            }

            # Add subcategory for subsections
            if tier == "subsection" and current_section:
                rule["subcategory"] = current_section

            rules.append(rule)

    return rules


def main() -> int:
    """Command-line entry point for testing."""
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m srd_builder.parse.parse_rules <rules_raw.json>")
        return 1

    import pathlib

    raw_path = pathlib.Path(sys.argv[1])
    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    parsed = parse_rules(raw_data)

    # Write to stdout
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
