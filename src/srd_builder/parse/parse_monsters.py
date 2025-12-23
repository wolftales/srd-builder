"""Utilities for normalizing raw SRD monster payloads."""

from __future__ import annotations

import re
from collections.abc import Iterable
from copy import deepcopy
from typing import Any

from ..postprocess import normalize_id
from ..postprocess.text import clean_text
from . import parse_actions

__all__ = ["normalize_monster", "parse_monster_records", "parse_monster_from_blocks"]

_ABILITY_MAP = {
    "str": "strength",
    "dex": "dexterity",
    "con": "constitution",
    "int": "intelligence",
    "wis": "wisdom",
    "cha": "charisma",
}

_DISTANCE_RE = re.compile(r"(?P<value>\d+)\s*ft\.?")
_PASSIVE_PERCEPTION_RE = re.compile(r"passive\s+perception\s+(?P<value>\d+)", re.IGNORECASE)
_SENSE_NAME_RE = re.compile(r"^(?P<name>[a-zA-Z ]+?)\s*\d+\s*ft", re.IGNORECASE)
_SPEED_PATTERN = re.compile(r"(?:(?P<mode>[a-z ]+)\s+)?(?P<value>\d+)\s*ft\.?", re.IGNORECASE)
_SPEED_WITH_CONDITION = re.compile(
    r"(?:(?P<mode>[a-z ]+)\s+)?(?P<value>\d+)\s*ft\.?\s*(?:\((?P<condition>[^)]+)\))?",
    re.IGNORECASE,
)
_XP_RE = re.compile(r"([\d,]+)\s*XP", re.IGNORECASE)

# PDF extraction constants
_MIN_BODY_TEXT_SIZE = 9.0  # Minimum font size for body text (Calibri 9pt-10pt)
_MAX_BODY_TEXT_SIZE = 10.0  # Maximum font size for body text
_SECTION_HEADER_SIZE = 10.8  # Font size for section headers (Actions, Traits, etc.)
_TRAIT_NAME_SIZE = 9.5  # Font size for trait/action names (BoldItalic)
_MAX_BLOCKS_AFTER_NAME = 2  # Maximum blocks to check after monster name for size/type/alignment
_MAX_LABEL_CONTINUATION_LENGTH = 6  # Maximum characters for split label words (e.g., "Sense" + "s")
_MAX_VALUE_BLOCKS = 6  # Maximum blocks to collect for multi-block values
_EXPECTED_ABILITY_SCORES = 6  # Number of ability scores (STR, DEX, CON, INT, WIS, CHA)
_MIN_SIZE_TYPE_PARTS = 2  # Minimum comma-separated parts in size/type/alignment line


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return int(value)
    stripped = str(value).strip()
    if not stripped:
        return None
    if "(" in stripped:
        stripped = stripped.split("(", 1)[0].strip()
    if "/" in stripped:
        return None
    stripped = stripped.replace(",", "")
    match = re.search(r"-?\d+", stripped)
    if match:
        try:
            return int(match.group())
        except ValueError:
            return None
    return None


def _expand_scores(raw_scores: dict[str, Any] | None) -> dict[str, int]:
    if not raw_scores:
        return {}
    expanded: dict[str, int] = {}
    for short, full in _ABILITY_MAP.items():
        score = raw_scores.get(short)
        coerced = _coerce_int(score)
        if coerced is not None:
            expanded[full] = coerced
    return expanded


def _expand_proficiencies(raw_profs: dict[str, Any] | None) -> dict[str, int]:
    if not raw_profs:
        return {}
    expanded: dict[str, int] = {}
    if isinstance(raw_profs, dict):
        items = raw_profs.items()
    else:
        entries: list[tuple[str, Any]] = []
        for part in str(raw_profs).split(","):
            stripped = part.strip()
            if not stripped:
                continue
            match = re.match(r"([A-Za-z ]+)\s*([+-]?\d+)", stripped)
            if match:
                entries.append((match.group(1), match.group(2)))
        items = entries
    for short, bonus in items:
        key = _ABILITY_MAP.get(str(short).strip().lower(), str(short).strip().lower())
        coerced = _coerce_int(bonus)
        if coerced is not None:
            expanded[key] = coerced
    return expanded


