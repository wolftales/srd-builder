#!/usr/bin/env python3
"""Rules parsing for SRD 5.1.

Structures raw text blocks into hierarchical rule outlines.
Returns unnormalized dicts for downstream postprocessing.

This module implements the PARSE stage:
- Builds outline tree from font tiers and header stack
- Detects paragraphs vs headers
- Attaches page provenance
- Returns structured dicts WITHOUT ids/simple_names (added in postprocess)
"""

from __future__ import annotations

from typing import Any


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
            - parent_id: None (will be added in postprocess if needed)
            - text: list[str] (paragraphs)
            - page: int (first page)
            - source: str (always "SRD 5.1")
            - tags: list[str] (lightweight tags)
            - related_conditions: list[str] (will be populated in postprocess)
            - related_spells: list[str]
            - related_features: list[str]
            - related_tables: list[str]
    """
    text_blocks = raw_data.get("text_blocks", [])
    # sections = raw_data.get("sections", [])  # TODO: Use in real implementation

    if not text_blocks:
        return []

    # PHASE 1 STUB: Return minimal structure for initial testing
    # TODO: Implement actual outline parsing using font metadata
    #
    # Real implementation will:
    # 1. Identify headers using font_size thresholds and font_name patterns
    # 2. Build header hierarchy (chapter → section → subsection)
    # 3. Group paragraphs under headers
    # 4. Extract category/subcategory from header stack
    # 5. Detect lightweight tags from keywords
    # 6. Return structured dicts WITHOUT id/simple_name

    # Stub: Return empty list (prevents build errors)
    # Real implementation coming after extraction is tested
    return []


def _identify_headers(text_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Identify header blocks using font metadata.

    Args:
        text_blocks: Text blocks with font_name, font_size, is_bold

    Returns:
        List of header blocks with tier assignments
    """
    # TODO: Implement header detection
    # - Larger font_size = higher tier (chapter > section > subsection)
    # - Bold + specific font patterns indicate headers
    # - Group by relative font sizes (not absolute)
    return []


def _group_paragraphs_under_headers(
    text_blocks: list[dict[str, Any]], headers: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Group paragraph blocks under their parent headers.

    Args:
        text_blocks: All text blocks
        headers: Identified header blocks

    Returns:
        Grouped structures with headers and paragraphs
    """
    # TODO: Implement paragraph grouping
    # - Paragraphs between headers belong to previous header
    # - Track page boundaries
    # - Combine multi-line paragraphs
    return []


def _build_outline_tree(grouped_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build hierarchical outline from grouped header/paragraph blocks.

    Args:
        grouped_blocks: Headers with associated paragraphs

    Returns:
        Flattened list of rule entities (hierarchy via parent_id)
    """
    # TODO: Implement outline tree building
    # - Assign category (chapter name)
    # - Assign subcategory (section name)
    # - Optional parent_id for nesting
    # - Flatten tree into list
    return []


def main():
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
