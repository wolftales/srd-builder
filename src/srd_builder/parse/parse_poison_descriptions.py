"""Parse poison description prose into structured records.

Poison descriptions contain the detailed mechanics (save DC, damage, etc.)
that complement the basic table data (name, type, price).
"""

from __future__ import annotations

import re
from typing import Any

from ..postprocess import normalize_id
from ..utils.prose import clean_text


def parse_poison_description_records(
    raw_sections: list[dict[str, Any]],
    ruleset: str,  # noqa: ARG001 - kept for prose-parser interface uniformity
) -> list[dict[str, Any]]:
    """Parse raw poison description sections.

    Args:
        raw_sections: List of raw section dicts from prose extraction
        ruleset: Accepted for prose-parser interface uniformity; descriptions are
            merged into poison records that get their source stamped elsewhere.

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
    text = clean_text(raw.get("raw_text", ""))
    page = raw.get("page", 204)

    if not name or not text:
        return None

    # Generate simple_name
    simple_name = normalize_id(name)

    # Strip the leading section header "Name (Type). " from the prose body so
    # the description starts with the rules text, matching the prior
    # hand-curated POISON_DESCRIPTIONS shape.
    header_match = re.match(
        rf"\s*{re.escape(name)}\s*\([A-Za-z]+\)\.\s*",
        text,
    )
    if header_match:
        text = text[header_match.end() :]

    result: dict[str, Any] = {
        "simple_name": simple_name,
        "description": text,
        "page": page,
    }

    # Extract save DC if present (e.g., "DC 13 Constitution saving throw")
    save_match = re.search(r"DC\s+(\d+)\s+(\w+)\s+saving\s+throw", text, re.IGNORECASE)
    if save_match:
        result["save"] = {"dc": int(save_match.group(1)), "ability": save_match.group(2).lower()}

    # Extract damage if present. Covers all three SRD poison phrasings:
    #   "takes 6 (1d12) poison damage"          (assassin's blood)
    #   "take 10 (3d6) poison damage"           (burnt othur fumes, pale tincture)
    #   "taking 24 (7d6) poison damage on a failed save"  (midnight tears,
    #       purple worm poison, serpent venom, wyvern poison)
    damage_match = re.search(
        r"tak(?:es?|ing)\s+(\d+)\s*\(([^)]+)\)\s+(\w+)\s+damage",
        text,
        re.IGNORECASE,
    )
    if damage_match:
        damage_type = damage_match.group(3).lower()
        result["damage"] = {
            "average": int(damage_match.group(1)),
            "formula": damage_match.group(2),
            "type": damage_type,
            "type_id": f"damage:{damage_type}",
        }

    return result
