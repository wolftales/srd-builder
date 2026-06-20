"""Extract class features and lineage traits from SRD 5.1 PDF.

This module extracts feature descriptions from:
- Class sections (pages 8-55): Class features like Rage, Spellcasting, etc.
- Lineage sections (pages 3-7): Racial traits like Darkvision, Lucky, etc.

Feature Pattern:
- Class feature headers: 13.9pt GillSans-SemiBold (e.g., "Rage")
- Lineage trait headers: 9.8pt Cambria-BoldItalic ending with "." (e.g., "Darkvision.")

This is the first binding of the engine's `font_fingerprint_walk` pattern type
(prototype). See docs/BACKLOG.md "Design-pass finding" for the design context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from srd_builder.extract.patterns import extract_records_by_config

# Shared engine config: detect either class-feature OR lineage-trait headers
# in a single walk. The two fingerprints are OR'd; whichever matches first
# wins for that span.
DATASET_CONFIG: dict[str, Any] = {
    "pattern_type": "font_fingerprint_walk",
    "header_fingerprints": [
        # Class feature: 13.9pt GillSans-SemiBold, bold, min length 2
        # (len>=2 keeps short feature names like the monk's "Ki").
        {
            "font_substring": "GillSans",
            "size_min": 13.5,
            "size_max": 14.5,
            "require_bold": True,
            "min_text_len": 2,
        },
        # Lineage trait: 9.8pt Cambria-BoldItalic, must end with "."
        # (the period is the structural signal; strip it from the record name).
        {
            "font_substring": "Cambria",
            "size_min": 9.5,
            "size_max": 10.5,
            "require_bold": True,
            "require_italic": True,
            "min_text_len": 4,
            "require_trailing_period": True,
            "strip_trailing_period_from_name": True,
        },
    ],
    "body_grouping": "single_bucket_concat",
    "body_cleanup": "clean_text",
    "filter_structural": True,
}


def extract_features(pdf_path: str | Path, pages: list[int]) -> dict[str, Any]:
    """Extract class features and lineage traits from PDF.

    Args:
        pdf_path: Path to SRD PDF
        pages: List of page numbers to extract from

    Returns:
        Dict with extracted features metadata including raw feature text
    """
    records = extract_records_by_config(str(pdf_path), pages, DATASET_CONFIG)
    return {
        "source_pages": f"{min(pages)}-{max(pages)}",
        "features": records,
        "extraction_warnings": [],
    }


def extract_class_features(pdf_path: str | Path) -> dict[str, Any]:
    """Extract all class features from PDF pages 8-55."""
    return extract_features(pdf_path, list(range(8, 56)))


def extract_lineage_traits(pdf_path: str | Path) -> dict[str, Any]:
    """Extract all lineage traits from PDF pages 3-7."""
    return extract_features(pdf_path, list(range(3, 8)))
