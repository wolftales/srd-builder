"""Common prose extraction patterns for SRD PDF.

This module provides reusable components for extracting prose sections
(conditions, diseases, madness, etc.) that share similar structural patterns.

Use these helpers in your extract_*.py modules to reduce boilerplate.
"""

from __future__ import annotations

import re
from typing import Any

# Import shared text cleaning utility to avoid duplication
from .postprocess.text import clean_pdf_text

__all__ = ["clean_pdf_text", "extract_bullet_points", "extract_table_by_pattern", "ProseExtractor"]


def extract_bullet_points(text: str) -> list[str]:
    """Extract bullet points from text.

    Supports multiple bullet styles:
    - • (bullet character)
    - Numbered lists (1., 2., etc.)
    - Dashed lists (-, --, etc.)

    Args:
        text: Text containing bullet points

    Returns:
        List of bullet point strings (cleaned)
    """
    bullets = []

    # Try bullet character (•) first - most common in SRD
    bullet_matches = re.findall(r"•\s*([^•]+)", text)
    if bullet_matches:
        bullets = [bullet.strip() for bullet in bullet_matches if bullet.strip()]
        return bullets

    # Try numbered lists (1. item, 2. item)
    numbered_matches = re.findall(r"^\d+\.\s+([^\d]+?)(?=\d+\.|$)", text, re.MULTILINE)
    if numbered_matches:
        bullets = [item.strip() for item in numbered_matches if item.strip()]
        return bullets

    # Try dashed lists (- item, -- item)
    dashed_matches = re.findall(r"^-+\s+([^-]+?)(?=-+\s+|$)", text, re.MULTILINE)
    if dashed_matches:
        bullets = [item.strip() for item in dashed_matches if item.strip()]
        return bullets

    return bullets


def extract_table_by_pattern(
    text: str, pattern: str, column_names: list[str]
) -> list[dict[str, str]]:
    r"""Extract table data using a regex pattern.

    Args:
        text: Text containing table data
        pattern: Regex pattern with capture groups for each column
        column_names: Names for the columns (must match pattern group count)

    Returns:
        List of row dictionaries

    Example:
        >>> pattern = r"(\d+)\s+([A-Z][^0-9]+?)(?=\d+|$)"
        >>> columns = ["level", "effect"]
        >>> extract_table_by_pattern(text, pattern, columns)
        [{"level": "1", "effect": "Disadvantage on ability checks"}, ...]
    """
    rows = []
    matches = re.findall(pattern, text)

    for match in matches:
        if len(match) != len(column_names):
            continue  # Skip malformed rows

        row = {}
        for i, col_name in enumerate(column_names):
            row[col_name] = match[i].strip()
        rows.append(row)

    return rows


def extract_level_effect_table(text: str) -> list[dict[str, str]]:
    """Extract level/effect style tables (common in conditions, diseases).

    Args:
        text: Text containing "Level Effect" style table

    Returns:
        List of dicts with "level" and "effect" keys
    """
    # Look for Level/Effect pattern
    pattern = r"(\d+)\s+([A-Z][^0-9]+?)(?=\d+\s+[A-Z]|$)"
    return extract_table_by_pattern(text, pattern, ["level", "effect"])


