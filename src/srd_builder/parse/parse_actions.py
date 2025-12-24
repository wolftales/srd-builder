"""Parse structured data from monster action text."""

from __future__ import annotations

import re
from typing import Any

__all__ = ["parse_action_fields"]


# Patterns for action parsing
_ATTACK_HEADER = re.compile(
    r"^(Melee|Ranged)\s+(Weapon|Spell)\s+Attack:",
    re.IGNORECASE,
)
_TO_HIT = re.compile(r"([+\-]\d+)\s+to\s+hit", re.IGNORECASE)
_REACH = re.compile(r"reach\s+(\d+)\s*ft", re.IGNORECASE)
_RANGE = re.compile(r"range\s+(\d+)/(\d+)\s*ft", re.IGNORECASE)
_DAMAGE = re.compile(
    r"(\d+)\s*\(\s*(\d+d\d+(?:\s*[+\-]\s*\d+)?)\s*\)\s+(\w+)\s+damage",
    re.IGNORECASE,
)
_SAVING_THROW = re.compile(
    r"DC\s+(\d+)\s+([A-Za-z]+)(?:\s+saving\s+throw)?",
    re.IGNORECASE,
)


def parse_action_fields(action: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    """Parse structured fields from action text for v2.0 schema.

    Extracts (schema v2.0.0 format):
    - attack_bonus: integer (from "+X to hit")
    - damage: array of {dice: str, type: str, type_id: str}
    - dc: {dc_value: int, dc_type: str, dc_type_id: str, success_type: str}
    - range: {reach: int, normal: int, long: int}

    Uses description array (not legacy text field).
    """
    patched = {**action}

    # Get description - support both array and string formats
    description = action.get("description", [])
    if isinstance(description, str):
        text = description
    elif isinstance(description, list) and description:
        text = " ".join(description)
    else:
        # Fallback to legacy text field
        text = action.get("text", "")

    if not isinstance(text, str):
        return patched

    # Parse attack bonus
    to_hit_match = _TO_HIT.search(text)
    if to_hit_match:
        try:
            patched["attack_bonus"] = int(to_hit_match.group(1))
        except ValueError:
            pass

    # Parse range object (v2.0 structure)
    range_obj: dict[str, int] = {}

    # Reach (for melee attacks)
    reach_match = _REACH.search(text)
    if reach_match:
        try:
            range_obj["reach"] = int(reach_match.group(1))
        except ValueError:
            pass

    # Range (for ranged attacks)
    range_match = _RANGE.search(text)
    if range_match:
        try:
            range_obj["normal"] = int(range_match.group(1))
            range_obj["long"] = int(range_match.group(2))
        except ValueError:
            pass

    if range_obj:
        patched["range"] = range_obj

    # Parse damage array (v2.0 structure)
    damage_matches = list(_DAMAGE.finditer(text))
    if damage_matches:
        damage_array = []
        for match in damage_matches:
            try:
                damage_dice = match.group(2).strip()
                # Normalize spacing: "2d6 + 5" -> "2d6+5"
                damage_dice = re.sub(r"\s+", "", damage_dice)
                damage_type = match.group(3).lower()

                damage_array.append(
                    {
                        "dice": damage_dice,
                        "type": damage_type,
                        "type_id": f"damage:{damage_type.replace(' ', '_')}",
                    }
                )
            except (ValueError, IndexError):
                continue

        if damage_array:
            patched["damage"] = damage_array

    # Parse saving throw (v2.0 dc structure)
    save_match = _SAVING_THROW.search(text)
    if save_match:
        try:
            ability_full = save_match.group(2).lower()

            # Map short/full forms to schema IDs (full prefixed format)
            ability_id_map = {
                "str": "ability:strength",
                "strength": "ability:strength",
                "dex": "ability:dexterity",
                "dexterity": "ability:dexterity",
                "con": "ability:constitution",
                "constitution": "ability:constitution",
                "int": "ability:intelligence",
                "intelligence": "ability:intelligence",
                "wis": "ability:wisdom",
                "wisdom": "ability:wisdom",
                "cha": "ability:charisma",
                "charisma": "ability:charisma",
            }

            ability_name_map = {
                "ability:strength": "Strength",
                "ability:dexterity": "Dexterity",
                "ability:constitution": "Constitution",
                "ability:intelligence": "Intelligence",
                "ability:wisdom": "Wisdom",
                "ability:charisma": "Charisma",
            }

            dc_type_id = ability_id_map.get(ability_full, f"ability:{ability_full[:3]}")
            dc_type = ability_name_map.get(dc_type_id, ability_full.capitalize())

            # Determine success_type from context
            success_type = "none"
            if "half" in text.lower() or "half as much" in text.lower():
                success_type = "half"

            patched["dc"] = {
                "dc_value": int(save_match.group(1)),
                "dc_type": dc_type,
                "dc_type_id": dc_type_id,
                "success_type": success_type,
            }
        except (ValueError, IndexError):
            pass

    return patched
