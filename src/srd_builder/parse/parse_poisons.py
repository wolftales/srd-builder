"""Parse raw poison data extracted from SRD PDF.

This module takes the raw poison text from extract_poisons.py
and parses it into structured poison records according to the schema.
"""

from __future__ import annotations

import re
from typing import Any

from ..extract.extract_prose import clean_text
from .postprocess import normalize_id


def parse_poison_records(raw_poisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw poison extractions into structured records.

    Args:
        raw_poisons: List of raw poison dictionaries from extract_poisons

    Returns:
        List of parsed poison dictionaries matching the schema
    """
    parsed = []

    for raw in raw_poisons:
        poison = _parse_single_poison(raw)
        if poison:
            parsed.append(poison)

    return parsed


def _parse_single_poison(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single raw poison into structured format.

    Args:
        raw: Raw poison dictionary with name, raw_text, page

    Returns:
        Parsed poison dictionary or None if parsing fails
    """
    name = raw.get("name", "").strip()
    raw_text = raw.get("raw_text", "")
    page = raw.get("page", 204)

    if not name or not raw_text:
        return None

    # Clean up text
    text = clean_text(raw_text)

    # Generate simple_name
    simple_name = normalize_id(name)

    # Extract poison type (Contact, Ingested, Inhaled, Injury)
    # Usually appears at start of text or in parentheses after name
    poison_type = _extract_poison_type(text)

    # Extract save information
    save_info = _extract_save_info(text)

    # Extract damage information
    damage_info = _extract_damage_info(text)

    # Extract condition
    condition = _extract_condition(text)

    # Extract duration
    duration = _extract_duration(text)

    # Extract cost
    cost = _extract_cost(text)

    result = {
        "id": f"poison:{simple_name}",
        "name": name,
        "simple_name": simple_name,
        "type": poison_type if poison_type else "injury",  # Default to injury
        "description": text,
        "page": page,
        "source": "SRD 5.1",
    }

    # Add optional fields if present
    if save_info:
        result["save"] = save_info
    if damage_info:
        result["damage"] = damage_info
    if condition:
        result["condition"] = condition
    if duration:
        result["duration"] = duration
    if cost:
        result["cost"] = cost

    return result


def _extract_poison_type(text: str) -> str | None:
    """Extract poison type from text.

    Args:
        text: Cleaned poison text

    Returns:
        Poison type or None
    """
    # Look for type keywords
    type_pattern = r"\b(Contact|Ingested|Inhaled|Injury)\b"
    match = re.search(type_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def _extract_save_info(text: str) -> dict[str, Any] | None:
    """Extract saving throw information.

    Args:
        text: Cleaned poison text

    Returns:
        Save info dict or None
    """
    save_pattern = r"(Constitution|Strength|Dexterity|Intelligence|Wisdom|Charisma)\s+saving throw.*?DC\s+(\d+)"
    match = re.search(save_pattern, text, re.IGNORECASE)
    if match:
        return {
            "ability": match.group(1).lower(),
            "dc": int(match.group(2)),
        }
    return None


def _extract_damage_info(text: str) -> dict[str, Any] | None:
    """Extract damage information.

    Args:
        text: Cleaned poison text

    Returns:
        Damage info dict or None
    """
    # Look for damage patterns like "3d6 poison damage"
    damage_pattern = r"(\d+d\d+(?:\s*\+\s*\d+)?)\s+(poison|necrotic|psychic)?\s*damage"
    match = re.search(damage_pattern, text, re.IGNORECASE)
    if match:
        damage_type = match.group(2).lower() if match.group(2) else "poison"
        return {
            "dice": match.group(1),
            "type": damage_type,
            "type_id": f"damage_type:{damage_type}",
        }
    return None


def _extract_condition(text: str) -> str | None:
    """Extract condition imposed by poison.

    Args:
        text: Cleaned poison text

    Returns:
        Condition name or None
    """
    condition_pattern = r"\b(poisoned|paralyzed|unconscious|stunned)\b"
    match = re.search(condition_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def _extract_duration(text: str) -> str | None:
    """Extract duration of poison effects.

    Args:
        text: Cleaned poison text

    Returns:
        Duration string or None
    """
    duration_pattern = r"for\s+(\d+\s+(?:hours?|minutes?|days?)|until)"
    match = re.search(duration_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_cost(text: str) -> dict[str, Any] | None:
    """Extract poison cost.

    Args:
        text: Cleaned poison text

    Returns:
        Cost info dict or None
    """
    cost_pattern = r"(\d+(?:,\d{3})*)\s*(cp|sp|gp|pp)\b"
    match = re.search(cost_pattern, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(",", "")
        return {
            "amount": int(amount_str),
            "currency": match.group(2).lower(),
        }
    return None
