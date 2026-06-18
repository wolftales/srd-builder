"""Extract class structures from SRD 5.1 PDF pages 8-55.

Replaces the hand-curated ``rulesets/srd_5_1/class_targets.py`` (~763
lines, in service since v0.8.2). The "manually transcribed via visual
inspection" rationale on that file was disproven by
[tests/test_pdf_provenance.py::test_class_pages_are_extractable_after_whitespace_normalization](../../../tests/test_pdf_provenance.py)
in v0.27.0 (DISPUTED).

Font fingerprints on pages 8-55 (verified 2026-06-18 against
SRD_CC_v5.1.pdf via PyMuPDF 1.27.x):

- 25.9pt GillSans-SemiBold       — class name (12 hits across the range:
                                   Barbarian, Bard, ..., Wizard)
- 18.0pt GillSans-SemiBold       — "Class Features" subheader (skip)
- 13.9pt GillSans-SemiBold       — feature heading (e.g. "Rage",
                                   "Unarmored Defense", "Spellcasting")
                                   AND subclass section heading
                                   ("Path of the Berserker",
                                    "College of Lore", "Champion", ...)
- 12.0pt GillSans-SemiBold       — class-block section header
                                   ("Hit Points", "Proficiencies",
                                    "Equipment")
- 12.0pt Calibri-Bold            — progression table title
                                   ("The Barbarian", etc.; skip — the
                                    actual progression rows live in
                                    dist/srd_5_1/tables.json already)
- 9.8pt  Cambria-Bold            — sub-section label
                                   ("Hit Dice:", "Hit Points at 1st
                                    Level:", "Armor:", "Weapons:",
                                    "Tools:", "Saving Throws:",
                                    "Skills:")
- 9.8pt  Cambria                 — body text (accumulate)
- 8.9pt  Calibri / Calibri-Bold  — progression table cells (skip)
- 10.8pt G-SB / Calibri          — page number + footer (skip)

The extractor's output mirrors the legacy ``CLASS_DATA`` consumer
contract for the fields ``parse_classes.py`` + ``parse_features.py``
need. See ``tests/fixtures/srd_5_1/class_targets_snapshot.json`` for
the byte-perfect parity target.

This module is grown incrementally — each commit adds one field group:

1. (landed) class discovery: ``name``, ``simple_name``, ``page``
2. (landed) ``hit_die``, ``primary_abilities``,
   ``saving_throw_proficiencies``, ``proficiencies``
3. (this commit) ``features`` + ``subclasses``
4. spellcasting block
5. progression (mirrored from ``tables.json``)
6. cutover ``parse_classes`` / ``parse_features``, delete
   ``class_targets.py``, retire from PROVENANCE
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from srd_builder.postprocess.ids import normalize_id
from srd_builder.utils.pdf_probe import normalize_whitespace
from srd_builder.utils.prose import clean_text

CLASS_PAGES_PDF_INDICES = range(7, 55)  # SRD pages 8-55 (PDF idx 7-54)

_CLASS_NAME_SIZE = 25.9
_FONT_PREFIX = "GillSans"

# Field labels that live inside the "Proficiencies"/"Hit Points" boxes
# at the top of each class's first page. The body content sits in
# 9.8pt Cambria spans that follow the matching 9.8pt Cambria-Bold span,
# and runs until the next label or any 12pt+ GillSans heading.
_FIELD_LABEL_RE = re.compile(
    r"^(Hit Dice|Hit Points at \w+ Level\w*|Armor|Weapons|Tools|Saving Throws|Skills):$"
)
_HIT_DIE_RE = re.compile(r"\d+d(\d+)\b")

# Word-to-int for "Choose two from ...".
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4}

# Ability names appear capitalized in the "Saving Throws:" line; legacy
# CLASS_DATA stores them lowercase.
_ABILITY_NAMES_LOWER = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)

# SRD 5.1 does NOT print "Primary Ability:" in the class body — it
# appears only in the 5e PHB, not in the SRD. Verified 2026-06-18 by
# grepping pages 8, 24, 26 for /[Pp]rimary/ — zero matches. The legacy
# CLASS_DATA value is inferred curation. This lookup preserves the
# legacy field with a 12-line constant instead of 763.
_PRIMARY_ABILITIES: dict[str, list[str]] = {
    "barbarian": ["strength"],
    "bard": ["charisma"],
    "cleric": ["wisdom"],
    "druid": ["wisdom"],
    "fighter": ["strength", "dexterity"],
    "monk": ["dexterity", "wisdom"],
    "paladin": ["strength", "charisma"],
    "ranger": ["dexterity", "wisdom"],
    "rogue": ["dexterity"],
    "sorcerer": ["charisma"],
    "warlock": ["charisma"],
    "wizard": ["intelligence"],
}


def extract_classes(pdf_path: str | Path) -> dict[str, Any]:
    """Extract the 12 SRD 5.1 classes from the PDF.

    Returns a dict shaped (incrementally growing per commit)::

        {
            "source_pages": "8-55",
            "classes": [
                {
                    "name": "Barbarian",
                    "simple_name": "barbarian",
                    "page": 8,
                    "hit_die": "d12",
                    "primary_abilities": ["strength"],
                    "saving_throw_proficiencies": ["strength", "constitution"],
                    "proficiencies": {
                        "armor": ["light", "medium", "shields"],
                        "weapons": ["simple", "martial"],
                        "tools": [],
                        "skills": {"choose": 2, "from": [...]},
                    },
                    "features": ["feature:rage", "feature:unarmored_defense", ...],
                    "subclasses": ["subclass:path_of_the_berserker"],
                    # (later commits add spellcasting, progression)
                },
                ...
            ],
        }
    """
    pdf_path = Path(pdf_path)

    with fitz.open(str(pdf_path)) as doc:
        # Phase 1: locate the 25.9pt class-name span on each class's
        # first page so we know each class's page range.
        page_spans: dict[int, list[tuple[str, float, str, tuple]]] = {
            pi: _collect_spans(doc[pi]) for pi in CLASS_PAGES_PDF_INDICES
        }
        starts: list[tuple[int, str]] = []
        for pi, spans in page_spans.items():
            for txt, sz, font, _ in spans:
                if sz == _CLASS_NAME_SIZE and _FONT_PREFIX in font and txt:
                    starts.append((pi, txt))
                    break

        # Phase 2: for each class, derive its page range as
        # [start_pi, next_start_pi) (or end-of-classes for the last one)
        # and pull all field groups from those pages.
        classes: list[dict[str, Any]] = []
        for idx, (pi, name) in enumerate(starts):
            next_pi = starts[idx + 1][0] if idx + 1 < len(starts) else CLASS_PAGES_PDF_INDICES.stop
            class_spans: list[tuple[str, float, str, tuple]] = []
            for p in range(pi, next_pi):
                class_spans.extend(page_spans[p])
            classes.append(_build_class_record(name, pi, class_spans))

    return {"source_pages": "8-55", "classes": classes}


def _build_class_record(
    name: str,
    pi: int,
    class_spans: list[tuple[str, float, str, tuple]],
) -> dict[str, Any]:
    """Assemble a single class record from its accumulated page spans."""
    simple = normalize_id(name)
    record: dict[str, Any] = {
        "name": name,
        "simple_name": simple,
        "page": pi + 1,
        "primary_abilities": _PRIMARY_ABILITIES[simple],
    }
    record.update(_extract_field_labels(class_spans))
    features, subclasses = _extract_features_and_subclasses(class_spans, simple)
    record["features"] = features
    record["subclasses"] = subclasses
    return record


def _collect_spans(page: fitz.Page) -> list[tuple[str, float, str, tuple]]:
    """Flatten the page into ``(text, size, font, bbox)`` tuples in order."""
    spans: list[tuple[str, float, str, tuple]] = []
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                txt = normalize_whitespace(span["text"])
                if not txt:
                    continue
                spans.append(
                    (txt, round(span.get("size", 0), 1), span.get("font", ""), span["bbox"])
                )
    return spans


def _extract_field_labels(
    spans: list[tuple[str, float, str, tuple]],
) -> dict[str, Any]:
    """Walk spans, capturing each ``<Label>:`` block's body text.

    Body runs until the next label or any 12pt+ GillSans heading.
    """
    bodies: dict[str, str] = {}
    i = 0
    while i < len(spans):
        txt, sz, font, _ = spans[i]
        m = _FIELD_LABEL_RE.match(txt) if sz == 9.8 and font == "Cambria-Bold" else None
        if m is None:
            i += 1
            continue
        label = m.group(1)
        body_parts: list[str] = []
        j = i + 1
        while j < len(spans):
            tj, szj, fj, _ = spans[j]
            if szj == 9.8 and fj == "Cambria-Bold" and _FIELD_LABEL_RE.match(tj):
                break
            if szj >= 12.0 and "GillSans" in fj:
                break
            if szj == 9.8 and "Cambria" in fj:
                body_parts.append(tj)
            j += 1
        bodies[label] = clean_text(" ".join(body_parts))
        i = j

    out: dict[str, Any] = {}
    if "Hit Dice" in bodies:
        out["hit_die"] = _parse_hit_die(bodies["Hit Dice"])
    if "Saving Throws" in bodies:
        out["saving_throw_proficiencies"] = _parse_saving_throws(bodies["Saving Throws"])
    out["proficiencies"] = {
        "armor": _parse_armor(bodies.get("Armor", "")),
        "weapons": _parse_weapons(bodies.get("Weapons", "")),
        "tools": _parse_tools(bodies.get("Tools", "")),
        "skills": _parse_skills(bodies.get("Skills", "")),
    }
    return out


def _parse_hit_die(text: str) -> str:
    """``"1d12 per barbarian level"`` → ``"d12"``."""
    m = _HIT_DIE_RE.search(text)
    return f"d{m.group(1)}" if m else ""


def _parse_saving_throws(text: str) -> list[str]:
    """``"Strength, Constitution"`` → ``["strength", "constitution"]``."""
    return [
        part.strip().lower()
        for part in text.split(",")
        if part.strip().lower() in _ABILITY_NAMES_LOWER
    ]


def _parse_armor(text: str) -> list[str]:
    """``"Light armor, medium armor, shields"`` → ``["light", "medium", "shields"]``.

    ``"None"`` → ``[]``. ``"All armor, shields"`` → ``["all", "shields"]``.
    Parenthetical clarifiers (druid's "...made of metal") are dropped.
    """
    text = re.sub(r"\s*\([^)]*\)", "", text).strip()
    if text.lower() in {"none", ""}:
        return []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    out: list[str] = []
    for p in parts:
        low = p.lower()
        if low.endswith(" armor"):
            low = low[: -len(" armor")]
        out.append(low)
    return out


def _parse_weapons(text: str) -> list[str]:
    """``"Simple weapons, martial weapons"`` → ``["simple", "martial"]``.

    ``"Daggers, darts, ..."`` → ``["daggers", "darts", ...]``.
    """
    if not text or text.lower() == "none":
        return []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    out: list[str] = []
    for p in parts:
        low = p.lower()
        if low.endswith(" weapons"):
            low = low[: -len(" weapons")]
        elif low.endswith(" weapon"):
            low = low[: -len(" weapon")]
        out.append(low)
    return out


def _parse_tools(text: str) -> list[str]:
    """``"None"`` → ``[]``; anything else becomes a single lowercase entry."""
    if not text or text.lower() == "none":
        return []
    return [text[0].lower() + text[1:]]


_SKILLS_ANY_RE = re.compile(r"^Choose\s+any\s+(\w+)$", re.IGNORECASE)
_SKILLS_FROM_RE = re.compile(
    r"^Choose\s+(\w+)(?:\s+skills?)?\s+from\s+(.+)$", re.IGNORECASE | re.DOTALL
)

# Universal headings the SRD prints in every class block but that the
# legacy CLASS_DATA only lists for cleric (so that owner-resolution in
# parse_features has at least one definitive owner; the runtime
# _UNIVERSAL_FEATURES handles the per-class reprints). Match that
# divergence so the extractor's output is byte-identical with the
# snapshot.
_ASI = "Ability Score Improvement"
_CLASSES_KEEPING_ASI = frozenset({"cleric"})


def _extract_features_and_subclasses(
    class_spans: list[tuple[str, float, str, tuple]],
    class_simple: str,
) -> tuple[list[str], list[str]]:
    """Return ``(features, subclasses)`` derived from 13.9pt headings.

    Algorithm: collect every 13.9pt GillSans-SemiBold heading in PDF
    order across the class's page range. The last one is the subclass
    section heading; the rest are class features. Drop ``Ability Score
    Improvement`` from the features list for every class except cleric
    (see ``_CLASSES_KEEPING_ASI``).

    Feature IDs are unqualified (``feature:rage``) — the consumer
    ``parse_classes._qualify_feature_ids()`` rewrites them to
    ``feature:{owner}:rage``.
    """
    headings: list[str] = []
    for txt, sz, font, _ in class_spans:
        if sz == 13.9 and "GillSans" in font and txt:
            headings.append(txt)
    if not headings:
        return [], []
    *feature_headings, subclass_heading = headings
    if class_simple not in _CLASSES_KEEPING_ASI:
        feature_headings = [h for h in feature_headings if h != _ASI]
    features = [f"feature:{normalize_id(h)}" for h in feature_headings]
    subclasses = [f"subclass:{normalize_id(subclass_heading)}"]
    return features, subclasses


def _parse_skills(text: str) -> dict[str, Any]:
    """Parse the "Choose N from ..." / "Choose any N" shapes the SRD uses."""
    text = text.strip()
    m_any = _SKILLS_ANY_RE.match(text)
    if m_any:
        word = m_any.group(1).lower()
        return {"choose": _NUMBER_WORDS.get(word, 0), "from": ["any"]}
    m = _SKILLS_FROM_RE.match(text)
    if not m:
        return {"choose": 0, "from": []}
    count_word = m.group(1).lower()
    list_text = m.group(2).strip().rstrip(".")
    list_text = re.sub(r",\s+and\s+", ", ", list_text)
    list_text = re.sub(r"\s+and\s+", ", ", list_text)
    items = [p.strip() for p in list_text.split(",") if p.strip()]
    return {"choose": _NUMBER_WORDS.get(count_word, 0), "from": items}
