"""Extract class features and lineage traits from SRD 5.1 PDF.

This module extracts feature descriptions from:
- Class sections (pages 8-55): Class features like Rage, Spellcasting, etc.
- Lineage sections (pages 3-7): Racial traits like Darkvision, Lucky, etc.

Feature Pattern:
- Feature headers: 13.9pt GillSans-SemiBold (e.g., "Rage", "Darkvision")
- Feature text: Regular text until next header or section break
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from .prose_extraction import clean_pdf_text


def extract_features(pdf_path: str | Path, pages: list[int]) -> dict[str, Any]:
    """Extract class features and lineage traits from PDF.

    Args:
        pdf_path: Path to SRD PDF
        pages: List of page numbers to extract from

    Returns:
        Dict with extracted features metadata including raw feature text
    """
    pdf_path = Path(pdf_path)
    pdf = fitz.open(pdf_path)

    all_features = []
    warnings = []

    for page_num in pages:
        page = pdf[page_num - 1]  # PyMuPDF uses 0-indexed
        features = _extract_features_from_page(page, page_num)
        all_features.extend(features)

    pdf.close()

    return {
        "source": "SRD 5.1",
        "source_pages": f"{min(pages)}-{max(pages)}",
        "features": all_features,
        "extraction_warnings": warnings,
    }


def _extract_features_from_page(page: fitz.Page, page_num: int) -> list[dict[str, Any]]:
    """Extract features from a single PDF page.

    Looks for feature headers in two formats:
    - Class features: 13.9pt GillSans-SemiBold (Rage, Spellcasting)
    - Lineage traits: 9.8pt Cambria-BoldItalic (Darkvision., Stonecunning.)

    Args:
        page: PyMuPDF page object
        page_num: Page number for metadata

    Returns:
        List of feature dicts with name, text, page
    """
    blocks = page.get_text("dict")["blocks"]
    features = []
    current_feature = None

    for block in blocks:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            # Check each span for feature headers
            for span in line["spans"]:
                text = span["text"].strip()
                size = span.get("size", 0)
                font = span.get("font", "")
                flags = span.get("flags", 0)
                is_bold = bool(flags & 2**4)
                is_italic = bool(flags & 2**1)

                # Class feature header: 13.9pt GillSans-SemiBold
                is_class_feature = (
                    is_bold and "GillSans" in font and 13.5 <= size <= 14.5 and len(text) > 2
                )

                # Lineage trait header: 9.8pt Cambria-BoldItalic ending with "."
                is_trait = (
                    is_bold
                    and is_italic
                    and "Cambria" in font
                    and 9.5 <= size <= 10.5
                    and text.endswith(".")
                    and len(text) > 3
                )

                if is_class_feature or is_trait:
                    # Save previous feature if exists
                    if current_feature:
                        features.append(current_feature)

                    # Start new feature (remove trailing period for traits)
                    feature_name = text.rstrip(".")
                    current_feature = {
                        "name": feature_name,
                        "text": "",
                        "page": page_num,
                    }

                # Accumulate description text for current feature
                elif current_feature and text:
                    # Skip table headers and other structural elements
                    if not _is_structural_text(text):
                        current_feature["text"] += text + " "

    # Save last feature
    if current_feature:
        features.append(current_feature)

    # Clean up text
    for feature in features:
        feature["text"] = clean_pdf_text(feature["text"].strip())

    return features


def _is_structural_text(text: str) -> bool:
    """Check if text is structural (headers, page numbers, etc.) not content.

    Args:
        text: Text to check

    Returns:
        True if text should be skipped
    """
    structural_patterns = [
        r"^System Reference Document",
        r"^\d+$",  # Page numbers
        r"^The [A-Z][a-z]+ Table",  # Table titles
        r"^Level\s+Proficiency",  # Table headers
        r"^Spell Slots per Spell Level",
    ]

    for pattern in structural_patterns:
        if re.match(pattern, text):
            return True

    return False


def extract_class_features(pdf_path: str | Path) -> dict[str, Any]:
    """Extract all class features from PDF pages 8-55.

    Args:
        pdf_path: Path to SRD PDF

    Returns:
        Dict with class features
    """
    # Pages 8-55 contain all 12 classes
    return extract_features(pdf_path, list(range(8, 56)))


def extract_lineage_traits(pdf_path: str | Path) -> dict[str, Any]:
    """Extract all lineage traits from PDF pages 3-7.

    Args:
        pdf_path: Path to SRD PDF

    Returns:
        Dict with lineage traits
    """
    # Pages 3-7 contain all lineages
    return extract_features(pdf_path, list(range(3, 8)))
