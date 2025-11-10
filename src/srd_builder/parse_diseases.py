"""Parse raw disease data extracted from SRD PDF.

This module takes the raw disease text from extract_diseases.py
and parses it into structured disease records according to the schema.
"""

from __future__ import annotations

import re
from typing import Any

from .prose_extraction import clean_pdf_text, extract_bullet_points


def parse_disease_records(raw_diseases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw disease extractions into structured records.

    Args:
        raw_diseases: List of raw disease dictionaries from extract_diseases

    Returns:
        List of parsed disease dictionaries matching the schema
    """
    parsed = []

    for raw in raw_diseases:
        disease = _parse_single_disease(raw)
        if disease:
            parsed.append(disease)

    return parsed


def _parse_single_disease(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single raw disease into structured format.

    Args:
        raw: Raw disease dictionary with name, raw_text, page

    Returns:
        Parsed disease dictionary or None if parsing fails
    """
    name = raw.get("name", "").strip()
    raw_text = raw.get("raw_text", "")
    page = raw.get("page", 199)

    if not name or not raw_text:
        return None

    # Clean up text
    text = clean_pdf_text(raw_text)

    # Generate simple_name
    simple_name = name.lower().replace(" ", "_").replace("'", "")

    # Extract components
    description = text
    effects = []
    save_info = None
    incubation = None

    # Try to extract save information (pattern: "Constitution saving throw", "DC X")
    save_match = re.search(
        r"(Constitution|Strength|Dexterity|Intelligence|Wisdom|Charisma)\s+saving throw.*?DC\s+(\d+)",
        text,
        re.IGNORECASE,
    )
    if save_match:
        save_info = {
            "ability": save_match.group(1).lower(),
            "dc": int(save_match.group(2)),
        }

    # Try to extract bullet-point effects
    effects = extract_bullet_points(text)

    # Extract incubation period if mentioned
    incubation_match = re.search(
        r"incubation.*?(\d+d\d+.*?(?:hours?|days?|weeks?))", text, re.IGNORECASE
    )
    if incubation_match:
        incubation = incubation_match.group(1).strip()

    # Generate summary (first sentence or first 100 chars)
    summary = _generate_summary(text)

    result = {
        "id": f"disease:{simple_name}",
        "name": name,
        "simple_name": simple_name,
        "page": page,
        "source": "SRD 5.1",
        "summary": summary,
        "description": description,
    }

    # Add optional fields if present
    if effects:
        result["effects"] = effects
    if save_info:
        result["save"] = save_info
    if incubation:
        result["incubation"] = incubation

    return result


def _generate_summary(text: str) -> str:
    """Generate a one-sentence summary from text.

    Args:
        text: Full text to summarize

    Returns:
        Summary string (first sentence or first 100 chars)
    """
    # Try to get first sentence
    match = re.match(r"([^.!?]+[.!?])", text)
    if match:
        summary = match.group(1).strip()
        if len(summary) <= 150:
            return summary

    # Fallback to first 100 chars
    if len(text) <= 100:
        return text
    return text[:97] + "..."
