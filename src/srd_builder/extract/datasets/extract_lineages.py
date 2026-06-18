"""Extract lineage (race) structures from SRD 5.1 PDF pages 3-7.

Replaces the hand-curated ``rulesets/srd_5_1/lineage_targets.py`` (~325
lines, in service since v0.8.0). The "PDF text is corrupted" rationale
on that file was disproven by
[tests/test_pdf_provenance.py::test_lineage_pages_are_extractable_after_whitespace_normalization](../../../tests/test_pdf_provenance.py).

Font fingerprints on pages 3-7 (verified 2026-06-17 against
SRD_CC_v5.1.pdf via PyMuPDF 1.27.x):

- 25.9pt GillSans-SemiBold        — section header "Races" (skip; one match)
- 18.0pt GillSans-SemiBold        — race name (9 matches: Dwarf, Elf,
                                    Halfling, Human, Dragonborn, Gnome,
                                    Half-Elf, Half-Orc, Tiefling)
- 13.9pt GillSans-SemiBold        — "<Race> Traits" subheader (skip)
- 12.0pt GillSans-SemiBold        — subrace name OR (on p.3 only, before
                                    the first race) one of 7 intro labels
                                    (Ability Score Increase, Age, ...);
                                    disambiguated by "race header seen"
- 12.0pt Calibri-Bold             — table header "Draconic Ancestry" (skip)
- 9.8pt  Cambria-BoldItalic + "." — trait header (Darkvision., etc.)
- 9.8pt  Cambria / Cambria-Italic — body text (accumulate)
- 10.8pt G-SB single digit        — page number (skip)
- 10.8pt Calibri                  — "System Reference Document 5.1" (skip)
- 8.9pt  Calibri / Calibri-Bold   — Dragon ancestry table cells (skip)

Output mirrors the legacy ``LINEAGE_DATA`` consumer contract for the
fields ``parse_lineages.py`` + ``parse_features.py`` need:

    {
        "source_pages": "3-7",
        "lineages": [
            {
                "name": "Dwarf",
                "simple_name": "dwarf",
                "page": 3,
                "ability_modifiers": {"constitution": 2},
                "size": "Medium",
                "speed": 25,
                "age": "...",
                "alignment": "...",
                "size_description": "...",
                "languages": ["Common", "Dwarvish"],
                "traits": [{"name": "Darkvision", "text": "..."}, ...],
                "subraces": [
                    {
                        "name": "Hill Dwarf",
                        "simple_name": "hill_dwarf",
                        "ability_modifiers": {"wisdom": 1},
                        "traits": [{"name": "Dwarven Toughness", "text": "..."}],
                    },
                ],
            },
            ...
        ],
    }
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from srd_builder.utils.pdf_probe import normalize_whitespace
from srd_builder.utils.prose import clean_text

LINEAGE_PAGES_PDF_INDICES = range(2, 7)  # SRD pages 3-7 (PDF idx 2-6)

# Trait names that get extracted into structured top-level fields rather
# than left in the `traits` list on the output record.
_STRUCTURAL_TRAIT_NAMES = frozenset(
    {
        "Ability Score Increase",
        "Age",
        "Alignment",
        "Size",
        "Speed",
        "Languages",
    }
)

# Canonical ability-score names; map "Strength" → "strength".
_ABILITIES = ("Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma")
_ABILITY_INCREASE_RE = re.compile(
    rf"Your\s+({'|'.join(_ABILITIES)})\s+score\s+(?:increases|increase)\s+by\s+(\d+)",
    re.IGNORECASE,
)
_SIZE_RE = re.compile(r"your\s+size\s+is\s+(\w+)\.", re.IGNORECASE)
_SPEED_RE = re.compile(r"base\s+walking\s+speed\s+is\s+(\d+)\s+feet")
_LANGUAGES_RE = re.compile(r"You\s+can\s+speak,?\s+read,?\s+and\s+write\s+([^.]+)\.")


def extract_lineages(pdf_path: str | Path) -> dict[str, Any]:
    """Extract all lineages + subraces from the SRD PDF.

    Returns the raw extraction shape (see module docstring). The result
    is JSON-serializable and intended to be written to
    ``rulesets/srd_5_1/raw/lineages_raw.json`` and re-consumed by
    ``parse_lineages.parse_lineages()``.
    """
    pdf_path = Path(pdf_path)
    with fitz.open(str(pdf_path)) as doc:
        records = _walk_lineage_pages(doc)

    lineages = [_finalize_lineage_record(rec) for rec in records]
    return {
        "source_pages": "3-7",
        "lineages": lineages,
    }


# ---------------------------------------------------------------------------
# PDF walking
# ---------------------------------------------------------------------------


def _walk_lineage_pages(doc: fitz.Document) -> list[dict[str, Any]]:
    """Walk pages 3-7 span-by-span, grouping traits under race + subrace."""
    races: list[dict[str, Any]] = []
    current_race: dict[str, Any] | None = None
    current_container: dict[str, Any] | None = None  # race or subrace
    current_trait: dict[str, str] | None = None

    def close_trait() -> None:
        nonlocal current_trait
        if current_trait is not None and current_container is not None:
            current_trait["text"] = clean_text(current_trait["text"].strip())
            current_container["traits"].append(current_trait)
            current_trait = None

    for pi in LINEAGE_PAGES_PDF_INDICES:
        page = doc[pi]
        srd_page = pi + 1
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = normalize_whitespace(span["text"])
                    if not text:
                        continue
                    size = round(span.get("size", 0), 1)
                    font = span.get("font", "")
                    flags = span.get("flags", 0)
                    is_bold = bool(flags & 16)
                    is_italic = bool(flags & 2)
                    role = _classify_span(
                        text=text,
                        size=size,
                        font=font,
                        is_bold=is_bold,
                        is_italic=is_italic,
                        race_seen=current_race is not None,
                    )

                    if role == "race":
                        close_trait()
                        current_race = {
                            "name": text,
                            "page": srd_page,
                            "traits": [],
                            "subraces": [],
                        }
                        current_container = current_race
                        races.append(current_race)
                    elif role == "subrace":
                        close_trait()
                        if current_race is None:
                            # 12pt GillSans before any race appeared (intro
                            # labels on p.3). Already filtered by race_seen,
                            # but guard defensively.
                            continue
                        subrace = {
                            "name": text,
                            "page": srd_page,
                            "traits": [],
                        }
                        current_race["subraces"].append(subrace)
                        current_container = subrace
                    elif role == "trait":
                        close_trait()
                        if current_container is None:
                            continue
                        # clean_text() does not normalize U+2019 (right
                        # single quote) reliably, so handle it here.
                        name = text.rstrip(".").replace("\u2019", "'")
                        current_trait = {
                            "name": name,
                            "text": "",
                        }
                    elif role == "body":
                        if current_trait is not None:
                            current_trait["text"] += text + " "
                    # role == "skip": no-op

    close_trait()
    return races


def _classify_span(
    *,
    text: str,
    size: float,
    font: str,
    is_bold: bool,
    is_italic: bool,
    race_seen: bool,
) -> str:
    """Return one of: race, subrace, trait, body, skip."""
    # Skip "Races" section header (only one occurrence, 25.9pt)
    if size >= 20.0:
        return "skip"

    # Race name: 18pt GillSans-SemiBold
    if is_bold and "GillSans" in font and 17.5 <= size <= 18.5:
        return "race"

    # "<Race> Traits" subheader: 13.9pt GillSans-SemiBold (skip — decoration)
    if is_bold and "GillSans" in font and 13.5 <= size <= 14.5:
        return "skip"

    # 12pt GillSans-SemiBold:
    #   - Before any race header → intro labels on p.3 (skip)
    #   - After race header → subrace name
    # Note: 12pt Calibri-Bold is the Draconic Ancestry table header (skip).
    if is_bold and "GillSans" in font and 11.5 <= size <= 12.5:
        return "subrace" if race_seen else "skip"

    # Trait header: 9.8pt Cambria-BoldItalic ending in "."
    if (
        is_bold
        and is_italic
        and "Cambria" in font
        and 9.5 <= size <= 10.5
        and text.endswith(".")
        and len(text) > 3
    ):
        return "trait"

    # Skip page numbers (10.8pt G-SB single digit) and header/footer
    if 10.5 <= size <= 11.0:
        return "skip"

    # Skip Dragon-ancestry table cells (8.9pt Calibri)
    if size < 9.5:
        return "skip"

    # Default: body text (typically 9.8pt Cambria or Cambria-Italic)
    if "Cambria" in font and 9.5 <= size <= 10.5:
        return "body"

    return "skip"


# ---------------------------------------------------------------------------
# Post-extraction structuring
# ---------------------------------------------------------------------------


def _finalize_lineage_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Pull structural traits up into top-level fields; same for subraces."""
    traits_by_name = {t["name"]: t["text"] for t in rec["traits"]}
    structured: dict[str, Any] = {
        "name": rec["name"],
        "simple_name": _slug(rec["name"]),
        "page": rec["page"],
        "ability_modifiers": _parse_ability_modifiers(
            traits_by_name.get("Ability Score Increase", "")
        ),
        "size": _parse_size(traits_by_name.get("Size", "")),
        "speed": _parse_speed(traits_by_name.get("Speed", "")),
    }
    if "Age" in traits_by_name:
        structured["age"] = traits_by_name["Age"]
    if "Alignment" in traits_by_name:
        structured["alignment"] = traits_by_name["Alignment"]
    if "Size" in traits_by_name:
        structured["size_description"] = traits_by_name["Size"]
    structured["languages"] = _parse_languages(traits_by_name.get("Languages", ""))
    structured["traits"] = [t for t in rec["traits"] if t["name"] not in _STRUCTURAL_TRAIT_NAMES]
    if rec["subraces"]:
        structured["subraces"] = [_finalize_subrace_record(sr) for sr in rec["subraces"]]
    return structured


