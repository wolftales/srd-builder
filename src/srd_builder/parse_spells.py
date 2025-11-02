"""Parse raw spell data into structured format.

Converts raw spell text from PDF extraction into structured spell objects
matching the spell schema (v1.3.0).

This is a STUB implementation - full parsing will be implemented incrementally.
"""

from __future__ import annotations

import re
from typing import Any


def _clean_text(text: str) -> str:
    """Clean garbled PDF text.

    Removes Unicode control characters, normalizes whitespace.
    """
    # Remove control chars, soft hyphens, non-breaking spaces
    text = re.sub(r"[\t\r\n\u00ad\u2010\u2011\u00a0]+", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_spell_records(raw_spells: list[dict[str, Any]]) -> list[dict[str, Any]]:  # noqa: C901
    """Parse raw spell data into structured spell records.

    Args:
        raw_spells: List of raw spell dicts from extract_spells

    Returns:
        List of structured spell dicts matching spell.schema.json
    """
    parsed = []

    for raw_spell in raw_spells:
        name = _clean_text(raw_spell.get("name", "Unknown Spell"))
        header_text = _clean_text(raw_spell.get("header_text", ""))
        description_text = _clean_text(raw_spell.get("description_text", ""))
        level_and_school = _clean_text(raw_spell.get("level_and_school", ""))

        # Fix edge case: multi-page spells where description ended up in header_text
        # Pattern: "Duration: X System Reference Document 5.1 [page] [actual description]"
        if description_text == "" and "System Reference Document" in header_text:
            # Split at the SRD marker - everything after is the description
            parts = re.split(r"System\s+Reference\s+Document\s+5\.1\s+\d+", header_text, maxsplit=1)
            if len(parts) == 2:
                header_text = parts[0].strip()
                description_text = parts[1].strip()

        # Parse level and school
        level, school = _parse_level_and_school(level_and_school)

        # Parse header fields (format: "Casting Time: X\nRange: Y\nComponents: Z\nDuration: W")
        casting_time = "1 action"
        range_value: dict[str, Any] | str = "self"
        components_value = {"verbal": False, "somatic": False, "material": False}
        duration_value = "instantaneous"
        concentration = False
        ritual = False

        # Extract individual header fields
        # Header may be multi-line or single-line with field markers
        # Use regex to extract fields by looking for label patterns
        # Fields end at next label (word followed by colon)

        # Extract Casting Time
        if match := re.search(
            r"Casting Time:\s*(.+?)(?=\s+Range:|\s+Components:|\s+Duration:|$)", header_text
        ):
            casting_time = _parse_casting_time(match.group(1).strip())
            if "(ritual)" in casting_time.lower():
                ritual = True
                casting_time = casting_time.replace("(ritual)", "").strip()

        # Extract Range
        if match := re.search(r"Range:\s*(.+?)(?=\s+Components:|\s+Duration:|$)", header_text):
            range_value = _parse_range(match.group(1).strip())

        # Extract Components
        if match := re.search(r"Components:\s*(.+?)(?=\s+Duration:|$)", header_text):
            components_value = _parse_components(match.group(1).strip())

        # Extract Duration
        if match := re.search(r"Duration:\s*(.+?)$", header_text):
            duration_value, concentration = _parse_duration(match.group(1).strip())

        # Extract effects and scaling from description
        effects = _extract_effects(description_text)
        scaling = _extract_scaling(description_text, level)

        # Build spell structure
        spell: dict[str, Any] = {
            "name": name,
            "level": level,
            "school": school,
            "casting": {
                "time": casting_time,
                "range": range_value,
                "duration": duration_value,
                "concentration": concentration,
                "ritual": ritual,
            },
            "components": components_value,
            "text": description_text,
            "page": raw_spell.get("pages", [0])[0] if raw_spell.get("pages") else 0,
        }

        # Add optional fields
        if effects:
            spell["effects"] = effects
        if scaling:
            spell["scaling"] = scaling

        parsed.append(spell)

    return parsed


def _parse_level_and_school(level_school_text: str) -> tuple[int, str]:
    """Parse spell level and school from text like '3rd-level evocation'.

    Args:
        level_school_text: Text containing level and school

    Returns:
        Tuple of (level, school)
    """
    import re

    text = level_school_text.lower().strip()

    # Check for cantrip
    if "cantrip" in text:
        # Extract school name (word before "cantrip")
        school = text.split()[0] if text.split() else "evocation"
        return (0, school)

    # Parse leveled spell (e.g., "3rd-level evocation", "2nd- level evocation")
    # Handle optional space after hyphen due to PDF garbling
    match = re.match(r"(\d+)(?:st|nd|rd|th)-?\s*level\s+(\w+)", text)
    if match:
        level = int(match.group(1))
        school = match.group(2)
        return (level, school)

    return (0, "evocation")


def _parse_casting_time(text: str) -> str:
    """Parse casting time from spell header.

    Args:
        text: Casting time text

    Returns:
        Normalized casting time
    """
    return text.strip()


def _parse_range(text: str) -> dict[str, Any] | str:
    """Parse spell range into structured format.

    Args:
        text: Range text (e.g., "150 feet", "Self", "Touch")

    Returns:
        Structured range object or string for special cases
    """
    import re

    text_lower = text.lower().strip()

    # Special ranges
    if text_lower == "self":
        return "self"
    if text_lower == "touch":
        return "touch"
    if text_lower == "sight":
        return "sight"
    if text_lower == "unlimited":
        return "unlimited"

    # Numeric range (e.g., "150 feet")
    match = re.match(r"(\d+)\s+(feet|miles|foot|mile)", text_lower)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        # Normalize to plural
        if unit in ("foot", "feet"):
            unit = "feet"
        elif unit in ("mile", "miles"):
            unit = "miles"
        return {"kind": "ranged", "value": value, "unit": unit}

    # Fallback to self
    return "self"


def _parse_duration(text: str) -> tuple[str, bool]:
    """Parse duration and detect concentration.

    Args:
        text: Duration text

    Returns:
        Tuple of (duration, requires_concentration)
    """
    text_lower = text.lower().strip()

    # Check for concentration
    concentration = "concentration" in text_lower

    # Remove "concentration, " prefix if present
    if concentration:
        text_lower = text_lower.replace("concentration,", "").strip()

    return (text_lower, concentration)


def _parse_components(text: str) -> dict[str, Any]:
    """Parse spell components (V/S/M).

    Args:
        text: Components text (e.g., "V, S, M (a tiny ball of bat guano)")

    Returns:
        Components dict with verbal, somatic, material, material_description
    """
    import re

    components: dict[str, Any] = {
        "verbal": "V" in text.upper(),
        "somatic": "S" in text.upper(),
        "material": "M" in text.upper(),
    }

    # Extract material description from parentheses
    match = re.search(r"M\s*\(([^)]+)\)", text, re.IGNORECASE)
    if match:
        components["material_description"] = match.group(1).strip()

    return components


def _extract_effects(description: str) -> dict[str, Any]:
    """Extract damage, healing, saves, etc. from spell description.

    Args:
        description: Full spell description text

    Returns:
        Effects dict (may be empty if no extractable effects)
    """
    import re

    effects: dict[str, Any] = {}

    # Extract damage
    damage_pattern = r"(\d+d\d+)\s+(acid|bludgeoning|cold|fire|force|lightning|necrotic|piercing|poison|psychic|radiant|slashing|thunder)\s+damage"
    damage_match = re.search(damage_pattern, description, re.IGNORECASE)
    if damage_match:
        effects["damage"] = {
            "dice": damage_match.group(1),
            "type": damage_match.group(2).lower(),
        }

    # Extract saving throw
    save_pattern = (
        r"(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+saving\s+throw"
    )
    save_match = re.search(save_pattern, description, re.IGNORECASE)
    if save_match:
        ability = save_match.group(1).lower()
        # Determine success behavior (schema values: 'none', 'half', 'negates', 'other')
        on_success = "half"
        if "half as much damage" in description.lower():
            on_success = "half"
        elif "negates" in description.lower():
            on_success = "negates"

        effects["save"] = {"ability": ability, "on_success": on_success}

    # Extract area
    area_pattern = r"(\d+)-foot[- ](?:radius\s+)?(sphere|cone|cube|cylinder|line)"
    area_match = re.search(area_pattern, description, re.IGNORECASE)
    if area_match:
        effects["area"] = {
            "shape": area_match.group(2).lower(),
            "size": int(area_match.group(1)),
            "unit": "feet",
        }

    return effects


def _extract_scaling(description: str, level: int) -> dict[str, Any] | None:
    """Extract scaling information from spell description.

    Args:
        description: Full spell description text
        level: Spell level (0 = cantrip)

    Returns:
        Scaling dict or None if spell doesn't scale
    """
    import re

    # Check for "At Higher Levels" section (slot scaling)
    higher_levels_match = re.search(
        r"At Higher Levels\.\s*(.+?)(?:\.|$)", description, re.IGNORECASE | re.DOTALL
    )
    if higher_levels_match:
        formula_text = higher_levels_match.group(1).strip()
        return {"type": "slot", "base_level": level, "formula": formula_text}

    # Check for character level scaling (cantrips)
    if level == 0:
        char_level_pattern = r"(?:increases|becomes).*?(?:5th|11th|17th).*?level"
        if re.search(char_level_pattern, description, re.IGNORECASE):
            # Extract the scaling formula
            formula_match = re.search(
                r"(\+?\d+d\d+).*?(?:5th|11th|17th)", description, re.IGNORECASE
            )
            if formula_match:
                return {
                    "type": "character_level",
                    "base_level": 1,
                    "formula": formula_match.group(0),
                }

    return None
