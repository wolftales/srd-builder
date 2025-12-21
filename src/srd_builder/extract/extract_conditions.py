#!/usr/bin/env python3
"""PDF condition extraction for SRD 5.1.

Extracts raw condition entries from Appendix PH-A (pages 358-359).
Outputs verbatim text with metadata for downstream parsing.

This module demonstrates the reusable prose extraction pattern - see
prose_extraction.py for the framework components.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.constants import EXTRACTOR_VERSION
from .prose_extraction import ProseExtractor

# Condition pages from Appendix PH-A
CONDITION_START_PAGE = 358
CONDITION_END_PAGE = 359

# Known condition names from SRD 5.1
CONDITION_NAMES = [
    "Blinded",
    "Charmed",
    "Deafened",
    "Exhaustion",
    "Frightened",
    "Grappled",
    "Incapacitated",
    "Invisible",
    "Paralyzed",
    "Petrified",
    "Poisoned",
    "Prone",
    "Restrained",
    "Stunned",
    "Unconscious",
]


@dataclass
class ExtractionConfig:
    """Configuration for PDF condition extraction."""

    page_start: int = CONDITION_START_PAGE
    page_end: int = CONDITION_END_PAGE
    expected_condition_count: int = 14  # Standard conditions (not counting Exhaustion levels)


def extract_conditions(pdf_path: Path) -> dict[str, Any]:
    """Extract conditions from SRD PDF Appendix PH-A.

    Uses the reusable ProseExtractor framework for standardized extraction.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - conditions: list of raw condition dicts
            - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    config = ExtractionConfig()

    # Calculate PDF hash for provenance
    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Use ProseExtractor framework
    extractor = ProseExtractor(
        section_name="condition",
        known_headers=CONDITION_NAMES,
        start_page=config.page_start,
        end_page=config.page_end,
    )

    # Extract sections from PDF
    sections, warnings = extractor.extract_from_pdf(pdf_path)

    # Convert to condition format
    conditions = [
        {
            "name": section["name"],
            "raw_text": section["raw_text"],
            "pages": [config.page_start, config.page_end],
        }
        for section in sections
    ]

    if len(conditions) < config.expected_condition_count:
        warnings.append(
            f"Only extracted {len(conditions)} conditions, expected {config.expected_condition_count}"
        )

    return {
        "conditions": conditions,
        "_meta": {
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "pages_processed": config.page_end - config.page_start + 1,
            "condition_count": len(conditions),
            "total_warnings": len(warnings),
            "warnings": warnings,
        },
    }


# Removed: _extract_conditions_from_text()
# Now using ProseExtractor.extract_from_pdf() from prose_extraction.py
# This reduces duplication and makes the pattern reusable


def main():
    """Command-line entry point for testing."""
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m srd_builder.extract_conditions <pdf_path>")
        return 1

    pdf_path = Path(sys.argv[1])
    result = extract_conditions(pdf_path)

    # Write to stdout
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
