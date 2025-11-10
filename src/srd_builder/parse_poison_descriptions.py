"""Parse poison description prose into structured records.

Poison descriptions contain the detailed mechanics (save DC, damage, etc.)
that complement the basic table data (name, type, price).
"""

from __future__ import annotations

import re
from typing import Any

from .prose_extraction import clean_pdf_text


def parse_poison_description_records(raw_sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw poison description sections.

    Args:
        raw_sections: List of raw section dicts from prose extraction

    Returns:
        List of parsed description records (for build_prose_dataset)
    """
    descriptions = []

    for raw in raw_sections:
        parsed = _parse_single_description(raw)
        if parsed:
            descriptions.append(parsed)

    return descriptions


def _parse_single_description(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single poison description.

    Args:
        raw: Raw section dict with name, raw_text, page

    Returns:
        Parsed description dict or None
    """
    name = raw.get("name", "").strip()
    text = clean_pdf_text(raw.get("raw_text", ""))
    page = raw.get("page", 204)

    if not name or not text:
        return None

    # Generate simple_name
    simple_name = name.lower().replace(" ", "_").replace("'", "")

    result: dict[str, Any] = {
        "simple_name": simple_name,
        "description": text,
        "page": page,
    }

    # Extract save DC if present (e.g., "DC 13 Constitution saving throw")
    save_match = re.search(r"DC\s+(\d+)\s+(\w+)\s+saving\s+throw", text, re.IGNORECASE)
    if save_match:
        result["save"] = {"dc": int(save_match.group(1)), "ability": save_match.group(2).lower()}

    # Extract damage if present (e.g., "takes 6 (1d12) poison damage")
    damage_match = re.search(r"takes?\s+(\d+)\s*\(([^)]+)\)\s+(\w+)\s+damage", text, re.IGNORECASE)
    if damage_match:
        result["damage"] = {
            "average": int(damage_match.group(1)),
            "formula": damage_match.group(2),
            "type": damage_match.group(3).lower(),
        }

    return result
