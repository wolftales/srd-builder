"""Reading module-supplied statblocks out of a publication appendix.

Split deliberately at the lens boundary. Everything here is source-specific: it
knows this publisher's typography and turns it into a raw payload. Turning that
payload into a schema-shaped record is the selected ruleset lens's job, and the
lens already exists - `parse.parse_monsters.normalize_monster` - so a module
supplement and an SRD monster go through exactly the same normalization (D2).
"""

from __future__ import annotations

import re
from typing import Any

from srd_builder.module_import.profile import (
    STATBLOCK_ABILITY_HEADER,
    STATBLOCK_ABILITY_VALUE,
    STATBLOCK_BODY,
    STATBLOCK_ENTRY_NAME,
    STATBLOCK_LABELLED,
    STATBLOCK_META,
    STATBLOCK_NAME,
    STATBLOCK_SECTION,
    SourceProfile,
)
from srd_builder.module_import.spine import slugify

_ABILITIES = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
_ABBREVIATIONS = {"STR": 0, "DEX": 1, "CON": 2, "INT": 3, "WIS": 4, "CHA": 5}

# The publication sets negative modifiers with an en dash, not a hyphen.
_MINUS = "–−-"
_ABILITY_VALUE = re.compile(rf"^(?P<value>\d+)\s*\(\s*(?P<sign>[+{_MINUS}])?\s*(?P<mod>\d+)\s*\)$")
_DISTANCE = re.compile(r"(?P<value>\d+)\s*(?:ft|feet)\b", re.IGNORECASE)
_PASSIVE = re.compile(r"passive\s+perception\s+(?P<value>\d+)", re.IGNORECASE)
_ENTRY_SPLIT = re.compile(r"^(?P<name>.+?)\.\s+(?P<rest>.*)$", re.DOTALL)

#: Labelled statblock lines this importer understands. Anything else is kept as
#: an unrecognized label rather than dropped, so the lens can report it.
_LABELS = (
    "Armor Class",
    "Hit Points",
    "Speed",
    "Saving Throws",
    "Skills",
    "Damage Resistances",
    "Damage Immunities",
    "Damage Vulnerabilities",
    "Condition Immunities",
    "Senses",
    "Languages",
    "Challenge",
)


def appendix_page_range(toc: Any, profile: SourceProfile, page_count: int) -> tuple[int, int]:
    """The 0-based page span of the statblock appendix, inclusive.

    Bounded by outline LEVEL, not by the next entry on a later page: the
    appendix's own children are creature names on later pages, so a page-only
    boundary stops at the second statblock and silently drops the rest.
    """
    pattern = re.compile(profile.appendix_pattern)
    start_at = next((i for i, entry in enumerate(toc) if pattern.match(entry.title)), None)
    if start_at is None:
        raise ValueError("publication outline names no statblock appendix")

    opening = toc[start_at]
    for entry in toc[start_at + 1 :]:
        if entry.level <= opening.level:
            return opening.page - 1, max(opening.page - 1, entry.page - 2)
    return opening.page - 1, page_count - 1


def role_of(line: dict[str, Any], profile: SourceProfile) -> str | None:
    return profile.statblock_roles.get((line["font"], line["size"]))


def split_statblocks(
    lines: list[dict[str, Any]], profile: SourceProfile
) -> list[list[dict[str, Any]]]:
    """Group appendix lines into one run per creature."""
    runs: list[list[dict[str, Any]]] = []
    for line in lines:
        if role_of(line, profile) == STATBLOCK_NAME:
            runs.append([line])
        elif runs:
            runs[-1].append(line)
    return runs


def _split_label(text: str) -> tuple[str, str] | None:
    for label in _LABELS:
        if text.startswith(label):
            return label, text[len(label) :].strip()
    return None


def _parse_ability_value(text: str) -> dict[str, int] | None:
    match = _ABILITY_VALUE.match(text.strip())
    if not match:
        return None
    modifier = int(match.group("mod"))
    if match.group("sign") and match.group("sign") in _MINUS:
        modifier = -modifier
    return {"value": int(match.group("value")), "modifier": modifier}


def _parse_speed(text: str) -> dict[str, int]:
    speeds: dict[str, int] = {}
    for raw_part in text.split(","):
        part = raw_part.strip()
        distance = _DISTANCE.search(part)
        if not distance:
            continue
        mode = part[: distance.start()].strip().lower() or "walk"
        speeds[slugify(mode) or "walk"] = int(distance.group("value"))
    return speeds