def _normalize_list_of_dicts(entries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not entries:
        return []
    return [deepcopy(entry) for entry in entries]


def _normalize_actions(entries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Normalize actions with structured field extraction for v2.0 schema."""
    if not entries:
        return []
    normalized = []
    for action in entries:
        action_copy = deepcopy(action)
        # Apply v2.0 field extraction
        parsed = parse_actions.parse_action_fields(action_copy)
        normalized.append(parsed)
    return normalized


def _normalize_speed(raw_speed: Any) -> dict[str, int | bool | str]:
    """Normalize speed into v2.0 structured format.

    Schema v2.0.0 format: All movement types explicit with integer values (0 for unused).
    Hover is boolean flag. Notes field for conditions.

    Examples:
        "30 ft." -> {"walk": 30, "swim": 0, "fly": 0, "burrow": 0, "climb": 0, "hover": False}
        "walk 30 ft., fly 60 ft." -> {"walk": 30, "swim": 0, "fly": 60, "burrow": 0, "climb": 0, "hover": False}
        "fly 50 ft. (hover)" -> {"walk": 0, "swim": 0, "fly": 50, "burrow": 0, "climb": 0, "hover": True}
        "30 ft., swim 60 ft." -> {"walk": 30, "swim": 60, "fly": 0, "burrow": 0, "climb": 0, "hover": False}
    """
    # Initialize v2.0 structure with all movement types
    speed_obj: dict[str, int | bool | str] = {
        "walk": 0,
        "swim": 0,
        "fly": 0,
        "burrow": 0,
        "climb": 0,
        "hover": False,
    }

    if isinstance(raw_speed, str):
        for match in _SPEED_WITH_CONDITION.finditer(raw_speed):
            mode = match.group("mode") or "walk"
            value = int(match.group("value"))
            condition = match.group("condition")

            mode_key = mode.strip().lower().replace(" ", "_")
            if mode_key in speed_obj:
                speed_obj[mode_key] = value

            # Check for hover condition
            if condition and "hover" in condition.lower():
                speed_obj["hover"] = True

        return speed_obj

    if not isinstance(raw_speed, dict):
        return speed_obj

    # Process dict input (from existing normalized data)
    for mode, value in raw_speed.items():
        mode_key = str(mode).strip().lower().replace(" ", "_")
        if mode_key in ("walk", "swim", "fly", "burrow", "climb"):
            coerced = _coerce_int(value)
            if coerced is not None:
                speed_obj[mode_key] = coerced
        elif mode_key == "hover":
            speed_obj["hover"] = bool(value)

    return speed_obj


def _normalize_defense_entries(value: Any) -> list[Any]:
    """Normalize defense entries for v2.0 schema (resistances, immunities, vulnerabilities).

    Schema v2.0.0 format: [{type: str, type_id: str, conditions: str?}, ...]

    Splits semicolon-separated strings and adds type_id.

    Example:
        "fire" -> [{"type": "fire", "type_id": "fire"}]
        "radiant; bludgeoning, piercing, and slashing from nonmagical attacks" ->
            [{"type": "radiant", "type_id": "radiant"},
             {"type": "bludgeoning, piercing, and slashing from nonmagical attacks",
              "type_id": "bludgeoning", "conditions": "nonmagical"}]
    """
    if not value:
        return []
    if isinstance(value, list | tuple):
        # Already structured - add type_id if missing
        return [_add_type_id_to_defense(deepcopy(entry)) for entry in value]

    # Split semicolon-separated string and create entries
    entries = []
    for part in str(value).split(";"):
        cleaned = " ".join(part.split()).strip()
        if cleaned:
            entry = {"type": cleaned}
            # Extract conditions (e.g., "from nonmagical attacks")
            if " from " in cleaned.lower():
                damage_types, condition = cleaned.split(" from ", 1)
                entry["type"] = damage_types.strip()
                entry["conditions"] = condition.strip()
            # Add type_id (first damage type word)
            entry["type_id"] = _extract_damage_type_id(entry["type"])
            entries.append(entry)
    return entries


def _add_type_id_to_defense(entry: dict[str, Any]) -> dict[str, Any]:
    """Add type_id to defense entry if missing."""
    if "type_id" not in entry and "type" in entry:
        entry["type_id"] = _extract_damage_type_id(entry["type"])
    return entry


def _extract_damage_type_id(damage_type: str) -> str:
    """Extract normalized damage type ID from type string.

    Examples:
        "fire" -> "fire"
        "bludgeoning, piercing, and slashing" -> "bludgeoning"
        "radiant" -> "radiant"
    """
    # Take first word/type from comma-separated list
    first_type = damage_type.split(",")[0].strip()
    # Normalize to lowercase snake_case
    return re.sub(r"[^a-z0-9]+", "_", first_type.lower()).strip("_")


def _normalize_condition_immunities(value: Any) -> list[dict[str, str]]:
    """Normalize condition immunities for v2.0 schema.

    Schema v2.0.0 format: [{name: str, condition_id: str}, ...]

    Example:
        "charmed, frightened" ->
            [{"name": "charmed", "condition_id": "condition:charmed"},
             {"name": "frightened", "condition_id": "condition:frightened"}]
    """
    if not value:
        return []

    # If already structured list of dicts, add condition_id
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return [_add_condition_id(deepcopy(entry)) for entry in value]

    # Parse string format (comma-separated)
    if isinstance(value, str):
        conditions = []
        for condition in value.split(","):
            cleaned = condition.strip()
            if cleaned:
                condition_id = re.sub(r"[^a-z0-9]+", "_", cleaned.lower()).strip("_")
                conditions.append(
                    {
                        "name": cleaned,
                        "condition_id": f"condition:{condition_id}",
                    }
                )
        return conditions

    return []


def _add_condition_id(entry: dict[str, Any]) -> dict[str, str]:
    """Add condition_id to condition entry if missing."""
    if "condition_id" not in entry and "name" in entry:
        name = entry["name"]
        condition_id = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
        entry["condition_id"] = f"condition:{condition_id}"
    # Rename 'type' to 'name' if present (legacy format)
    if "type" in entry and "name" not in entry:
        entry["name"] = entry.pop("type")
    return entry


def _add_sense_entry(senses: dict[str, int], entry: str) -> None:
    passive_match = _PASSIVE_PERCEPTION_RE.search(entry)
    if passive_match:
        senses["passive_perception"] = int(passive_match.group("value"))
    distance_match = _DISTANCE_RE.search(entry)
    name_match = _SENSE_NAME_RE.search(entry)
    if distance_match and name_match:
        sense_name = name_match.group("name").strip().lower().replace(" ", "_")
        senses[sense_name] = int(distance_match.group("value"))


def _normalize_sense_mapping(mapping: dict[Any, Any]) -> dict[str, int]:
    senses: dict[str, int] = {}
    for name, distance in mapping.items():
        coerced = _coerce_int(distance)
        if coerced is not None:
            senses[str(name).lower()] = coerced
    return senses


def _iter_sense_fragments(raw_senses: Any) -> Iterable[str]:
    if isinstance(raw_senses, list | tuple):
        for entry in raw_senses:
            yield from str(entry).split(",")
    else:
        yield from str(raw_senses).split(",")


def _normalize_senses(raw_senses: Any) -> dict[str, int]:
    """Normalize senses into v2.0 structured format.

    Schema v2.0.0 format: All sense types explicit with integer values (0 for unused).

    Examples:
        "darkvision 60 ft., passive Perception 10" -> {"darkvision": 60, "blindsight": 0, "tremorsense": 0, "truesight": 0, "passive_perception": 10}
        "blindsight 120 ft." -> {"darkvision": 0, "blindsight": 120, "tremorsense": 0, "truesight": 0, "passive_perception": 0}
    """
    # Initialize v2.0 structure with all sense types
    senses: dict[str, int] = {
        "darkvision": 0,
        "blindsight": 0,
        "tremorsense": 0,
        "truesight": 0,
        "passive_perception": 0,
    }

    if not raw_senses:
        return senses

    if isinstance(raw_senses, dict):
        # Process dict input (from existing normalized data)
        for key, value in raw_senses.items():
            key_normalized = str(key).strip().lower().replace(" ", "_")
            if key_normalized in senses:
                coerced = _coerce_int(value)
                if coerced is not None:
                    senses[key_normalized] = coerced
        return senses

    # Process string input
    for fragment in _iter_sense_fragments(raw_senses):
        text = str(fragment).strip()
        if text:
            _add_sense_entry(senses, text)

    return senses


def _infer_simple_name(raw: dict[str, Any]) -> str:
    if simple := raw.get("simple_name"):
        return str(simple)
    if identifier := raw.get("id"):
        _, _, slug = str(identifier).partition(":")
        if slug:
            return slug.replace("-", "_")
    if name := raw.get("name"):
        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
    return ""


def _parse_hit_point_values(raw_hp: Any, raw_dice: Any) -> tuple[int, str]:
    dice_text = "" if raw_dice is None else str(raw_dice)
    if raw_hp is None:
        return 0, dice_text
    if isinstance(raw_hp, int | float):
        return int(raw_hp), dice_text
    text = str(raw_hp)
    if not dice_text and "(" in text and ")" in text:
        dice_text = text.split("(", 1)[1].split(")", 1)[0].strip()
    points = _coerce_int(text) or 0
    return points, dice_text


def _parse_armor_class(raw_ac: Any) -> dict[str, Any]:
    """Parse armor class into v2.0 structured format.

    Schema v2.0.0 format: Always return dict with value, type, and type_id.

    Examples:
        "17" -> {"value": 17}
        "17 (natural armor)" -> {"value": 17, "type": "natural armor", "type_id": "natural_armor"}
        "16 (chain mail, shield)" -> {"value": 16, "type": "chain mail, shield", "type_id": "chain_mail"}
    """
    if raw_ac is None:
        return {"value": 0}

    text = str(raw_ac).strip()
    if not text:
        return {"value": 0}

    # Extract value (number before any parenthesis)
    value = _coerce_int(text) or 0

    # Extract type (text in parentheses)
    if "(" in text and ")" in text:
        armor_type = text.split("(", 1)[1].split(")", 1)[0].strip()
        # Create normalized type_id
        type_id = re.sub(r"[^a-z0-9]+", "_", armor_type.lower()).strip("_")
        # Take first word for multi-word types (e.g., "chain mail, shield" -> "chain_mail")
        type_id = type_id.split(",")[0].strip()
        return {"value": value, "type": armor_type, "type_id": type_id}

    # Simple numeric AC (no armor type)
    return {"value": value}


def _parse_hit_points_structured(raw_hp: Any) -> dict[str, Any] | int:
    """Parse hit points into structured format.

    Examples:
        "135" -> {"average": 135}
        "135 (18d10 + 36)" -> {"average": 135, "formula": "18d10+36"}
        "135 (18d10+36)" -> {"average": 135, "formula": "18d10+36"}

    Returns dict with "average" and optionally "formula", or int for simple cases.
    """
    if raw_hp is None:
        return 0

    text = str(raw_hp).strip()
    if not text:
        return 0

    # Extract average (number before any parenthesis)
    average = _coerce_int(text) or 0

    # Extract formula (text in parentheses, normalize spacing)
    if "(" in text and ")" in text:
        formula = text.split("(", 1)[1].split(")", 1)[0].strip()
        # Normalize spacing around operators
        formula = re.sub(r"\s*([+\-])\s*", r"\1", formula)
        return {"average": average, "formula": formula}

    # Simple numeric HP
    return average


def _parse_challenge_value(raw_challenge: Any) -> Any:
    if raw_challenge is None:
        return 0
    if isinstance(raw_challenge, int | float):
        return raw_challenge
    text = str(raw_challenge).strip()
    if not text:
        return 0
    token = text.split()[0]
    return token


def _extract_xp_value(monster: dict[str, Any]) -> int:
    for source in (
        monster.get("xp"),
        monster.get("xp_value"),
        monster.get("challenge"),
        monster.get("challenge_rating"),
    ):
        if not source:
            continue
        if isinstance(source, int | float):
            return int(source)
        match = _XP_RE.search(str(source))
        if match:
            return int(match.group(1).replace(",", ""))
        stripped = str(source).strip()
        if stripped.isdigit():
            return int(stripped)
    return 0


def normalize_monster(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw monster payload into the canonical monster template.

    Expects schema-compliant keys from v0.3.0+ extraction.
    """

    monster = deepcopy(raw)

    # v0.3.0+ parser outputs full key names (strength, dexterity, etc.)
    # If we get short keys (str, dex, etc.), expand them
    raw_abilities = monster.get("ability_scores", {})
    if raw_abilities and any(
        k in raw_abilities for k in ("str", "dex", "con", "int", "wis", "cha")
    ):
        ability_scores = _expand_scores(raw_abilities)
    else:
        ability_scores = dict(raw_abilities) if isinstance(raw_abilities, dict) else {}

    saving_throws = _expand_proficiencies(monster.get("saving_throws"))
    skills = _expand_proficiencies(monster.get("skills"))
    senses = _normalize_senses(monster.get("senses"))

    simple_name = _infer_simple_name(monster)
    challenge_value = _parse_challenge_value(monster.get("challenge_rating"))

    # v0.4.0: Structured AC and HP parsing
    # Support both new keys (armor_class, hit_points) and legacy keys (ac, hp)
    raw_ac = monster.get("armor_class") or monster.get("ac")
    armor_class_value = _parse_armor_class(raw_ac)

    raw_hp = monster.get("hit_points") or monster.get("hp")
    hit_points = _parse_hit_points_structured(raw_hp)

    # Keep hit_dice for backward compatibility (deprecated in favor of HP formula)
    _, hit_dice_text = _parse_hit_point_values(raw_hp, monster.get("hit_dice"))

    monster_id = monster.get("id")

    # Extract summary from first trait's description
    summary = ""
    traits = monster.get("traits", [])
    if traits and isinstance(traits, list) and len(traits) > 0:
        first_trait = traits[0]
        if isinstance(first_trait, dict):
            # Handle both old format (text) and new format (description array)
            description = first_trait.get("description")
            if isinstance(description, list) and description:
                summary = description[0]  # First paragraph
            else:
                # Fallback to text field (legacy format)
                summary = first_trait.get("text", "")

    # Determine ID prefix based on page number
    # - Monsters: pages 261-365 (main monster section)
    # - Creatures: pages 366-394 (Appendix MM-A: Miscellaneous Creatures)
    # - NPCs: pages 395-403 (Appendix MM-B: Nonplayer Characters)
    page = _coerce_int(monster.get("page")) or 0
    if 395 <= page <= 403:
        id_prefix = "npc"
    elif 366 <= page <= 394:
        id_prefix = "creature"
    else:
        id_prefix = "monster"

    normalized = {
        "id": str(monster_id) if monster_id else f"{id_prefix}:{simple_name}",
        "simple_name": simple_name,
        "name": str(monster.get("name", "")),
        "summary": summary,
        "size": str(monster.get("size", "")),
        "type": str(monster.get("type", "")),
        "alignment": str(monster.get("alignment", "")),
        "armor_class": armor_class_value,
        "hit_points": hit_points,
        "hit_dice": hit_dice_text,
        "speed": _normalize_speed(monster.get("speed")),
        "ability_scores": ability_scores,
        "saving_throws": saving_throws,
        "skills": skills,
        "traits": _normalize_list_of_dicts(monster.get("traits")),
        "actions": _normalize_actions(monster.get("actions")),
        "reactions": _normalize_actions(monster.get("reactions")),
        "legendary_actions": _normalize_actions(monster.get("legendary_actions")),
        "challenge_rating": challenge_value,
        "xp_value": _extract_xp_value(monster),
        "senses": senses,
        "damage_resistances": _normalize_defense_entries(monster.get("damage_resistances")),
        "damage_immunities": _normalize_defense_entries(monster.get("damage_immunities")),
        "damage_vulnerabilities": _normalize_defense_entries(monster.get("damage_vulnerabilities")),
        "condition_immunities": _normalize_condition_immunities(
            monster.get("condition_immunities")
        ),
        "languages": monster.get("languages"),
        "page": _coerce_int(monster.get("page")) or 0,
        "src": str(monster.get("src", "")),
    }

    return normalized


def _gather_multiline_value(blocks: list[dict], start_idx: int) -> tuple[str, int]:
    """Gather a value that may span multiple blocks.

    Reads consecutive 9.84pt Calibri (non-bold) blocks until hitting a bold label.
    Cleans whitespace (tabs, newlines, etc.) from each block.
    Returns (joined_text, blocks_consumed).
    """
    parts = []
    idx = start_idx

    while idx < len(blocks):
        block = blocks[idx]
        font = block.get("font", "")
        size = block.get("size", 0)
        text = clean_text(block.get("text", ""))

        # Stop if we hit a bold label (next field)
        if "Bold" in font:
            break

        # Only collect regular text blocks (9.84pt Calibri)
        if (
            text
            and size >= _MIN_BODY_TEXT_SIZE
            and size <= _MAX_BODY_TEXT_SIZE
            and "Calibri" in font
        ):
            # Text already cleaned by clean_text()
            parts.append(text)
            idx += 1
        else:
            break

    combined = " ".join(parts)
    blocks_consumed = idx - start_idx
    return combined, blocks_consumed


def parse_monster_from_blocks(monster: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    """Parse monster fields from blocks array (v0.3.0 extraction format).

    Args:
        monster: Dict with 'name', 'blocks', 'pages', etc.

    Returns:
        Dict with parsed fields ready for normalize_monster()

    Note: Complexity acceptable for initial parser. Will refactor in v0.4.0.
    """
    # If no blocks array, assume legacy format and pass through
    blocks = monster.get("blocks")
    if not blocks:
        return monster

    parsed: dict[str, Any] = {"name": monster.get("name", "")}

    # Add page numbers (take first page)
    pages = monster.get("pages", [])
    if pages:
        parsed["page"] = pages[0]

    # Parse blocks sequentially
    i = 0
    while i < len(blocks):
        block = blocks[i]
        text = block.get("text", "").strip()
        font = block.get("font", "")

        # Skip empty blocks
        if not text:
            i += 1
            continue

        # Size/type/alignment line (Calibri-Italic, right after name)
        # Handle split across multiple Italic blocks (e.g., Kraken, Mummy, Unicorn)
        if "Italic" in font and i <= _MAX_BLOCKS_AFTER_NAME:
            # Collect all consecutive Italic blocks (may be split with comma blocks between)
            italic_parts = [text]
            j = i + 1
            while j < len(blocks) and j < i + 5:  # Safety limit
                next_block = blocks[j]
                next_font = next_block.get("font", "")
                next_text = next_block.get("text", "").strip()

                # Stop at Bold (start of stat block)
                if "Bold" in next_font:
                    break

                # Continue if Italic or if it's just a comma/punctuation
                if "Italic" in next_font:
                    italic_parts.append(next_text)
                    j += 1
                elif next_text in (",", ";"):
                    # Skip punctuation blocks but don't add them
                    j += 1
                else:
                    break

            # Combine parts with comma separator
            combined_text = ", ".join(italic_parts)
            parsed.update(_parse_size_type_alignment(combined_text))
            i = j
            continue

        # Check for stat block labels (Bold text)
        if "Bold" in font:
            # Clean label text: normalize whitespace
            label_clean = " ".join(text.split()).lower()

            # Handle multi-block labels (e.g., "Armor" + "Class 14..." or "Sense" + "s darkvision...")
            # Check if next block continues the label (either Bold or regular text starting with lowercase)
            j = i + 1
            if j < len(blocks):
                peek_block = blocks[j]
                peek_font = peek_block.get("font", "")
                peek_text = peek_block.get("text", "").strip()

                # Case 1: Next block is Bold and looks like label continuation (e.g., "Sense" + "s")
                if "Bold" in peek_font and peek_text and not peek_text[0].isdigit():
                    if len(peek_text) <= _MAX_LABEL_CONTINUATION_LENGTH and not any(
                        c in peek_text for c in "():,"
                    ):
                        label_clean += " " + " ".join(peek_text.split()).lower()
                        j += 1

                # Case 2: Next block is regular text starting with label word (e.g., "Armor" + "Class 14...")
                elif "Bold" not in peek_font and peek_text:
                    # Extract first word from next block
                    first_word = peek_text.split()[0] if peek_text.split() else ""
                    # Common label continuations that aren't Bold
                    if first_word.lower() in ("class", "points", "s"):
                        label_clean += " " + first_word.lower()
                        # The rest of the block is the value
                        remaining = " ".join(peek_text.split()[1:])
                        if remaining:
                            # Value is in the same block as the label continuation
                            next_text = remaining
                            # We consumed label block (i) and the combined block (i+1)
                            # So we should skip to i+2
                            j = i + 2
                        else:
                            # Value is in the next block after the label continuation
                            j = i + 2
                            if j < len(blocks):
                                next_block = blocks[j]
                                next_text = next_block.get("text", "").strip() if next_block else ""
                            else:
                                next_text = ""

            # Get next block value if we haven't already processed it
            if j == i + 1:
                next_block = blocks[j] if j < len(blocks) else None
                next_text = next_block.get("text", "").strip() if next_block else ""

            if "armor class" in label_clean:
                # v0.4.0: Gather full AC text including parentheses
                # e.g., "17 (natural armor)" -> {"value": 17, "source": "natural armor"}
                value, consumed = _gather_multiline_value(blocks, i + 1)
                parsed["armor_class"] = value
                i += 1 + consumed
                continue

            if "hit points" in label_clean:
                # v0.4.0: Gather full HP text including formula
                # e.g., "135 (18d10 + 36)" -> {"average": 135, "formula": "18d10+36"}
                value, consumed = _gather_multiline_value(blocks, i + 1)
                parsed["hit_points"] = value
                i += 1 + consumed
                continue

            if label_clean == "speed":
                parsed["speed"] = next_text
                i = j
                continue

            # Ability scores: STR, DEX, CON, INT, WIS, CHA
            if label_clean in ("str", "dex", "con", "int", "wis", "cha"):
                # Collect all 6 ability headers
                ability_blocks = []
                j = i
                while j < len(blocks) and j < i + 6:
                    ab_block = blocks[j]
                    ab_text = ab_block.get("text", "").strip().lower()
                    if ab_text in ("str", "dex", "con", "int", "wis", "cha"):
                        ability_blocks.append(ab_text)
                        j += 1
                    else:
                        break

                # Gather value blocks (might be split across multiple lines)
                # Continue until we hit a Bold label (next stat block field)
                values_parts = []
                k = j
                while k < len(blocks):
                    val_block = blocks[k]
                    val_font = val_block.get("font", "")
                    val_text = val_block.get("text", "").strip()

                    # Stop at next Bold label
                    if "Bold" in val_font:
                        break

                    # Collect value text
                    if val_text:
                        values_parts.append(val_text)
                    k += 1

                    # Safety: stop after collecting reasonable amount (up to 6 blocks for edge cases)
                    if len(values_parts) >= _MAX_VALUE_BLOCKS:
                        break

                # Parse combined values
                combined_values = " ".join(values_parts)
                ability_scores = _parse_ability_scores(combined_values)
                if ability_scores:
                    # Use schema key "ability_scores" directly (not legacy "stats")
                    parsed["ability_scores"] = ability_scores
                i = k
                continue

            # Saving Throws
            if "saving" in label_clean and "throw" in label_clean:
                parsed["saving_throws"] = next_text
                i = j
                continue

            # Skills
            if label_clean == "skills":
                parsed["skills"] = next_text
                i = j
                continue

            # Senses
            if label_clean in ("senses", "sense s"):
                parsed["senses"] = next_text
                i = j
                continue

            # Languages (optional field, but good to capture)
            if label_clean == "languages":
                value, consumed = _gather_multiline_value(blocks, i + 1)
                parsed["languages"] = value
                i += 1 + consumed
                continue

            # Challenge Rating
            if label_clean == "challenge":
                parsed["challenge_rating"] = next_text
                i += 2
                continue

            # Damage Resistances
            if "damage" in label_clean and "resistance" in label_clean:
                value, consumed = _gather_multiline_value(blocks, i + 1)
                parsed["damage_resistances"] = value
                i += 1 + consumed
                continue

            # Damage Immunities
            if "damage" in label_clean and (
                "immunity" in label_clean or "immunities" in label_clean
            ):
                value, consumed = _gather_multiline_value(blocks, i + 1)
                parsed["damage_immunities"] = value
                i += 1 + consumed
                continue

            # Damage Vulnerabilities
            if "damage" in label_clean and (
                "vulnerability" in label_clean or "vulnerabilities" in label_clean
            ):
                value, consumed = _gather_multiline_value(blocks, i + 1)
                parsed["damage_vulnerabilities"] = value
                i += 1 + consumed
                continue

            # Condition Immunities
            if "condition" in label_clean and (
                "immunity" in label_clean or "immunities" in label_clean
            ):
                value, consumed = _gather_multiline_value(blocks, i + 1)
                parsed["condition_immunities"] = value
                i += 1 + consumed
                continue

        i += 1

    # Parse traits, actions, legendary actions from remaining blocks
    traits, actions, reactions, legendary_actions = _parse_traits_and_actions(blocks)
    if traits:
        parsed["traits"] = traits
    if actions:
        parsed["actions"] = actions
    if reactions:
        parsed["reactions"] = reactions
    if legendary_actions:
        parsed["legendary_actions"] = legendary_actions

    return parsed


def _parse_size_type_alignment(text: str) -> dict[str, Any]:
    """Parse 'Large aberration, lawful evil' line."""
    # Clean whitespace/tabs
    text = " ".join(text.split())

    parts = [p.strip() for p in text.split(",")]
    if len(parts) < _MIN_SIZE_TYPE_PARTS:
        return {}

    # First part: size + type
    size_type = parts[0].split(None, 1)
    size = size_type[0] if len(size_type) > 0 else None
    creature_type = size_type[1] if len(size_type) > 1 else None

    # Rest: alignment
    alignment = ", ".join(parts[1:]).strip()

    return {
        "size": size,
        "type": creature_type,
        "alignment": alignment,
    }


def _parse_ability_scores(text: str) -> dict[str, Any]:
    """Parse '21 (+5)  9 (−1)  15 (+2)  18 (+4)  15 (+2)  18 (+4)' line."""
    # Clean text
    text = " ".join(text.split())

    # Extract numbers before parentheses (the actual scores)
    # Pattern: number followed by optional modifier in parens
    scores = []
    pattern = r"(\d+)\s*\([^)]+\)"
    for match in re.finditer(pattern, text):
        scores.append(int(match.group(1)))

    if len(scores) != _EXPECTED_ABILITY_SCORES:
        return {}

    return {
        "strength": scores[0],
        "dexterity": scores[1],
        "constitution": scores[2],
        "intelligence": scores[3],
        "wisdom": scores[4],
        "charisma": scores[5],
    }


def _segment_description_paragraphs(text_blocks: list[str]) -> list[str]:
    """Segment trait/action description into paragraphs.

    Uses sentence detection and text patterns to identify paragraph breaks.
    Similar to spell description segmentation.

    Args:
        text_blocks: List of text strings from consecutive PDF blocks

    Returns:
        List of paragraph strings
    """
    if not text_blocks:
        return []

    # Join all blocks into full text
    full_text = " ".join(text_blocks)

    # For short descriptions (<300 chars), return as single paragraph
    if len(full_text) < 300:
        return [full_text]

    # Split on sentence boundaries for longer descriptions
    # Look for period followed by capital letter or specific markers
    paragraphs: list[str] = []
    current: list[str] = []

    sentences = []
    # Split on ". " followed by capital letter (sentence boundary)
    parts = re.split(r"(\.\s+)(?=[A-Z])", full_text)
    for i in range(0, len(parts), 2):
        if i < len(parts):
            sentence = parts[i]
            if i + 1 < len(parts):
                sentence += parts[i + 1]  # Re-add the ". "
            sentences.append(sentence.strip())

    # Group sentences into paragraphs by semantic breaks
    for i, sentence in enumerate(sentences):
        current.append(sentence)

        # Detect paragraph breaks:
        # 1. Sentence starts with Unless/However/Additionally (often new paragraph)
        # 2. Sentence is long and next starts with conditional (If the...)
        # 3. Every ~3-4 sentences for very long text
        next_sentence = sentences[i + 1] if i + 1 < len(sentences) else ""

        is_paragraph_break = False
        if next_sentence:
            # Next sentence starts new topic
            if any(
                next_sentence.startswith(w)
                for w in ("Unless", "However", "Additionally", "When the")
            ):
                is_paragraph_break = True
            # Current paragraph getting long (>300 chars)
            elif len(" ".join(current)) > 300:
                is_paragraph_break = True

        if is_paragraph_break and current:
            paragraphs.append(" ".join(current))
            current = []

    # Add final paragraph
    if current:
        paragraphs.append(" ".join(current))

    return paragraphs if paragraphs else [full_text]


def _parse_traits_and_actions(  # noqa: C901
    blocks: list[dict],
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Parse traits, actions, reactions, and legendary actions from blocks.

    Patterns:
    - Trait names: 9.84pt Calibri-BoldItalic ending with period, before "Actions" header
    - Action names: 9.84pt Calibri-BoldItalic ending with period, after "Actions" header
    - Reaction names: 9.84pt Calibri-BoldItalic ending with period, after "Reactions" header
    - Legendary action names: Similar pattern, after "Legendary Actions" header
    - Section headers: 10.8pt Calibri-Bold ("Actions", "Reactions", "Legendary Actions")
    - Text: Multiple 9.84pt Calibri blocks following name

    Returns:
        (traits, actions, reactions, legendary_actions) where each is a list of dicts with
        {name, simple_name, description} (description is array of paragraphs)
    """
    traits = []
    actions = []
    reactions = []
    legendary_actions = []
    current_section = "traits"  # Start before "Actions" header

    i = 0
    while i < len(blocks):
        block = blocks[i]
        # Clean control characters and whitespace
        text = clean_text(block.get("text", ""))
        font = block.get("font", "")
        font_size = block.get("size", 0)

        # Detect section headers
        if font_size >= _SECTION_HEADER_SIZE and "bold" in font.lower():
            if text.lower() == "actions":
                current_section = "actions"
                i += 1
                continue
            elif text.lower() == "reactions":
                current_section = "reactions"
                i += 1
                continue
            elif "legendary" in text.lower() and "actions" in text.lower():
                current_section = "legendary_actions"
                i += 1
                continue

        # Detect trait/action names (BoldItalic with period for traits/actions,
        # or just Bold with period for legendary actions)
        is_bold_italic = "bold" in font.lower() and "italic" in font.lower()
        is_just_bold = "bold" in font.lower() and "italic" not in font.lower()
        is_legendary_section = current_section == "legendary_actions"

        is_name_block = (
            font_size >= _TRAIT_NAME_SIZE
            and text.endswith(".")
            and (is_bold_italic or (is_just_bold and is_legendary_section))
        )

        if is_name_block:
            # Extract name (remove trailing period)
            name = text[:-1].strip()
            simple_name = normalize_id(name)

            # Collect text blocks until next BoldItalic or section header
            description_parts = []
            j = i + 1
            while j < len(blocks):
                next_block = blocks[j]
                next_text = clean_text(next_block.get("text", ""))
                next_font = next_block.get("font", "")
                next_font_size = next_block.get("size", 0)

                # Stop at next name or section header
                next_is_bold_italic = "bold" in next_font.lower() and "italic" in next_font.lower()
                next_is_just_bold = (
                    "bold" in next_font.lower() and "italic" not in next_font.lower()
                )

                # Stop at section header
                if next_font_size >= _SECTION_HEADER_SIZE and "bold" in next_font.lower():
                    break

                # Stop at next BoldItalic name (trait/action)
                if (
                    next_font_size >= _TRAIT_NAME_SIZE
                    and next_is_bold_italic
                    and next_text.endswith(".")
                ):
                    break

                # Stop at next Bold name (legendary action) if in legendary section
                if (
                    next_font_size >= _TRAIT_NAME_SIZE
                    and next_is_just_bold
                    and is_legendary_section
                    and next_text.endswith(".")
                ):
                    break

                # Collect regular text
                if next_text:
                    description_parts.append(next_text)
                j += 1

            # Build entry with paragraph segmentation
            description_paragraphs = _segment_description_paragraphs(description_parts)

            entry = {
                "name": name,
                "simple_name": simple_name,
                "description": description_paragraphs,
            }

            # Add to appropriate section
            if current_section == "traits":
                traits.append(entry)
            elif current_section == "actions":
                actions.append(entry)
            elif current_section == "reactions":
                reactions.append(entry)
            elif current_section == "legendary_actions":
                legendary_actions.append(entry)

            i = j
            continue

        i += 1

    return traits, actions, reactions, legendary_actions


def parse_monster_records(monsters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a list of raw monster dictionaries."""

    # First parse blocks into fields (v0.3.0 format), then normalize
    parsed = [parse_monster_from_blocks(monster) for monster in monsters]
    return [normalize_monster(monster) for monster in parsed]
