"""Utilities for normalizing raw SRD monster payloads."""

from __future__ import annotations

import re
from collections.abc import Iterable
from copy import deepcopy
from typing import Any

__all__ = ["normalize_monster", "parse_monster_records"]

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
    """Map a raw monster payload into the canonical monster template."""

    monster = deepcopy(raw)
    ability_scores = _expand_scores(monster.get("stats"))
    saving_throws = _expand_proficiencies(monster.get("saves"))
    skills = _expand_proficiencies(monster.get("skills"))
    senses = _normalize_senses(monster.get("senses"))

    simple_name = _infer_simple_name(monster)
    challenge_value = _parse_challenge_value(monster.get("cr") or monster.get("challenge"))

    raw_hp = monster.get("hp") if monster.get("hp") is not None else monster.get("hit_points")
    hit_points, hit_dice_text = _parse_hit_point_values(raw_hp, monster.get("hit_dice"))

    normalized = {
        "id": str(monster.get("id", "")),
        "simple_name": simple_name,
        "name": str(monster.get("name", "")),
        "summary": str(monster.get("summary", "")),
        "size": str(monster.get("size", "")),
        "type": str(monster.get("type", "")),
        "alignment": str(monster.get("alignment", "")),
        "armor_class": _coerce_int(monster.get("ac") or monster.get("armor_class")) or 0,
        "hit_points": hit_points,
        "hit_dice": hit_dice_text,
        "speed": _normalize_speed(monster.get("speed")),
        "ability_scores": ability_scores,
        "saving_throws": saving_throws,
        "skills": skills,
        "traits": _normalize_list_of_dicts(monster.get("traits")),
        "actions": _normalize_list_of_dicts(monster.get("actions")),
        "legendary_actions": _normalize_list_of_dicts(monster.get("legendary_actions")),
        "challenge_rating": challenge_value if challenge_value is not None else 0,
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


def parse_monster_records(monsters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a list of raw monster dictionaries."""

    return [normalize_monster(monster) for monster in monsters]
