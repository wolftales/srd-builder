"""Parse raw condition data extracted from SRD PDF.

This module takes the raw condition text from extract_conditions.py
and parses it into structured condition records according to the schema.
"""

from __future__ import annotations

import re
from typing import Any

from ..extract.prose_extraction import clean_pdf_text, extract_bullet_points
from ..postprocess import normalize_id


def parse_condition_records(raw_conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw condition extractions into structured records.

    Args:
        raw_conditions: List of raw condition dictionaries from extract_conditions

    Returns:
        List of parsed condition dictionaries matching the schema
    """
    parsed = []

    for raw in raw_conditions:
        condition = _parse_single_condition(raw)
        if condition:
            parsed.append(condition)

    return parsed


def _parse_single_condition(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single raw condition into structured format.

    Args:
        raw: Raw condition dictionary with name, raw_text, pages

    Returns:
        Parsed condition dictionary or None if parsing fails
    """
    name = raw.get("name", "").strip()
    raw_text = raw.get("raw_text", "")
    pages = raw.get("pages", [])

    if not name or not raw_text:
        return None

    text = clean_pdf_text(raw_text)

    # Generate simple_name
    simple_name = normalize_id(name)

    # Parse based on condition type
    if name == "Exhaustion":
        return _parse_exhaustion(name, simple_name, text, pages)
    else:
        return _parse_standard_condition(name, simple_name, text, pages)


def _parse_standard_condition(
    name: str, simple_name: str, text: str, pages: list[int]
) -> dict[str, Any]:
    """Parse a standard (non-Exhaustion) condition.

    Args:
        name: Condition name
        simple_name: Normalized identifier
        text: Cleaned condition text
        pages: Source pages

    Returns:
        Parsed condition dictionary
    """
    # Extract bullet points (effects)
    effects = extract_bullet_points(text)

    # If no bullets found, use the whole text as a single effect
    if not effects:
        effects = [text]

    # Generate summary from first effect
    summary = _generate_summary(effects[0] if effects else text)

    # Get source page (use first page)
    page = pages[0] if pages else 358

    return {
        "id": f"condition:{simple_name}",
        "name": name,
        "simple_name": simple_name,
        "page": page,
        "source": "SRD 5.1",
        "summary": summary,
        "effects": effects,
    }


def _parse_exhaustion(name: str, simple_name: str, text: str, pages: list[int]) -> dict[str, Any]:
    """Parse the Exhaustion condition with its special level structure.

    Args:
        name: Condition name
        simple_name: Normalized identifier
        text: Cleaned condition text
        pages: Source pages

    Returns:
        Parsed exhaustion condition dictionary
    """
    # Extract the introduction paragraph (before the level table)
    intro_match = re.search(
        r"Exhaustion (.*?)(?:Level Effect|Disadvantage on ability checks)", text
    )
    intro_text = intro_match.group(1).strip() if intro_match else ""

    # Parse the level table
    levels = []
    level_patterns = [
        (1, r"1\s+Disadvantage on ability checks"),
        (2, r"2\s+Speed halved"),
        (3, r"3\s+Disadvantage on attack rolls and saving throws"),
        (4, r"4\s+Hit point maximum halved"),
        (5, r"5\s+Speed reduced to 0"),
        (6, r"6\s+Death"),
    ]

    for level_num, pattern in level_patterns:
        if re.search(pattern, text):
            # Extract the effect text
            match = re.search(pattern, text)
            if match:
                effect_text = match.group(0)
                # Remove the level number
                effect_text = re.sub(rf"^{level_num}\s+", "", effect_text)
                levels.append({"level": level_num, "effect": effect_text})

    # Extract special rules (paragraphs after the table)
    special_rules = []

    # Find all sentences after "Death" that explain exhaustion mechanics
    after_table = re.search(r"Death\s+(.*)", text)
    if after_table:
        rules_text = after_table.group(1).strip()
        # Split into sentences (roughly)
        sentences = re.split(r"\.\s+", rules_text)
        for raw_sentence in sentences:
            cleaned = raw_sentence.strip()
            if cleaned and len(cleaned) > 20:  # Skip very short fragments
                if not cleaned.endswith("."):
                    cleaned += "."
                special_rules.append(cleaned)

    # Main effects (bullet points if any, plus intro)
    effects = [intro_text] if intro_text else []

    summary = "Exhaustion is measured in six levels"

    page = pages[0] if pages else 358

    condition_dict: dict[str, Any] = {
        "id": f"condition:{simple_name}",
        "name": name,
        "simple_name": simple_name,
        "page": page,
        "source": "SRD 5.1",
        "summary": summary,
        "effects": effects,
        "levels": levels,
    }

    if special_rules:
        condition_dict["special_rules"] = special_rules

    return condition_dict


def _generate_summary(text: str) -> str:
    """Generate a one-sentence summary from the first effect.

    Args:
        text: Effect text

    Returns:
        Summary sentence
    """
    # Take first sentence
    match = re.match(r"^([^.!?]+[.!?])", text)
    if match:
        return match.group(1).strip()

    # Fallback: take first 100 characters
    if len(text) > 100:
        return text[:97] + "..."

    return text