def _parse_senses(text: str) -> dict[str, int]:
    senses: dict[str, int] = {}
    passive = _PASSIVE.search(text)
    # The schema requires passive_perception, so a statblock without one is
    # reported by the validator rather than silently given a default.
    if passive:
        senses["passive_perception"] = int(passive.group("value"))
    for raw_part in text.split(","):
        part = raw_part.strip()
        if part.lower().startswith("passive"):
            continue
        distance = _DISTANCE.search(part)
        if distance:
            name = slugify(part[: distance.start()].strip())
            if name:
                senses[name] = int(distance.group("value"))
    return senses


def _parse_defenses(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for part in re.split(r",| and ", text):
        cleaned = part.strip().rstrip(".")
        if cleaned:
            entries.append({"type": cleaned, "type_id": f"damage:{slugify(cleaned)}"})
    return entries


def _flush_entry(name: str, body: list[str]) -> dict[str, Any]:
    description = " ".join(part.strip() for part in body if part.strip())
    return {
        "name": name,
        "simple_name": slugify(name),
        "description": [description] if description else [name],
    }


def parse_statblock(run: list[dict[str, Any]], profile: SourceProfile) -> dict[str, Any]:
    """One creature's lines into a raw payload for the ruleset lens.

    Produces schema-compliant keys but does not normalize; that is the lens's
    responsibility and is shared with SRD monster extraction.
    """
    raw: dict[str, Any] = {"name": run[0]["text"].strip()}
    ability_order: list[str] = []
    ability_values: list[dict[str, int]] = []
    entries: list[tuple[str, str, list[str]]] = []  # (section, name, body)
    section = "traits"
    pending: tuple[str, list[str]] | None = None

    def close_pending() -> None:
        nonlocal pending
        if pending is not None:
            entries.append((section, pending[0], pending[1]))
            pending = None

    for line in run[1:]:
        role = role_of(line, profile)
        text = line["text"].strip()
        if not text:
            continue

        if role == STATBLOCK_SECTION:
            close_pending()
            section = slugify(text)
        elif role == STATBLOCK_META:
            raw["meta_line"] = text
        elif role == STATBLOCK_ABILITY_HEADER:
            close_pending()
            if text.upper() in _ABBREVIATIONS:
                ability_order.append(text.upper())
        elif role == STATBLOCK_ABILITY_VALUE:
            parsed = _parse_ability_value(text)
            if parsed is not None:
                ability_values.append(parsed)
        elif role == STATBLOCK_LABELLED:
            close_pending()
            split = _split_label(text)
            if split is not None:
                raw.setdefault("_labels", {})[split[0]] = split[1]
            else:
                # A bold line that is not a known label starts a trait whose name
                # runs into its body, e.g. an entry name set in bold.
                match = _ENTRY_SPLIT.match(text)
                if match:
                    pending = (match.group("name").strip(), [match.group("rest")])
        elif role == STATBLOCK_ENTRY_NAME:
            close_pending()
            match = _ENTRY_SPLIT.match(text)
            pending = (match.group("name").strip(), [match.group("rest")]) if match else (text, [])
        elif role == STATBLOCK_BODY and pending is not None:
            pending[1].append(text)
        elif role == STATBLOCK_BODY and "_labels" in raw:
            # Continuation of a wrapped labelled line.
            last = list(raw["_labels"])[-1]
            raw["_labels"][last] = f"{raw['_labels'][last]} {text}".strip()

    close_pending()

    labels: dict[str, str] = raw.pop("_labels", {})
    if "Armor Class" in labels:
        value = re.match(r"\d+", labels["Armor Class"])
        if value:
            raw["armor_class"] = {"value": int(value.group())}
    if "Hit Points" in labels:
        raw["hit_points"] = labels["Hit Points"]
    if "Speed" in labels:
        raw["speed"] = _parse_speed(labels["Speed"])
    if "Senses" in labels:
        raw["senses"] = _parse_senses(labels["Senses"])
    for label, key in (
        ("Damage Resistances", "damage_resistances"),
        ("Damage Immunities", "damage_immunities"),
        ("Damage Vulnerabilities", "damage_vulnerabilities"),
    ):
        if label in labels:
            raw[key] = _parse_defenses(labels[label])
    if "Condition Immunities" in labels:
        raw["condition_immunities"] = [
            {"name": part.strip(), "condition_id": f"condition:{slugify(part)}"}
            for part in labels["Condition Immunities"].split(",")
            if part.strip()
        ]

    if len(ability_order) == len(ability_values) == len(_ABILITIES):
        raw["ability_scores"] = {
            _ABILITIES[_ABBREVIATIONS[abbrev]]: value
            for abbrev, value in zip(ability_order, ability_values, strict=True)
        }

    raw["actions"] = [_flush_entry(name, body) for sec, name, body in entries if sec == "actions"]
    traits = [_flush_entry(name, body) for sec, name, body in entries if sec != "actions"]
    if traits:
        raw["traits"] = traits
    return raw
