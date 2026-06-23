"""Post-extraction corrections for the paladin and ranger progression tables.

Our `split_column` table extractor (configured in
``src/srd_builder/extract/extraction_metadata.py`` with hand-tuned
``column_boundaries``) misdetects column boundaries on two SRD class
progressions because the Features column contains multi-line text that wraps
into adjacent column slots:

  - ``table:paladin_progression`` row 2 (level 2): the Features cell
    ``"Fighting Style, Spellcasting, Divine Smite"`` wraps; the trailing
    ``"Divine Smite"`` token gets merged with the level-2 first-level spell
    slot count ``2`` and emitted as ``"Divine Smite 2"`` in the 1st-slot
    column. All other paladin rows are correct.

  - ``table:ranger_progression`` is wrong at 19 of 20 levels. The
    Spells Known column is dropped to empty for rows 1-16 (slot values
    shift left by one position; the trailing 5th-slot column gets a
    duplicated value or loses its terminal dash), and for rows 17-20 the
    Spells Known column is populated but the 1st-slot column is blank
    (slot values 2nd-5th shift left and the 5th-slot value is dropped).

Both behaviors originate at the ``split_column`` extractor in
``extract/patterns/split_column.py`` reading the boundaries configured
for these two tables. They are NOT introduced by our parse layer. See
``tests/test_pdf_provenance.py::test_paladin_l2_divine_smite_column_drift``
and ``::test_ranger_progression_column_drift`` for reproducers.

This module replaces the affected cells with canonical SRD 5.1 CC-BY values:

  - Paladin: Features L2 -> ``"Fighting Style, Spellcasting, Divine Smite"``;
    1st-slot L2 -> ``"2"``.
  - Ranger: Spells Known and 1st-5th slot columns -> canonical half-caster
    spell-slot progression for all 20 levels. The Features column is left
    as extracted (the L6/L8/L10 Features wrap is benign once the slot
    columns are correct).

Long-term fix: re-tune the ``column_boundaries`` for ``paladin`` and
``ranger`` in ``extraction_metadata.py`` so the extractor places text
spans correctly without post-hoc patching. At that point this entire
module can be deleted; see PROVENANCE entry for the removal trigger.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

EM_DASH = "\u2014"

PALADIN_L2_FEATURES = "Fighting Style, Spellcasting, Divine Smite"

# Canonical SRD 5.1 ranger spell-slot progression (half-caster).
# Index = level - 1. Each entry is (spells_known, 1st, 2nd, 3rd, 4th, 5th).
# Em-dash for slots the ranger does not have at that level.
_RANGER_CANONICAL: list[tuple[str, str, str, str, str, str]] = [
    (EM_DASH, EM_DASH, EM_DASH, EM_DASH, EM_DASH, EM_DASH),  # L1
    ("2", "2", EM_DASH, EM_DASH, EM_DASH, EM_DASH),  # L2
    ("3", "3", EM_DASH, EM_DASH, EM_DASH, EM_DASH),  # L3
    ("3", "3", EM_DASH, EM_DASH, EM_DASH, EM_DASH),  # L4
    ("4", "4", "2", EM_DASH, EM_DASH, EM_DASH),  # L5
    ("4", "4", "2", EM_DASH, EM_DASH, EM_DASH),  # L6
    ("5", "4", "3", EM_DASH, EM_DASH, EM_DASH),  # L7
    ("5", "4", "3", EM_DASH, EM_DASH, EM_DASH),  # L8
    ("6", "4", "3", "2", EM_DASH, EM_DASH),  # L9
    ("6", "4", "3", "2", EM_DASH, EM_DASH),  # L10
    ("7", "4", "3", "3", EM_DASH, EM_DASH),  # L11
    ("7", "4", "3", "3", EM_DASH, EM_DASH),  # L12
    ("8", "4", "3", "3", "1", EM_DASH),  # L13
    ("8", "4", "3", "3", "1", EM_DASH),  # L14
    ("9", "4", "3", "3", "2", EM_DASH),  # L15
    ("9", "4", "3", "3", "2", EM_DASH),  # L16
    ("10", "4", "3", "3", "3", "1"),  # L17
    ("10", "4", "3", "3", "3", "1"),  # L18
    ("11", "4", "3", "3", "3", "2"),  # L19
    ("11", "4", "3", "3", "3", "2"),  # L20
]


def _fix_paladin(table: dict[str, Any]) -> dict[str, Any]:
    """Patch the paladin L2 row in-place on a deep copy."""
    fixed = deepcopy(table)
    columns = [c["name"] for c in fixed["columns"]]
    features_idx = columns.index("Features")
    first_slot_idx = columns.index("1st")
    for row in fixed["rows"]:
        if not row or str(row[0]).strip() != "2nd":
            continue
        # Detect the wrapped "Divine Smite N" cell verbatim before patching;
        # if PyMuPDF starts returning the correct split, leave the row alone
        # so the test in tests/test_pdf_provenance.py fails and signals that
        # the correction can be retired.
        slot_cell = str(row[first_slot_idx]).strip()
        if not slot_cell.startswith("Divine Smite "):
            continue
        row[features_idx] = PALADIN_L2_FEATURES
        row[first_slot_idx] = slot_cell[len("Divine Smite ") :].strip()
    return fixed


def _fix_ranger(table: dict[str, Any]) -> dict[str, Any]:
    """Replace ranger Spells Known + 1st-5th slot columns with canonical SRD
    values on a deep copy. Features and Proficiency Bonus columns are left
    as extracted.
    """
    fixed = deepcopy(table)
    columns = [c["name"] for c in fixed["columns"]]
    sk_idx = columns.index("Spells Known")
    slot_idxs = [columns.index(name) for name in ("1st", "2nd", "3rd", "4th", "5th")]

    if len(fixed["rows"]) != len(_RANGER_CANONICAL):
        # Row count drift means the extractor changed shape; don't silently
        # patch wrong rows. Let the downstream parity test surface the change.
        return fixed

    for row, canonical in zip(fixed["rows"], _RANGER_CANONICAL, strict=True):
        sk, *slots = canonical
        row[sk_idx] = sk
        for col_idx, value in zip(slot_idxs, slots, strict=True):
            row[col_idx] = value
    return fixed


def apply_progression_corrections(tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a new list with paladin and ranger progression tables corrected.

    Other tables pass through unchanged (same dict instance).
    """
    out: list[dict[str, Any]] = []
    for table in tables:
        tid = table.get("id")
        if tid == "table:paladin_progression":
            out.append(_fix_paladin(table))
        elif tid == "table:ranger_progression":
            out.append(_fix_ranger(table))
        else:
            out.append(table)
    return out
