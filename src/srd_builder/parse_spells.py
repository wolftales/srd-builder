"""Parse raw spell data into structured format.

Converts raw spell text from PDF extraction into structured spell objects
matching the spell schema (v1.3.0).

This is a STUB implementation - full parsing will be implemented incrementally.
"""

from __future__ import annotations

from typing import Any


def parse_spell_records(raw_spells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw spell data into structured spell records.

    Args:
        raw_spells: List of raw spell dicts from extract_spells

    Returns:
        List of structured spell dicts matching spell.schema.json
    """
    parsed = []

    for raw_spell in raw_spells:
        # TODO: Implement actual parsing
        # For now, create minimal stub structure
        spell = {
            "name": raw_spell.get("name", "Unknown Spell"),
            "level": 0,  # Placeholder
            "school": "evocation",  # Placeholder
            "casting": {
                "time": "1 action",
                "range": "self",
                "duration": "Instantaneous",
                "concentration": False,
                "ritual": False,
            },
            "components": {
                "verbal": False,
                "somatic": False,
                "material": False,
            },
            "text": raw_spell.get("description_text", ""),
            "page": raw_spell.get("pages", [0])[0] if raw_spell.get("pages") else 0,
        }

        parsed.append(spell)

    return parsed


def _parse_level_and_school(level_school_text: str) -> tuple[int, str]:
    """Parse spell level and school from text like '3rd-level evocation'.

    Args:
        level_school_text: Text containing level and school

    Returns:
        Tuple of (level, school)
    """
    # TODO: Implement parsing
    return (0, "evocation")


def _parse_casting_time(text: str) -> str:
    """Parse casting time from spell header.

    Args:
        text: Casting time text

    Returns:
        Normalized casting time
    """
    # TODO: Implement parsing
    return "1 action"


def _parse_range(text: str) -> dict[str, Any] | str:
    """Parse spell range into structured format.

    Args:
        text: Range text (e.g., "150 feet", "Self", "Touch")

    Returns:
        Structured range object or string for special cases
    """
    # TODO: Implement parsing
    return "self"


def _parse_duration(text: str) -> tuple[str, bool]:
    """Parse duration and detect concentration.

    Args:
        text: Duration text

    Returns:
        Tuple of (duration, requires_concentration)
    """
    # TODO: Implement parsing
    return ("Instantaneous", False)


def _parse_components(text: str) -> dict[str, Any]:
    """Parse spell components (V/S/M).

    Args:
        text: Components text (e.g., "V, S, M (a tiny ball of bat guano)")

    Returns:
        Components dict with verbal, somatic, material, material_description
    """
    # TODO: Implement parsing
    return {
        "verbal": False,
        "somatic": False,
        "material": False,
    }


def _extract_effects(description: str) -> dict[str, Any]:
    """Extract damage, healing, saves, etc. from spell description.

    Args:
        description: Full spell description text

    Returns:
        Effects dict (may be empty if no extractable effects)
    """
    # TODO: Implement parsing
    return {}


def _extract_scaling(description: str, level: int) -> dict[str, Any] | None:
    """Extract scaling information from spell description.

    Args:
        description: Full spell description text
        level: Spell level (0 = cantrip)

    Returns:
        Scaling dict or None if spell doesn't scale
    """
    # TODO: Implement parsing
    return None
