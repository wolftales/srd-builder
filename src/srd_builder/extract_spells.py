#!/usr/bin/env python3
"""PDF spell extraction for SRD 5.1.

Extracts raw spell entries from PDF using font analysis and layout detection.
Outputs verbatim text with metadata for downstream parsing.

Phase: v0.4.0 - Raw extraction only (no field parsing)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import EXTRACTOR_VERSION


@dataclass
class ExtractionConfig:
    """Configuration for PDF spell extraction."""

    # Page range for spells (TBD - need to find spell section in SRD)
    # TODO: Research actual spell page range in SRD_CC_v5.1.pdf
    page_start: int = 100  # Placeholder
    page_end: int = 200  # Placeholder

    # Font size thresholds (TBD - need font analysis like we did for monsters)
    spell_name_font_size: float = 11.0  # Placeholder
    header_font_size_min: float = 12.0  # Placeholder

    # Font patterns (TBD - need to analyze spell formatting)
    spell_name_font: str = "UNKNOWN"  # Placeholder
    spell_level_font: str = "UNKNOWN"  # Placeholder

    # Quality thresholds
    expected_spell_count_min: int = 300  # We expect ~300-400 spells


@dataclass
class RawSpell:
    """Raw spell extraction with metadata."""

    name: str
    level_and_school: str  # e.g., "3rd-level evocation"
    header_text: str  # Casting time, range, etc.
    description_text: str  # Full spell description
    pages: list[int]  # Page numbers where this spell appears


def extract_spells(pdf_path: Path) -> dict[str, Any]:
    """Extract spells from SRD PDF.

    This is a STUB implementation that returns empty data.
    Full extraction will be implemented in future commits.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - spells: list of raw spell dicts
            - _meta: extraction metadata
    """
    config = ExtractionConfig()

    # Calculate PDF hash for provenance
    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # TODO: Implement actual spell extraction
    # For now, return empty structure
    spells: list[dict[str, Any]] = []

    return {
        "spells": spells,
        "_meta": {
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "pages_processed": config.page_end - config.page_start + 1,
            "spell_count": len(spells),
            "total_warnings": 0,
            "extraction_warnings": [],
        },
    }


def main() -> None:  # pragma: no cover
    """CLI entry point for spell extraction."""
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    result = extract_spells(pdf_path)

    print(f"Extracted {result['_meta']['spell_count']} spells")
    print(f"Warnings: {result['_meta']['total_warnings']}")


if __name__ == "__main__":  # pragma: no cover
    main()