def split_by_known_headers(
    text: str, headers: list[str], validate_boundaries: bool = True
) -> list[dict[str, Any]]:
    """Split text into sections using known headers as boundaries.

    This is the core pattern used in extract_conditions.py and can be
    reused for any prose section with known headers.

    Args:
        text: Full text to split
        headers: Ordered list of section headers
        validate_boundaries: If True, add warnings for cross-contamination

    Returns:
        List of sections with name, raw_text, start_pos, end_pos, warnings (optional)

    Example:
        >>> headers = ["Blinded", "Charmed", "Deafened"]
        >>> sections = split_by_known_headers(text, headers)
        >>> sections[0]["name"]  # "Blinded"
    """
    sections = []
    cleaned_text = clean_pdf_text(text)

    for i, header in enumerate(headers):
        # Find this header (word boundary to avoid partial matches)
        # Use case-sensitive matching to avoid matching references like
        # "incapacitated" in other conditions' text vs header "Incapacitated"
        # This is critical because D&D conditions frequently reference each other
        # (e.g., "The grappler is incapacitated" in Grappled condition)
        # Without case-sensitivity, "incapacitated" would incorrectly match the
        # "Incapacitated" header, causing Grappled section to be truncated
        pattern = rf"\b{re.escape(header)}\b"
        match = re.search(pattern, cleaned_text)

        if not match:
            continue

        start_pos = match.start()

        # Find where next header starts (or end of text)
        end_pos = len(cleaned_text)
        if i + 1 < len(headers):
            next_header = headers[i + 1]
            # Use case-sensitive matching to avoid matching lowercase references
            # (same reasoning as above - preserve section integrity)
            next_pattern = rf"\b{re.escape(next_header)}\b"
            next_match = re.search(
                next_pattern,
                cleaned_text[start_pos + len(header) :],
            )
            if next_match:
                end_pos = start_pos + len(header) + next_match.start()

        # Extract section text
        section_text = cleaned_text[start_pos:end_pos].strip()

        section = {
            "name": header,
            "raw_text": section_text,
            "start_pos": start_pos,
            "end_pos": end_pos,
        }

        # Validate boundaries if requested
        if validate_boundaries:
            warnings = _validate_section_boundaries(header, section_text, headers)
            if warnings:
                section["warnings"] = warnings

        sections.append(section)

    return sections


def _validate_section_boundaries(header: str, text: str, all_headers: list[str]) -> list[str]:
    """Validate that section text doesn't contain cross-contamination.

    Args:
        header: This section's header name
        text: Section text to validate
        all_headers: All header names to check for contamination

    Returns:
        List of warning messages (empty if clean)
    """
    warnings = []

    # Check for OTHER headers in this section's text (cross-contamination)
    # Use case-sensitive matching to avoid false positives from lowercase references
    for other_header in all_headers:
        if other_header == header:
            continue

        # Look for other header (capitalized) after first occurrence of current header
        # This catches actual headers bleeding across boundaries
        first_header_pos = text.find(header)
        if first_header_pos == -1:
            continue

        first_header_end = first_header_pos + len(header)
        remaining_text = text[first_header_end:]

        # Case-sensitive search for capitalized header (not lowercase references)
        if re.search(rf"\b{re.escape(other_header)}\b", remaining_text):
            warnings.append(
                f"Section '{header}' contains text from '{other_header}' (cross-contamination)"
            )

    # Check for unreasonably long sections (likely merged multiple sections)
    max_reasonable_length = 2000  # Most conditions are 200-500 chars
    if len(text) > max_reasonable_length:
        warnings.append(
            f"Section '{header}' is {len(text)} chars (expected < {max_reasonable_length})"
        )

    return warnings


def discover_headers_by_font(
    page: Any, font_name: str, font_size: float, tolerance: float = 0.5
) -> list[tuple[str, float]]:
    """Discover section headers by font characteristics.

    Use this when you don't know the header names in advance but can
    identify them by font (e.g., bold, larger size).

    Args:
        page: PyMuPDF page object
        font_name: Font name to match (e.g., "Calibri-Bold")
        font_size: Font size to match (points)
        tolerance: Size tolerance (points)

    Returns:
        List of (header_text, y_position) tuples
    """
    headers = []
    blocks = page.get_text("dict")["blocks"]

    for block in blocks:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            for span in line["spans"]:
                span_font = span["font"]
                span_size = span["size"]
                span_text = span["text"].strip()

                # Check if this span matches our header criteria
                if (
                    font_name in span_font
                    and abs(span_size - font_size) <= tolerance
                    and len(span_text) > 2  # Minimum length
                ):
                    headers.append((span_text, span["bbox"][1]))  # text, y-position

    return headers


