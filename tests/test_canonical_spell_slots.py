"""Semantic parity tests: shipped paladin/ranger spell-slot data matches
canonical SRD 5.1 truth after the v0.39.1 column corrections.

These tests guard against silently regressing the v0.39.1 column
corrections (see `src/srd_builder/postprocess/correct_class_progressions.py`).
They fail if either:

  - the correction module stops running before tables.json is written,
  - the canonical SRD values in `_RANGER_CANONICAL` drift away from the
    published SRD 5.1 CC-BY half-caster spell-slot progression, or
  - the derivation in `derive_reference_tables.py` selects the wrong
    source columns.

Scope notes:

  - The source paladin progression (`table:paladin_progression`) retains
    PyMuPDF's combining-overlay strikethrough character (U+0336) in
    em-dash cells we did NOT touch; that is a separate pre-existing
    cosmetic concern that affects all 8 spellcaster progressions. The
    paladin test here only validates the cells we patched (L2 Features
    + L2 first-slot).
  - The source ranger progression (`table:ranger_progression`) gets all
    Spells Known + 1st-5th slot cells overwritten by the corrections
    module, so it ships with clean em-dashes in those positions.
  - The derived spell-slot tables go through `_clean_cell` in
    `derive_reference_tables.py`, which normalizes dirty dashes to clean
    em-dashes, so they always match the canonical truth.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_TABLES = REPO_ROOT / "dist" / "srd_5_1" / "tables.json"

EM_DASH = "\u2014"

# Canonical SRD 5.1 ranger spell-slot progression (half-caster).
# Each tuple: (level_label, spells_known, 1st, 2nd, 3rd, 4th, 5th).
CANONICAL_RANGER_ROWS: list[tuple[str, ...]] = [
    ("1st", EM_DASH, EM_DASH, EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("2nd", "2", "2", EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("3rd", "3", "3", EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("4th", "3", "3", EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("5th", "4", "4", "2", EM_DASH, EM_DASH, EM_DASH),
    ("6th", "4", "4", "2", EM_DASH, EM_DASH, EM_DASH),
    ("7th", "5", "4", "3", EM_DASH, EM_DASH, EM_DASH),
    ("8th", "5", "4", "3", EM_DASH, EM_DASH, EM_DASH),
    ("9th", "6", "4", "3", "2", EM_DASH, EM_DASH),
    ("10th", "6", "4", "3", "2", EM_DASH, EM_DASH),
    ("11th", "7", "4", "3", "3", EM_DASH, EM_DASH),
    ("12th", "7", "4", "3", "3", EM_DASH, EM_DASH),
    ("13th", "8", "4", "3", "3", "1", EM_DASH),
    ("14th", "8", "4", "3", "3", "1", EM_DASH),
    ("15th", "9", "4", "3", "3", "2", EM_DASH),
    ("16th", "9", "4", "3", "3", "2", EM_DASH),
    ("17th", "10", "4", "3", "3", "3", "1"),
    ("18th", "10", "4", "3", "3", "3", "1"),
    ("19th", "11", "4", "3", "3", "3", "2"),
    ("20th", "11", "4", "3", "3", "3", "2"),
]

# Canonical SRD 5.1 paladin spell slots (half-caster, no Spells Known column).
# Each tuple: (level_label, 1st, 2nd, 3rd, 4th, 5th).
CANONICAL_PALADIN_SLOTS: list[tuple[str, ...]] = [
    ("1st", EM_DASH, EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("2nd", "2", EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("3rd", "3", EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("4th", "3", EM_DASH, EM_DASH, EM_DASH, EM_DASH),
    ("5th", "4", "2", EM_DASH, EM_DASH, EM_DASH),
    ("6th", "4", "2", EM_DASH, EM_DASH, EM_DASH),
    ("7th", "4", "3", EM_DASH, EM_DASH, EM_DASH),
    ("8th", "4", "3", EM_DASH, EM_DASH, EM_DASH),
    ("9th", "4", "3", "2", EM_DASH, EM_DASH),
    ("10th", "4", "3", "2", EM_DASH, EM_DASH),
    ("11th", "4", "3", "3", EM_DASH, EM_DASH),
    ("12th", "4", "3", "3", EM_DASH, EM_DASH),
    ("13th", "4", "3", "3", "1", EM_DASH),
    ("14th", "4", "3", "3", "1", EM_DASH),
    ("15th", "4", "3", "3", "2", EM_DASH),
    ("16th", "4", "3", "3", "2", EM_DASH),
    ("17th", "4", "3", "3", "3", "1"),
    ("18th", "4", "3", "3", "3", "1"),
    ("19th", "4", "3", "3", "3", "2"),
    ("20th", "4", "3", "3", "3", "2"),
]


@pytest.fixture(scope="module")
def bundle_tables_by_id() -> dict[str, dict]:
    if not BUNDLE_TABLES.exists():
        pytest.skip(f"Bundle tables not found at {BUNDLE_TABLES} — run `make bundle` first")
    doc = json.loads(BUNDLE_TABLES.read_text(encoding="utf-8"))
    return {t["id"]: t for t in doc["items"]}


def test_paladin_progression_l2_divine_smite_corrected(
    bundle_tables_by_id: dict[str, dict],
) -> None:
    """Source `table:paladin_progression` row 2 has the Features cell and
    1st-slot cell corrected from PyMuPDF's mis-merged
    `Divine Smite 2` extraction into the canonical SRD split values.
    """
    table = bundle_tables_by_id["table:paladin_progression"]
    columns = [c["name"] for c in table["columns"]]
    features_idx = columns.index("Features")
    first_slot_idx = columns.index("1st")

    l2_row = next((r for r in table["rows"] if str(r[0]).strip() == "2nd"), None)
    assert l2_row is not None, "Could not find L2 row in shipped paladin_progression"

    assert l2_row[features_idx] == "Fighting Style, Spellcasting, Divine Smite", (
        f"Paladin L2 Features cell is {l2_row[features_idx]!r}; "
        "v0.39.1 correction in correct_class_progressions._fix_paladin "
        "may not be running."
    )
    assert l2_row[first_slot_idx] == "2", (
        f"Paladin L2 1st-slot cell is {l2_row[first_slot_idx]!r}; "
        "v0.39.1 correction may not be running, or PyMuPDF returned a "
        "different broken format that the fix predicate did not match."
    )


def test_ranger_progression_spell_slots_match_canonical_srd(
    bundle_tables_by_id: dict[str, dict],
) -> None:
    """Source `table:ranger_progression`: every row's Spells Known
    + 1st-5th slot cells match SRD 5.1 canonical values after the
    v0.39.1 column correction. Features and Proficiency Bonus columns
    are not validated here (they are unaffected by the correction).
    """
    table = bundle_tables_by_id["table:ranger_progression"]
    columns = [c["name"] for c in table["columns"]]
    slot_cols = ["Spells Known", "1st", "2nd", "3rd", "4th", "5th"]
    level_idx = columns.index("Level")
    slot_idxs = [columns.index(name) for name in slot_cols]

    actual = []
    for row in table["rows"]:
        level = str(row[level_idx]).strip()
        slots = tuple(str(row[i]).strip() for i in slot_idxs)
        actual.append((level, *slots))

    assert actual == CANONICAL_RANGER_ROWS


def test_derived_paladin_spell_slots_match_canonical_srd(
    bundle_tables_by_id: dict[str, dict],
) -> None:
    """Derived `table:paladin_spell_slots` matches the canonical SRD
    paladin slot progression byte-for-byte (no Spells Known column).
    """
    table = bundle_tables_by_id["table:paladin_spell_slots"]
    columns = [c["name"] for c in table["columns"]]
    assert columns == ["Level", "1st", "2nd", "3rd", "4th", "5th"]

    actual = [tuple(str(cell).strip() for cell in row) for row in table["rows"]]
    assert actual == CANONICAL_PALADIN_SLOTS


def test_derived_ranger_spell_slots_match_canonical_srd(
    bundle_tables_by_id: dict[str, dict],
) -> None:
    """Derived `table:ranger_spell_slots` matches the canonical SRD
    ranger slot progression byte-for-byte. Note: the derived table does
    not include the Spells Known column (consistent with paladin's
    derived slot table; consumers should read Spells Known from the
    source `table:ranger_progression` if needed).
    """
    table = bundle_tables_by_id["table:ranger_spell_slots"]
    columns = [c["name"] for c in table["columns"]]
    assert columns == ["Level", "1st", "2nd", "3rd", "4th", "5th"]

    expected = [(row[0], *row[2:]) for row in CANONICAL_RANGER_ROWS]
    actual = [tuple(str(cell).strip() for cell in row) for row in table["rows"]]
    assert actual == expected
