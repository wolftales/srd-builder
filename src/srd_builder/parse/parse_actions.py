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
    """Parse structured fields from action text.

    Extracts:
    - attack_type: "melee_weapon", "ranged_weapon", "melee_spell", "ranged_spell"
    - to_hit: integer bonus
    - reach: integer (feet)
    - range: {normal: int, long: int}
    - damage: {average: int, dice: str, type: str}
    - saving_throw: {dc: int, ability: str}

    Preserves original text field for fallback.
    """
    patched = {**action}
    text = action.get("text", "")

    if not isinstance(text, str):
        return patched

    # Parse attack type
    attack_match = _ATTACK_HEADER.search(text)
    if attack_match:
        attack_category = attack_match.group(1).lower()  # melee or ranged
        attack_kind = attack_match.group(2).lower()  # weapon or spell
        patched["attack_type"] = f"{attack_category}_{attack_kind}"

    # Parse to-hit bonus
    to_hit_match = _TO_HIT.search(text)
    if to_hit_match:
        try:
            patched["to_hit"] = int(to_hit_match.group(1))
        except ValueError:
            pass

    # Parse reach (for melee attacks)
    reach_match = _REACH.search(text)
    if reach_match:
        try:
            patched["reach"] = int(reach_match.group(1))
        except ValueError:
            pass

    # Parse range (for ranged attacks)
    range_match = _RANGE.search(text)
    if range_match:
        try:
            patched["range"] = {
                "normal": int(range_match.group(1)),
                "long": int(range_match.group(2)),
            }
        except ValueError:
            pass

    # Parse damage (can have multiple damage instances)
    damage_matches = list(_DAMAGE.finditer(text))
    if damage_matches:
        # Take first damage as primary
        first = damage_matches[0]
        try:
            damage_dice = first.group(2).strip()
            # Normalize spacing: "2d6 + 5" or "2d6+5"
            damage_dice = re.sub(r"\s+", "", damage_dice)

            patched["damage"] = {
                "average": int(first.group(1)),
                "dice": damage_dice,
                "type": first.group(3).lower(),
            }
        except (ValueError, IndexError):
            pass

        # If multiple damage types, store as array
        if len(damage_matches) > 1:
            all_damages = []
            for match in damage_matches:
                try:
                    damage_dice = match.group(2).strip()
                    damage_dice = re.sub(r"\s+", "", damage_dice)
                    all_damages.append(
                        {
                            "average": int(match.group(1)),
                            "dice": damage_dice,
                            "type": match.group(3).lower(),
                        }
                    )
                except (ValueError, IndexError):
                    continue
            if len(all_damages) > 1:
                patched["damage_options"] = all_damages

    # Parse saving throw
    save_match = _SAVING_THROW.search(text)
    if save_match:
        try:
            ability = save_match.group(2).lower()
            # Map short forms to full names
            ability_map = {
                "str": "strength",
                "dex": "dexterity",
                "con": "constitution",
                "int": "intelligence",
                "wis": "wisdom",
                "cha": "charisma",
            }
            ability = ability_map.get(ability, ability)

            patched["saving_throw"] = {
                "dc": int(save_match.group(1)),
                "ability": ability,
            }
        except (ValueError, IndexError):
            pass

    return patched
