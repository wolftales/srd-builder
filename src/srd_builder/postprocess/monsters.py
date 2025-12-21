"""Postprocessing helpers specific to monster statblocks."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from .ids import normalize_id
from .text import polish_text_fields

__all__ = [
    "add_ability_modifiers",
    "clean_monster_record",
    "dedup_defensive_lists",
    "parse_action_structures",
    "prune_empty_fields",
    "rename_abilities_to_traits",
    "split_legendary",
    "standardize_challenge",
    "structure_defenses",
    "unify_simple_name",
]


_LEGENDARY_HEADER_RE = re.compile(r"can take\s+(?:\w+\s+)?legendary actions", re.IGNORECASE)


def _copy_entries(entries: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [{**entry} for entry in entries or []]


def unify_simple_name(monster: dict[str, Any]) -> dict[str, Any]:
    """Ensure IDs and nested records use a consistent normalized identifier."""

    patched = {**monster}
    patched_name = str(patched.get("name", "")).rstrip(".")
    if patched_name:
        patched["name"] = patched_name

    base_simple = patched.get("simple_name") or patched.get("name", "")
    simple_name = normalize_id(str(base_simple))
    if simple_name:
        patched["simple_name"] = simple_name
        existing_id = patched.get("id", "")
        if existing_id and ":" in existing_id:
            prefix = existing_id.split(":")[0]
            patched["id"] = f"{prefix}:{simple_name}"
        else:
            patched["id"] = f"monster:{simple_name}"

    for key in ("abilities", "traits", "actions", "legendary_actions", "reactions"):
        if key not in monster:
            continue
        entries: list[dict[str, Any]] = []
        for entry in monster.get(key, []):
            if not isinstance(entry, dict):
                entries.append(entry)
                continue
            item = {**entry}
            name = item.get("name")
            if isinstance(name, str):
                item["name"] = name.rstrip(".")
                item["simple_name"] = normalize_id(item.get("simple_name", name))
            entries.append(item)
        patched[key] = entries

    return patched


def rename_abilities_to_traits(monster: dict[str, Any]) -> dict[str, Any]:
    """Rename legacy ability fields to the canonical trait structure."""

    patched = {**monster}
    if "abilities" in monster and "traits" not in monster:
        patched["traits"] = _copy_entries(monster.get("abilities"))
        patched.pop("abilities", None)

    for key in ("traits", "actions", "legendary_actions"):
        if key not in monster:
            continue
        converted: list[dict[str, Any]] = []
        for entry in monster.get(key, []):
            if not isinstance(entry, dict):
                converted.append(entry)
                continue
            item = {**entry}
            if "description" in item and "text" not in item:
                item["text"] = item.pop("description")
            converted.append(item)
        patched[key] = converted

    return patched


def _contains_legendary_header(text: str) -> bool:
    return bool(text and _LEGENDARY_HEADER_RE.search(text))


def _is_legendary_action(entry: dict[str, Any]) -> bool:
    name = entry.get("name", "").lower()
    text = entry.get("text", "").lower()
    if "legendary action" in name or "legendary action" in text:
        return True
    if "(cost" in name:
        return True
    return False


def split_legendary(monster: dict[str, Any]) -> dict[str, Any]:
    """Move legendary actions from the main action list into their own field."""

    patched = {**monster}
    actions = _copy_entries(monster.get("actions"))
    regular: list[dict[str, Any]] = []
    legendary: list[dict[str, Any]] = _copy_entries(monster.get("legendary_actions"))
    seen_header = False

    for action in actions:
        text = action.get("text", "")
        if not seen_header and _contains_legendary_header(text):
            seen_header = True
            regular.append(action)
            continue
        if seen_header or _is_legendary_action(action):
            legendary.append(action)
        else:
            regular.append(action)

    patched["actions"] = regular
    if legendary:
        patched["legendary_actions"] = legendary
    elif "legendary_actions" in patched:
        patched["legendary_actions"] = []

    return patched


def _extract_damage_qualifier(segment: str) -> tuple[str, str | None]:
    working = segment
    qualifier: str | None = None
    lowered = working.lower()

    if "from nonmagical" in lowered:
        qualifier = "nonmagical"
        working = re.sub(
            r"\s+from\s+nonmagical\s+attacks?(?:\s+that\s+aren't\s+\w+)?",
            "",
            working,
            flags=re.IGNORECASE,
        )
    elif "that aren't" in lowered:
        match = re.search(r"that\s+aren't\s+(\w+)", working, flags=re.IGNORECASE)
        if match:
            allowed_qualifiers = {"magical", "silvered", "adamantine"}
            matched_word = match.group(1).lower()
            if matched_word in allowed_qualifiers:
                qualifier = f"not_{matched_word}"
        working = re.sub(r"\s+that\s+aren't\s+\w+", "", working, flags=re.IGNORECASE)
    elif "while in" in lowered:
        match = re.search(r"while\s+in\s+(.+)$", working, flags=re.IGNORECASE)
        if match:
            qualifier = f"in_{match.group(1).strip().lower().replace(' ', '_')}"
        working = re.sub(r"\s+while\s+in\s+.+$", "", working, flags=re.IGNORECASE)

    return working, qualifier


def _split_damage_types(segment: str) -> list[str]:
    return [part.strip() for part in re.split(r",|\band\b", segment) if part.strip()]


def normalize_damage_list(damage_str: str) -> list[dict[str, str]]:
    """Convert resistance/immunity strings to structured dictionaries."""

    if not damage_str:
        return []

    entries: list[dict[str, str]] = []
    segments = [segment.strip() for segment in damage_str.split(";") if segment.strip()]

    for segment in segments:
        cleaned_segment, qualifier = _extract_damage_qualifier(segment)
        for part in _split_damage_types(cleaned_segment):
            entry: dict[str, str] = {"type": part.lower()}
            if qualifier:
                entry["qualifier"] = qualifier
            entries.append(entry)

    return entries


def structure_defenses(monster: dict[str, Any]) -> dict[str, Any]:
    """Normalize damage and condition defenses into structured dictionaries."""

    patched = {**monster}
    for key in ("damage_resistances", "damage_immunities", "damage_vulnerabilities"):
        value = monster.get(key)
        if not value:
            patched[key] = []
            continue
        structured: list[dict[str, str]] = []
        for entry in value:
            if isinstance(entry, dict):
                normalized = {k: v for k, v in entry.items() if k in {"type", "qualifier"}}
                if "type" in normalized and isinstance(normalized["type"], str):
                    normalized["type"] = normalized["type"].lower()
                    structured.append(normalized)
            elif isinstance(entry, str):
                structured.extend(normalize_damage_list(entry))
        patched[key] = structured

    condition_value = monster.get("condition_immunities")
    if condition_value:
        patched["condition_immunities"] = [
            entry if isinstance(entry, dict) else {"type": str(entry).strip().lower()}
            for entry in condition_value
            if str(entry).strip()
        ]
    else:
        patched["condition_immunities"] = []

    return patched


def _normalize_challenge(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        if "/" in value:
            num, denom = value.split("/", 1)
            try:
                return float(num) / float(denom)
            except (ValueError, ZeroDivisionError):
                return value
        try:
            as_float = float(value)
        except ValueError:
            return value
        return int(as_float) if as_float.is_integer() else as_float
    if isinstance(value, float):
        return int(value) if value.is_integer() else value
    return value


def standardize_challenge(monster: dict[str, Any]) -> dict[str, Any]:
    """Standardize the challenge rating representation."""

    patched = {**monster}
    patched["challenge_rating"] = _normalize_challenge(patched.get("challenge_rating"))
    return patched


def add_ability_modifiers(monster: dict[str, Any]) -> dict[str, Any]:
    """Add calculated ability score modifiers for convenience."""

    patched = {**monster}
    ability_scores = patched.get("ability_scores")

    if not isinstance(ability_scores, dict):
        return patched

    updated_scores = {**ability_scores}

    for ability, score in ability_scores.items():
        if not isinstance(score, int):
            continue
        modifier = (score - 10) // 2
        modifier_key = f"{ability}_modifier"
        updated_scores[modifier_key] = modifier

    patched["ability_scores"] = updated_scores
    return patched


def parse_action_structures(monster: dict[str, Any]) -> dict[str, Any]:
    """Parse structured fields from action text."""

    from srd_builder.parse.parse_actions import parse_action_fields

    patched = {**monster}

    for key in ("actions", "legendary_actions", "reactions"):
        if key not in monster:
            continue
        parsed_entries: list[dict[str, Any]] = []
        for entry in monster.get(key, []):
            if not isinstance(entry, dict):
                parsed_entries.append(entry)
                continue
            parsed_entries.append(parse_action_fields(entry))
        patched[key] = parsed_entries

    return patched


def _dedup_list_of_dicts(
    items: Iterable[dict[str, Any]] | None, *, key: str
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for entry in items or []:
        if not isinstance(entry, dict):
            deduped.append(entry)
            continue
        item = {**entry}
        raw_type = item.get(key)
        if not isinstance(raw_type, str):
            deduped.append(item)
            continue
        normalized_type = raw_type.strip().lower()
        if not normalized_type:
            deduped.append(item)
            continue
        raw_qualifier = item.get("qualifier", "")
        qualifier = str(raw_qualifier).strip().lower() if raw_qualifier is not None else ""
        signature = (normalized_type, qualifier)
        if signature in seen:
            continue
        seen.add(signature)
        item[key] = normalized_type
        if qualifier:
            item["qualifier"] = qualifier
        elif "qualifier" in item:
            item.pop("qualifier")
        deduped.append(item)
    return deduped


def dedup_defensive_lists(monster: dict[str, Any]) -> dict[str, Any]:
    """Deduplicate defensive entries case-insensitively while preserving order."""

    patched = {**monster}
    for key in ("damage_resistances", "damage_immunities", "damage_vulnerabilities"):
        value = monster.get(key)
        if isinstance(value, list):
            patched[key] = _dedup_list_of_dicts(value, key="type")
    value = monster.get("condition_immunities")
    if isinstance(value, list):
        patched["condition_immunities"] = _dedup_list_of_dicts(value, key="type")
    return patched


_OPTIONAL_ARRAY_FIELDS = {
    "traits",
    "reactions",
    "legendary_actions",
    "condition_immunities",
    "damage_resistances",
    "damage_immunities",
    "damage_vulnerabilities",
}


def prune_empty_fields(monster: dict[str, Any]) -> dict[str, Any]:
    """Remove empty optional arrays or strings from monster records."""

    patched = {**monster}
    for key, value in list(patched.items()):
        if key in _OPTIONAL_ARRAY_FIELDS and isinstance(value, list) and not value:
            patched.pop(key)
            continue
        if isinstance(value, str) and not value.strip():
            patched.pop(key)
    return patched


def clean_monster_record(monster: dict[str, Any]) -> dict[str, Any]:
    """Run the canonical post-processing pipeline over a monster record."""

    pipeline = (
        unify_simple_name,
        rename_abilities_to_traits,
        split_legendary,
        structure_defenses,
        standardize_challenge,
        add_ability_modifiers,
        parse_action_structures,
        polish_text_fields,
        dedup_defensive_lists,
        prune_empty_fields,
    )

    patched = monster
    for step in pipeline:
        patched = step(patched)
    return patched
