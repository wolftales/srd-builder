"""Utilities for normalizing raw SRD monster payloads."""

from __future__ import annotations

import re
from collections.abc import Iterable
from copy import deepcopy
from typing import Any

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
_XP_RE = re.compile(r"([\d,]+)\s*XP", re.IGNORECASE)


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


def _normalize_speed(raw_speed: Any) -> dict[str, int]:
    if isinstance(raw_speed, str):
        normalized: dict[str, int] = {}
        for match in _SPEED_PATTERN.finditer(raw_speed):
            mode = match.group("mode") or "walk"
            normalized[mode.strip().lower().replace(" ", "_")] = int(match.group("value"))
        return normalized
    if not isinstance(raw_speed, dict):
        return {}
    normalized: dict[str, int] = {}
    for mode, value in raw_speed.items():
        coerced = _coerce_int(value)
        if coerced is not None:
            normalized[str(mode).strip().lower().replace(" ", "_")] = coerced
    return normalized


def _normalize_defense_entries(value: Any) -> list[Any]:
    if not value:
        return []
    if isinstance(value, list | tuple):
        return [deepcopy(entry) for entry in value]
    return [str(value)]


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
    if not raw_senses:
        return {}
    if isinstance(raw_senses, dict):
        return _normalize_sense_mapping(raw_senses)

    senses: dict[str, int] = {}
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
    for source in (monster.get("xp"), monster.get("xp_value"), monster.get("challenge")):
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

    ability_scores = _expand_scores(monster.get("ability_scores"))
    saving_throws = _expand_proficiencies(monster.get("saving_throws"))
    skills = _expand_proficiencies(monster.get("skills"))
    senses = _normalize_senses(monster.get("senses"))

    simple_name = _infer_simple_name(monster)
    challenge_value = _parse_challenge_value(monster.get("challenge_rating"))

    raw_hp = monster.get("hit_points")
    hit_points, hit_dice_text = _parse_hit_point_values(raw_hp, monster.get("hit_dice"))

    monster_id = monster.get("id")
    armor_class_value = _coerce_int(monster.get("armor_class")) or 0

    normalized = {
        "id": str(monster_id) if monster_id else f"monster:{simple_name}",
        "simple_name": simple_name,
        "name": str(monster.get("name", "")),
        "summary": str(monster.get("summary", "")),
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
        "actions": _normalize_list_of_dicts(monster.get("actions")),
        "legendary_actions": _normalize_list_of_dicts(monster.get("legendary_actions")),
        "challenge_rating": challenge_value,
        "xp_value": _extract_xp_value(monster),
        "senses": senses,
        "damage_resistances": _normalize_defense_entries(monster.get("damage_resistances")),
        "damage_immunities": _normalize_defense_entries(monster.get("damage_immunities")),
        "damage_vulnerabilities": _normalize_defense_entries(monster.get("damage_vulnerabilities")),
        "condition_immunities": _normalize_defense_entries(monster.get("condition_immunities")),
        "page": _coerce_int(monster.get("page")) or 0,
        "src": str(monster.get("src", "")),
    }

    return normalized


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
        if "Italic" in font and i <= 2:
            parsed.update(_parse_size_type_alignment(text))
            i += 1
            continue

        # Check for stat block labels (Bold text)
        if "Bold" in font:
            # Clean label text: normalize whitespace
            label_clean = " ".join(text.split()).lower()

            # Get next block value (usually)
            next_block = blocks[i + 1] if i + 1 < len(blocks) else None
            next_text = next_block.get("text", "").strip() if next_block else ""

            if "armor class" in label_clean:
                # TODO v0.4.0: Parse structured AC with source
                # e.g., "17 (natural armor)" -> {"value": 17, "source": "natural armor"}
                # Schema already supports object type for armor_class
                parsed["armor_class"] = next_text
                i += 2
                continue

            if "hit points" in label_clean:
                # TODO v0.4.0: Parse structured HP with dice formula
                # e.g., "135 (18d10 + 36)" -> {"average": 135, "formula": "18d10+36"}
                # Schema already supports object type for hit_points
                parsed["hit_points"] = next_text
                i += 2
                continue

            if label_clean == "speed":
                parsed["speed"] = next_text
                i += 2
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

                # Next block should have values
                if j < len(blocks):
                    values_text = blocks[j].get("text", "")
                    ability_scores = _parse_ability_scores(values_text)
                    if ability_scores:
                        # Use schema key "ability_scores" directly (not legacy "stats")
                        parsed["ability_scores"] = ability_scores
                    i = j + 1
                    continue

        i += 1

    return parsed


def _parse_size_type_alignment(text: str) -> dict[str, Any]:
    """Parse 'Large aberration, lawful evil' line."""
    # Clean whitespace/tabs
    text = " ".join(text.split())

    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 2:
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

    if len(scores) != 6:
        return {}

    return {
        "str": scores[0],
        "dex": scores[1],
        "con": scores[2],
        "int": scores[3],
        "wis": scores[4],
        "cha": scores[5],
    }


def parse_monster_records(monsters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a list of raw monster dictionaries."""

    # First parse blocks into fields (v0.3.0 format), then normalize
    parsed = [parse_monster_from_blocks(monster) for monster in monsters]
    return [normalize_monster(monster) for monster in parsed]
