#!/usr/bin/env python3
"""PDF rules extraction for SRD 5.1.

Extracts core mechanics and rules text from designated chapters.
Outputs verbatim text with font metadata for downstream parsing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..constants import EXTRACTOR_VERSION
from ..utils.page_index import PAGE_INDEX

# Rules chapters from PAGE_INDEX (Phase 1 scope - v0.17.0)
RULES_SECTIONS = [
    "using_ability_scores",  # Pages 76-83: Ability checks, saves, skills
    "time",  # Page 84: Time in D&D
    "movement",  # Pages 84-85: Movement rules
    "environment",  # Pages 86-87: Environmental hazards
    "between_adventures",  # Pages 88-89: Resting, lifestyle
    "combat",  # Pages 90-99: Combat rules
    "spellcasting",  # Pages 100-104: Spellcasting rules
]


@dataclass
class ExtractionConfig:
    """Configuration for PDF rules extraction."""

    sections: list[str] = None  # type: ignore[assignment]  # __post_init__ ensures non-None

    def __post_init__(self) -> None:
        """Initialize default sections if none provided."""
        if self.sections is None:
            self.sections = RULES_SECTIONS.copy()


def extract_rules(pdf_path: Path) -> dict[str, Any]:
    """Extract rules text from SRD PDF core mechanics chapters.

    Extracts text blocks with font metadata from designated rules chapters
    for downstream parsing into structured rule entities.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - text_blocks: list of raw text blocks with font metadata
            - sections: list of processed sections
            - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    config = ExtractionConfig()

    # Calculate PDF hash for provenance
    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Import here to avoid circular dependency
    import fitz

    doc = fitz.open(pdf_path)
    text_blocks: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        # Extract text from each rules section
        for section_name in config.sections:
            section_info = PAGE_INDEX.get(section_name)
            if not section_info:
                warnings.append(f"Section '{section_name}' not found in PAGE_INDEX")
                continue

            page_start = section_info["pages"]["start"]
            page_end = section_info["pages"]["end"]

            # Extract text blocks from this section
            section_blocks = []
            for page_num in range(page_start - 1, page_end):  # fitz uses 0-indexed pages
                page = doc[page_num]
                page_blocks = _extract_page_text_blocks(page, page_num + 1)
                section_blocks.extend(page_blocks)
                text_blocks.extend(page_blocks)

            sections.append(
                {
                    "name": section_name,
                    "description": section_info["description"],
                    "pages": {"start": page_start, "end": page_end},
                    "block_count": len(section_blocks),
                }
            )

    finally:
        doc.close()

    # Calculate total pages processed
    total_pages = sum(
        PAGE_INDEX[s]["pages"]["end"] - PAGE_INDEX[s]["pages"]["start"] + 1
        for s in config.sections
        if s in PAGE_INDEX
    )

    return {
        "text_blocks": text_blocks,
        "sections": sections,
        "_meta": {
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "sections_processed": len(sections),
            "pages_processed": total_pages,
            "total_blocks": len(text_blocks),
            "total_warnings": len(warnings),
            "warnings": warnings,
        },
    }


def _extract_page_text_blocks(page: Any, page_num: int) -> list[dict[str, Any]]:
    """Extract text blocks from a single page with font metadata.

    Args:
        page: PyMuPDF page object
        page_num: Page number (1-indexed)

    Returns:
        List of text blocks with font metadata
    """
    blocks: list[dict[str, Any]] = []

    # Extract text with font information
    # dict["blocks"] contains blocks, each block contains lines
    page_dict = page.get_text("dict", flags=0)

    for block_idx, block in enumerate(page_dict.get("blocks", [])):
        # Skip image blocks
        if block.get("type") != 0:  # 0 = text block
            continue

        # Extract lines from this block
        for line_idx, line in enumerate(block.get("lines", [])):
            # Extract spans (font runs) from this line
            for span_idx, span in enumerate(line.get("spans", [])):
                text = span.get("text", "").strip()
                if not text:
                    continue

                # Extract font metadata
                font_name = span.get("font", "Unknown")
                font_size = span.get("size", 0.0)
                font_flags = span.get("flags", 0)  # Bit flags for bold/italic/etc

                # bbox: (x0, y0, x1, y1) - bounding box coordinates
                bbox = span.get("bbox", (0, 0, 0, 0))

                blocks.append(
                    {
                        "text": text,
                        "page": page_num,
                        "font_name": font_name,
                        "font_size": round(font_size, 1),
                        "font_flags": font_flags,
                        "is_bold": bool(font_flags & 16),  # Flag 16 = bold
                        "is_italic": bool(font_flags & 2),  # Flag 2 = italic
                        "bbox": {
                            "x0": round(bbox[0], 1),
                            "y0": round(bbox[1], 1),
                            "x1": round(bbox[2], 1),
                            "y1": round(bbox[3], 1),
                        },
                        "block_idx": block_idx,
                        "line_idx": line_idx,
                        "span_idx": span_idx,
                    }
                )

    return blocks


def main() -> int:
    """Command-line entry point for testing."""
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m srd_builder.extract.extract_rules <pdf_path>")
        print("\nExtracts core mechanics rules from SRD PDF chapters:")
        for section in RULES_SECTIONS:
            info = PAGE_INDEX[section]
            pages = f"pages {info['pages']['start']}-{info['pages']['end']}"
            print(f"  - {section}: {pages}")
        return 1

    pdf_path = Path(sys.argv[1])
    result = extract_rules(pdf_path)

    # Write to stdout
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
