"""Parse raw madness data extracted from SRD PDF.

This module takes the raw madness text from extract_madness.py
and parses it into structured madness records according to the schema.
"""

from __future__ import annotations

import re
from typing import Any

from ..extract.prose_extraction import clean_pdf_text
from ..postprocess import normalize_id


def parse_madness_records(raw_categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw madness extractions into structured records.

    Args:
        raw_categories: List of raw madness category dicts from extract_madness

    Returns:
        List of parsed madness dictionaries matching the schema
    """
    parsed = []

    for raw in raw_categories:
        madness = _parse_single_madness(raw)
        if madness:
            parsed.append(madness)

    return parsed


def _parse_single_madness(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single raw madness category into structured format.

    Args:
        raw: Raw madness dictionary with name, raw_text, page

    Returns:
        Parsed madness dictionary or None if parsing fails
    """
    name = raw.get("name", "").strip()
    raw_text = raw.get("raw_text", "")
    page = raw.get("page", 201)

    if not name or not raw_text:
        return None

    # Clean up text
    text = clean_pdf_text(raw_text)

    # Generate simple_name
    simple_name = normalize_id(name)

    # Determine duration based on category name
    duration_map = {
        "short_term_madness": "1d10 minutes",
        "long_term_madness": "1d10 × 10 hours",
        "indefinite_madness": "until cured",
    }
    duration = duration_map.get(simple_name, "varies")

    # Extract the madness effect table
    effects = _extract_madness_effects(text)

    # Generate summary
    summary = f"{name} lasts {duration}"

    result = {
        "id": f"madness:{simple_name}",
        "name": name,
        "simple_name": simple_name,
        "summary": summary,
        "duration": duration,
        "effects": effects,
        "page": page,
        "source": "SRD 5.1",
    }

    return result


def _extract_madness_effects(text: str) -> list[dict[str, str]]:
    """Extract madness effect table entries from text.

    Expected format:
    d100 Effect
    1-10 The character feels...
    11-20 The character becomes...

    Args:
        text: Cleaned madness text

    Returns:
        List of effect dictionaries with roll and effect keys
    """
    effects = []

    # Pattern for d100 table entries: "1-10 Effect text"
    # Also handles single numbers: "100 Effect text"
    pattern = r"(\d+(?:-\d+)?)\s+(.+?)(?=\d+(?:-\d+)?\s+|$)"

    matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)

    for match in matches:
        roll = match.group(1).strip()
        effect = match.group(2).strip()

        # Clean up the effect text
        effect = re.sub(r"\s+", " ", effect)
        effect = effect.rstrip(",. ")

        # Skip if it's obviously a header
        if len(effect) < 10 or effect.lower() in ["effect", "the character"]:
            continue

        effects.append(
            {
                "roll": roll,
                "effect": effect,
            }
        )

    return effects