def _finalize_subrace_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Subrace records only carry name, simple_name, ability_modifiers, traits."""
    traits_by_name = {t["name"]: t["text"] for t in rec["traits"]}
    return {
        "name": rec["name"],
        "simple_name": _slug(rec["name"]),
        "ability_modifiers": _parse_ability_modifiers(
            traits_by_name.get("Ability Score Increase", "")
        ),
        "traits": [t for t in rec["traits"] if t["name"] not in _STRUCTURAL_TRAIT_NAMES],
    }


# ---------------------------------------------------------------------------
# Field parsers
# ---------------------------------------------------------------------------


def _slug(name: str) -> str:
    """Lower-case, replace spaces/hyphens with underscores."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# Number words used in the SRD for ability-score language
# (e.g., "two other ability scores of your choice increase by 1").
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3}
_OTHER_ABILITIES_RE = re.compile(
    rf"({'|'.join(_NUMBER_WORDS)})\s+(?:different\s+|other\s+)?ability\s+scores?\s+of\s+your\s+choice\s+increase\s+by\s+(\d+)",
    re.IGNORECASE,
)


def _parse_ability_modifiers(text: str) -> dict[str, int]:
    """Return {"strength": 2, ...} from an "Ability Score Increase" trait body.

    Special cases:
    - Human: "Your ability scores each increase by 1." → all 6 abilities.
    - Half-Elf / similar: "two other ability scores of your choice increase
      by 1" → contributes {"other": count * bonus} matching the existing
      LINEAGE_DATA convention.
    """
    if not text:
        return {}
    if re.search(r"ability\s+scores\s+each\s+increase\s+by\s+(\d+)", text, re.IGNORECASE):
        match = re.search(r"each\s+increase\s+by\s+(\d+)", text, re.IGNORECASE)
        amount = int(match.group(1)) if match else 1
        return {a.lower(): amount for a in _ABILITIES}
    out: dict[str, int] = {}
    for m in _ABILITY_INCREASE_RE.finditer(text):
        ability = m.group(1).lower()
        bonus = int(m.group(2))
        out[ability] = out.get(ability, 0) + bonus
    other_match = _OTHER_ABILITIES_RE.search(text)
    if other_match:
        count = _NUMBER_WORDS[other_match.group(1).lower()]
        bonus = int(other_match.group(2))
        out["other"] = out.get("other", 0) + count * bonus
    return out


def _parse_size(text: str) -> str:
    """Return "Medium" / "Small" / "Large" from a Size trait body."""
    if not text:
        return ""
    m = _SIZE_RE.search(text)
    return m.group(1) if m else ""


def _parse_speed(text: str) -> int:
    """Return base walking speed in feet, or 0 if unparseable."""
    if not text:
        return 0
    m = _SPEED_RE.search(text)
    return int(m.group(1)) if m else 0


def _parse_languages(text: str) -> list[str]:
    """Return language list from a Languages trait body.

    Preserves narrative continuations such as "one extra language of
    your choice" verbatim (matching legacy LINEAGE_DATA convention) so
    downstream consumers can surface them as choice prompts.
    """
    if not text:
        return []
    m = _LANGUAGES_RE.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    # Normalize ", and " → ", " so the split below treats it uniformly,
    # then split on commas. Each part is kept verbatim (whitespace-trimmed).
    raw = re.sub(r",?\s+and\s+", ", ", raw)
    return [part.strip() for part in raw.split(",") if part.strip()]
