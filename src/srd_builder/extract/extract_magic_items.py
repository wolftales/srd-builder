#!/usr/bin/env python3
"""PDF magic item extraction for SRD 5.1.

Extracts raw magic item entries from PDF using font analysis and layout detection.
Outputs verbatim text with metadata for downstream parsing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

try:
    from ..constants import EXTRACTOR_VERSION
except ImportError:
    # Running as script
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parents[2]))
    from srd_builder.constants import EXTRACTOR_VERSION

# Magic Items section pages
MAGIC_ITEMS_START_PAGE = 206  # "Magic Items" chapter start (first actual item)
MAGIC_ITEMS_END_PAGE = 253  # End of magic items section (before Appendix MM-A)

# Font patterns (similar to spells)
ITEM_NAME_FONT = "GillSans-SemiBold"
ITEM_NAME_SIZE = 12.0
ITEM_METADATA_FONT = "Cambria-Italic"  # For rarity/attunement
FIELD_LABEL_FONT = "Cambria-Bold"
BODY_TEXT_FONT = "Cambria"

# Extraction constants
FONT_SIZE_TOLERANCE = 0.5
MIN_DESCRIPTION_LENGTH = 20
MIN_CLI_ARGS = 2


@dataclass
class ExtractionConfig:
    """Configuration for PDF magic item extraction."""

    page_start: int = MAGIC_ITEMS_START_PAGE
    page_end: int = MAGIC_ITEMS_END_PAGE

    # Font identification
    item_name_font: str = ITEM_NAME_FONT
    item_name_size: float = ITEM_NAME_SIZE
    item_metadata_font: str = ITEM_METADATA_FONT

    # Quality thresholds
    expected_item_count_min: int = 150  # Conservative estimate


def extract_magic_items(pdf_path: Path) -> dict[str, Any]:
    """Extract magic items from SRD PDF.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - items: list of raw magic item dicts
            - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    config = ExtractionConfig()

    # Calculate PDF hash for provenance
    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    doc = fitz.open(pdf_path)
    items: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        # Extract items from each page
        for page_num in range(config.page_start - 1, config.page_end):
            page_items = _extract_page_items(doc[page_num], page_num + 1, config)
            items.extend(page_items)

        # Merge multi-page items
        items = _merge_multipage_items(items)

        if len(items) < config.expected_item_count_min:
            warnings.append(
                f"Only extracted {len(items)} items, expected at least {config.expected_item_count_min}"
            )

    finally:
        doc.close()

    return {
        "items": items,
        "_meta": {
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "pages_processed": config.page_end - config.page_start + 1,
            "item_count": len(items),
            "total_warnings": len(warnings),
            "extraction_warnings": warnings,
        },
    }


def _extract_page_items(
    page: fitz.Page, page_num: int, config: ExtractionConfig
) -> list[dict[str, Any]]:
    """Extract magic items from a single PDF page.

    Args:
        page: PyMuPDF page object
        page_num: 1-based page number
        config: Extraction configuration

    Returns:
        List of raw item dictionaries with metadata
    """
    blocks = page.get_text("dict")["blocks"]
    items: list[dict[str, Any]] = []
    current_item: dict[str, Any] | None = None
    pending_name_line: str | None = None  # For multi-line names

    for block in blocks:
        if block.get("type") != 0:  # Skip non-text blocks
            continue

        for line in block.get("lines", []):
            # Collect all spans in this line
            line_spans = []
            for span in line.get("spans", []):
                font = span.get("font", "")
                size = round(span.get("size", 0), 1)
                text = span.get("text", "")
                is_bold = "Bold" in font or "SemiBold" in font
                is_italic = "Italic" in font

                line_spans.append(
                    {
                        "text": text,
                        "font": font,
                        "size": size,
                        "is_bold": is_bold,
                        "is_italic": is_italic,
                    }
                )

            # Process line for item detection
            line_text = "".join(s["text"] for s in line_spans).strip()
            if not line_text:
                continue

            # Detect item name (GillSans-SemiBold 12pt)
            first_span = line_spans[0] if line_spans else None
            is_header = (
                first_span
                and config.item_name_font in first_span["font"]
                and abs(first_span["size"] - config.item_name_size) < FONT_SIZE_TOLERANCE
            )

            if is_header:
                # Check if this continues a pending name
                if pending_name_line:
                    # Merge with pending name
                    pending_name_line = pending_name_line.strip() + " " + line_text
                else:
                    # New header line
                    pending_name_line = line_text

                # Check if this header line looks incomplete (doesn't end with punctuation)
                # If it ends with "and", "or", "of", etc., expect continuation
                last_word = line_text.split()[-1].lower() if line_text.split() else ""
                if last_word in {"and", "or", "of", "the", "a", "an"}:
                    # Expect continuation on next line
                    continue

            # Not a header continuation - finalize pending item name
            elif pending_name_line:
                # Save previous item if exists
                if current_item:
                    items.append(current_item)

                # Start new item with completed name
                current_item = {
                    "name": pending_name_line,
                    "page": page_num,
                    "metadata_blocks": [],
                    "description_blocks": [],
                }
                pending_name_line = None

            # Add spans to current item (non-header lines)
            if current_item and not is_header:
                # Check if this is metadata (italic) or description (regular)
                is_metadata_line = any(
                    s["is_italic"] and config.item_metadata_font in s["font"] for s in line_spans
                )

                if is_metadata_line:
                    current_item["metadata_blocks"].extend(line_spans)
                else:
                    current_item["description_blocks"].extend(line_spans)

    # Finalize any pending name
    if pending_name_line:
        if current_item:
            items.append(current_item)
        current_item = {
            "name": pending_name_line,
            "page": page_num,
            "metadata_blocks": [],
            "description_blocks": [],
        }

    # Add last item
    if current_item:
        items.append(current_item)

    return items


def _merge_multipage_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge items that span multiple pages.

    Items are merged if they appear incomplete (no metadata or very short description).

    Args:
        items: List of raw item dictionaries

    Returns:
        List of merged items
    """
    if not items:
        return []

    merged: list[dict[str, Any]] = []
    current = items[0]

    for next_item in items[1:]:
        # Check if current item looks incomplete
        current_desc_len = sum(
            len(s.get("text", "")) for s in current.get("description_blocks", [])
        )
        has_metadata = len(current.get("metadata_blocks", [])) > 0

        # If current is very short and has no metadata, it might be incomplete
        if current_desc_len < MIN_DESCRIPTION_LENGTH and not has_metadata:
            # Merge into next_item (current was probably a continuation)
            next_item["description_blocks"] = current.get("description_blocks", []) + next_item.get(
                "description_blocks", []
            )
        else:
            # Current looks complete, save it
            merged.append(current)

        current = next_item

    # Add last item
    merged.append(current)

    return merged


def main():
    """CLI entry point for testing extraction."""
    import sys

    if len(sys.argv) < MIN_CLI_ARGS:
        print(f"Usage: {sys.argv[0]} <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    result = extract_magic_items(pdf_path)

    print(f"Extracted {result['_meta']['item_count']} magic items")
    print(f"Warnings: {result['_meta']['total_warnings']}")

    # Show first few items
    for item in result["items"][:5]:
        print(f"\n{item['name']} (page {item['page']})")
        metadata_text = "".join(s.get("text", "") for s in item.get("metadata_blocks", []))
        if metadata_text:
            print(f"  Metadata: {metadata_text[:100]}")
        desc_text = "".join(s.get("text", "") for s in item.get("description_blocks", []))
        print(f"  Description: {desc_text[:200]}...")


if __name__ == "__main__":
    main()