def generate_summary(text: str, max_length: int = 150) -> str:
    """Generate a summary from text (first sentence or truncated).

    Args:
        text: Text to summarize
        max_length: Maximum summary length

    Returns:
        Summary string
    """
    # Try to get first complete sentence
    match = re.match(r"^([^.!?]+[.!?])", text)
    if match:
        summary = match.group(1).strip()
        if len(summary) <= max_length:
            return summary

    # Fallback: truncate at word boundary
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    # Find last complete word
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated.strip() + "..."


class ProseExtractor:
    """Reusable prose extraction helper class.

    This class encapsulates common patterns for extracting prose sections
    with known headers. Use it as a base for your extract_*.py modules.

    Example:
        >>> extractor = ProseExtractor(
        ...     section_name="conditions",
        ...     known_headers=["Blinded", "Charmed", "Deafened"],
        ...     start_page=358,
        ...     end_page=359,
        ... )
        >>> result = extractor.extract(pdf_path)
    """

    def __init__(
        self,
        section_name: str,
        known_headers: list[str],
        start_page: int,
        end_page: int,
    ):
        """Initialize extractor.

        Args:
            section_name: Name of the section (e.g., "conditions")
            known_headers: Ordered list of expected section headers
            start_page: Starting page (1-indexed)
            end_page: Ending page (1-indexed)
        """
        self.section_name = section_name
        self.known_headers = known_headers
        self.start_page = start_page
        self.end_page = end_page

    def extract_from_pdf(self, pdf_path: Any) -> tuple[list[dict[str, Any]], list[str]]:
        """Extract sections from PDF with proper column handling.

        Args:
            pdf_path: Path to PDF or open PyMuPDF document

        Returns:
            Tuple of (sections list, warnings list)
        """
        from pathlib import Path

        import fitz

        # Handle both path and open document
        if isinstance(pdf_path, str | Path):
            doc = fitz.open(str(pdf_path))
            should_close = True
        else:
            doc = pdf_path
            should_close = False

        try:
            # Extract text with spatial awareness (column handling)
            full_text = self._extract_text_with_columns(doc)

            # Split by headers
            sections = split_by_known_headers(full_text, self.known_headers)

            # Check for missing sections
            warnings = []
            found_names = {s["name"] for s in sections}
            for header in self.known_headers:
                if header not in found_names:
                    warnings.append(f"Could not find {self.section_name}: {header}")

            return sections, warnings

        finally:
            if should_close:
                doc.close()

    def _extract_text_with_columns(self, doc: Any) -> str:
        """Extract text with proper column reading order.

        Uses spatial sorting to handle two-column layouts correctly.
        Prevents text bleeding across column boundaries.

        Args:
            doc: Open PyMuPDF document

        Returns:
            Text extracted in proper reading order (left column top-to-bottom,
            then right column top-to-bottom)
        """
        full_text = ""

        for page_num in range(self.start_page - 1, self.end_page):
            page = doc[page_num]
            page_rect = page.rect
            mid_x = page_rect.width / 2

            # Extract blocks with position data
            blocks = page.get_text("dict")["blocks"]

            # Separate into columns and sort by position
            left_col = []
            right_col = []

            for block in blocks:
                if "lines" not in block:
                    continue

                bbox = block["bbox"]
                block_x = bbox[0]
                block_y = bbox[1]

                # Extract text from block
                text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        text += span["text"]
                    text += "\n"

                # Assign to column based on x position
                if block_x < mid_x:
                    left_col.append((block_y, text))
                else:
                    right_col.append((block_y, text))

            # Sort each column by y position (top to bottom)
            left_col.sort()
            right_col.sort()

            # Concatenate in reading order: left column, then right column
            for _, text in left_col:
                full_text += text
            for _, text in right_col:
                full_text += text

        return full_text

    def enrich_section(self, section: dict[str, Any]) -> dict[str, Any]:
        """Add common metadata to a section.

        Override this method in subclasses to add section-specific enrichment.

        Args:
            section: Section dictionary from extract_from_pdf

        Returns:
            Enriched section dictionary
        """
        text = section["raw_text"]

        # Add common analyses
        section["bullets"] = extract_bullet_points(text)
        section["has_bullets"] = len(section["bullets"]) > 0
        section["summary"] = generate_summary(text)

        return section
