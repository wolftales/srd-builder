from __future__ import annotations

"""Pure post-processing utilities for normalized monster records."""

from copy import deepcopy
import re
from typing import Any, Iterable

__all__ = [
    "normalize_id",
    "unify_simple_name",
    "rename_abilities_to_traits",
    "split_legendary",
    "structure_defenses",
    "standardize_challenge",
    "polish_text",
    "polish_text_fields",
]


_ID_CLEAN_RE = re.compile(r"[^0-9a-z_]+")
_LEGENDARY_HEADER_RE = re.compile(
    r"can take\s+(?:\w+\s+)?legendary actions", re.IGNORECASE
)
_LEGENDARY_SENTENCES = [
    re.compile(r"The [^.]+ can take [^.]+ legendary actions[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"Only one legendary action option can be used at a time\.\s*", re.IGNORECASE),
    re.compile(r"The [^.]+ regains spent legendary actions[^.]*\.\s*", re.IGNORECASE),
]


def normalize_id(value: str) -> str:
    """Normalize arbitrary text into a lowercase underscore identifier."""

    simplified = value.strip().lower()
    simplified = simplified.replace("-", "_").replace(" ", "_")
    simplified = _ID_CLEAN_RE.sub("", simplified)
    simplified = re.sub(r"_+", "_", simplified)
    return simplified.strip("_")


def _copy_entries(entries: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [deepcopy(entry) for entry in entries or []]


def unify_simple_name(monster: dict[str, Any]) -> dict[str, Any]:
    """Ensure IDs and nested records use a consistent normalized identifier."""

    patched = deepcopy(monster)
    patched_name = patched.get("name", "").rstrip(".")
    if patched_name:
        patched["name"] = patched_name
    simple_name = normalize_id(patched.get("name", patched.get("simple_name", "")))
    if simple_name:
        patched["simple_name"] = simple_name
        patched["id"] = f"monster:{simple_name}"

    for key in ("abilities", "traits", "actions", "legendary_actions"):
        if key not in patched:
            continue
        entries: list[dict[str, Any]] = []
        for entry in patched.get(key, []):
            item = deepcopy(entry)
            name = item.get("name")
            if isinstance(name, str):
                item["name"] = name.rstrip(".")
                item["simple_name"] = normalize_id(name)
            entries.append(item)
        patched[key] = entries

    return patched


def rename_abilities_to_traits(monster: dict[str, Any]) -> dict[str, Any]:
    """Rename legacy ability fields to the canonical trait structure."""

    patched = deepcopy(monster)
    if "abilities" in patched and "traits" not in patched:
        patched["traits"] = _copy_entries(patched.get("abilities"))
        patched.pop("abilities", None)

    for key in ("traits", "actions", "legendary_actions"):
        if key not in patched:
            continue
        converted: list[dict[str, Any]] = []
        for entry in patched[key]:
            item = deepcopy(entry)
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

    patched = deepcopy(monster)
    actions = _copy_entries(patched.get("actions"))
    regular: list[dict[str, Any]] = []
    legendary: list[dict[str, Any]] = _copy_entries(patched.get("legendary_actions"))
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


def normalize_damage_list(damage_str: str) -> list[dict[str, str]]:
    """Convert resistance/immunity strings to structured dictionaries."""

    if not damage_str:
        return []

    segments = [segment.strip() for segment in damage_str.split(";") if segment.strip()]
    entries: list[dict[str, str]] = []

    for segment in segments:
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
                qualifier = f"not_{match.group(1).lower()}"
                working = re.sub(r"\s+that\s+aren't\s+\w+", "", working, flags=re.IGNORECASE)
        elif "while in" in lowered:
            match = re.search(r"while\s+in\s+(.+)$", working, flags=re.IGNORECASE)
            if match:
                qualifier = f"in_{match.group(1).strip().lower().replace(' ', '_')}"
                working = re.sub(r"\s+while\s+in\s+.+$", "", working, flags=re.IGNORECASE)

        parts = [p.strip() for p in re.split(r",|\band\b", working) if p.strip()]
        for part in parts:
            entry: dict[str, str] = {"type": part.lower()}
            if qualifier:
                entry["qualifier"] = qualifier
            entries.append(entry)

    return entries


def structure_defenses(monster: dict[str, Any]) -> dict[str, Any]:
    """Normalize damage and condition defenses into structured dictionaries."""

    patched = deepcopy(monster)
    for key in ("damage_resistances", "damage_immunities", "damage_vulnerabilities"):
        value = patched.get(key)
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

    condition_value = patched.get("condition_immunities")
    if condition_value:
        patched["condition_immunities"] = [
            entry
            if isinstance(entry, dict)
            else {"type": str(entry).strip().lower()}
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

    patched = deepcopy(monster)
    patched["challenge_rating"] = _normalize_challenge(patched.get("challenge_rating"))
    return patched


def polish_text(text: str | None) -> str | None:
    """Clean OCR artifacts, spacing, and boilerplate from text fields."""

    if text is None:
        return None

    cleaned = text
    for pattern in _LEGENDARY_SENTENCES:
        cleaned = pattern.sub("", cleaned)

    cleaned = re.sub(r"--+", "-", cleaned)
    cleaned = re.sub(r"\bH\s*it\b", "Hit", cleaned)
    cleaned = re.sub(r"Hit:\s*(\d)", r"Hit: \1", cleaned)
    cleaned = re.sub(r"(\d+d\d+)\s*([+-])\s*(\d+)", r"\1\2\3", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"([.!?])([A-Z])", r"\1 \2", cleaned)
    cleaned = cleaned.strip()
    return cleaned


def polish_text_fields(monster: dict[str, Any]) -> dict[str, Any]:
    """Apply :func:`polish_text` to summary, traits, actions, and legendary actions."""

    patched = deepcopy(monster)

    if "summary" in patched and isinstance(patched["summary"], str):
        patched["summary"] = polish_text(patched["summary"]) or ""

    for key in ("traits", "actions", "legendary_actions"):
        if key not in patched:
            continue
        formatted: list[dict[str, Any]] = []
        for entry in patched[key]:
            item = deepcopy(entry)
            if "text" in item:
                polished = polish_text(item["text"])
                if polished is not None:
                    item["text"] = polished
            if "name" in item and isinstance(item["name"], str):
                item["name"] = item["name"].rstrip(".")
            formatted.append(item)
        patched[key] = formatted

    return patched

