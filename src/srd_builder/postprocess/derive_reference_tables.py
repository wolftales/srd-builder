"""Derive canonical reference tables that aren't standalone in the SRD PDF.

Five of the six tables this module produces are referenced from class records
(`tables_referenced`) but do not exist as standalone tables in the SRD layout:

- ``table:proficiency_bonus`` — appears as a column in every class progression
  table; this aggregates it once for cross-reference.
- ``table:spell_slots_full_caster`` — appears as columns 1st-9th in every full
  caster's progression (bard, cleric, druid, sorcerer, wizard, all identical).
- ``table:paladin_spell_slots`` — appears as columns 1st-5th in the paladin
  progression.
- ``table:ranger_spell_slots`` — appears as columns 1st-5th in the ranger
  progression.
- ``table:warlock_spell_slots`` — appears as "Spell Slots" + "Slot Level"
  columns in the warlock progression (pact magic).

The sixth (``table:draconic_ancestry``) IS a standalone table in the SRD
Dragonborn section (page 5) but is not yet wired into the table extractor's
TARGET_TABLES list. It is hand-curated here from the SRD CC-BY content with
a corresponding entry in ``docs/PROVENANCE.md``; the long-term fix is to add
it to ``extract/table_targets.py`` and pull it from the PDF.

Introduced in v0.39.0 to close Blackmoor's 21 dangling cross-references
(6 missing table IDs referenced from class and lineage records).
"""

from __future__ import annotations

from typing import Any

__all__ = ["derive_reference_tables"]


_STRIKETHROUGH = "\u0336"


def _clean_cell(value: Any) -> str:
    """Normalize a spell-slot cell.

    The class progression tables represent "no slot" as the digit '0' or '1'
    overprinted with U+0336 (combining long stroke overlay), which renders
    as a strikethrough. Strip the overlay and convert any '0'/'-' to '—'.
    """

    if value is None:
        return "\u2014"
    text = str(value).replace(_STRIKETHROUGH, "").strip()
    if text in ("", "0", "-", "\u2014", "\u2013"):
        return "\u2014"
    return text


def _find_progression(tables: list[dict[str, Any]], table_id: str) -> dict[str, Any]:
    for t in tables:
        if t.get("id") == table_id:
            return t
    raise KeyError(f"progression table not found: {table_id}")


def _column_index(table: dict[str, Any], name: str) -> int:
    for i, col in enumerate(table.get("columns", [])):
        if col.get("name") == name:
            return i
    raise KeyError(f"column not found: {name!r} in {table.get('id')}")


def _derive_proficiency_bonus(tables: list[dict[str, Any]]) -> dict[str, Any]:
    src = _find_progression(tables, "table:barbarian_progression")
    level_idx = _column_index(src, "Level")
    pb_idx = _column_index(src, "Proficiency Bonus")
    rows = [[row[level_idx], row[pb_idx]] for row in src.get("rows", [])]
    return {
        "id": "table:proficiency_bonus",
        "simple_name": "proficiency_bonus",
        "name": "Proficiency Bonus by Level",
        "page": 76,
        "category": "character_creation",
        "section": "Chapter 7: Using Ability Scores",
        "notes": (
            "Derived from class progression tables; the Proficiency Bonus "
            "column is identical across all 12 classes. Aggregated here as "
            "a standalone reference so cross-references from class records "
            "resolve."
        ),
        "columns": [
            {"name": "Level", "type": "string"},
            {"name": "Proficiency Bonus", "type": "string"},
        ],
        "rows": rows,
    }


_SPELL_SLOT_LEVELS_FULL = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"]
_SPELL_SLOT_LEVELS_HALF = ["1st", "2nd", "3rd", "4th", "5th"]


def _derive_spell_slot_table(
    tables: list[dict[str, Any]],
    *,
    table_id: str,
    simple_name: str,
    display_name: str,
    progression_id: str,
    slot_levels: list[str],
    page: int,
    section: str,
    notes: str,
) -> dict[str, Any]:
    src = _find_progression(tables, progression_id)
    level_idx = _column_index(src, "Level")
    slot_indices = [_column_index(src, lvl) for lvl in slot_levels]

    rows = []
    for src_row in src.get("rows", []):
        level = src_row[level_idx]
        slots = [_clean_cell(src_row[i]) for i in slot_indices]
        rows.append([level, *slots])

    columns: list[dict[str, str]] = [{"name": "Level", "type": "string"}]
    columns.extend({"name": lvl, "type": "string"} for lvl in slot_levels)

    return {
        "id": table_id,
        "simple_name": simple_name,
        "name": display_name,
        "page": page,
        "category": "magic",
        "section": section,
        "notes": notes,
        "columns": columns,
        "rows": rows,
    }


def _derive_warlock_spell_slots(tables: list[dict[str, Any]]) -> dict[str, Any]:
    src = _find_progression(tables, "table:warlock_progression")
    level_idx = _column_index(src, "Level")
    count_idx = _column_index(src, "Spell Slots")
    slot_lvl_idx = _column_index(src, "Slot Level")
    rows = [[row[level_idx], row[count_idx], row[slot_lvl_idx]] for row in src.get("rows", [])]
    return {
        "id": "table:warlock_spell_slots",
        "simple_name": "warlock_spell_slots",
        "name": "Warlock Pact Magic Spell Slots",
        "page": 53,
        "category": "magic",
        "section": "Chapter 3: Classes - Warlock",
        "notes": (
            "Derived from the warlock class progression (Pact Magic columns). "
            "Warlocks recover all slots on a short rest; slot count and slot "
            "level scale together rather than via the full-caster table."
        ),
        "columns": [
            {"name": "Level", "type": "string"},
            {"name": "Spell Slots", "type": "string"},
            {"name": "Slot Level", "type": "string"},
        ],
        "rows": rows,
    }


# Hand-curated. The Draconic Ancestry table is a standalone SRD table on
# page 5 (Dragonborn section). The current TARGET_TABLES list in
# src/srd_builder/extract/table_targets.py does not include it, so the
# extractor never pulls it. Documented in docs/PROVENANCE.md with
# reason_code = pdf_missing; the long-term fix is to add it to
# TARGET_TABLES and re-extract.
_DRACONIC_ANCESTRY: dict[str, Any] = {
    "id": "table:draconic_ancestry",
    "simple_name": "draconic_ancestry",
    "name": "Draconic Ancestry",
    "page": 5,
    "category": "reference",
    "section": "Chapter 2: Races - Dragonborn",
    "notes": (
        "Hand-curated from SRD 5.1 CC-BY content (Dragonborn section, page 5). "
        "Not yet wired into extract/table_targets.py. See docs/PROVENANCE.md "
        "\u00a7 draconic_ancestry."
    ),
    "columns": [
        {"name": "Dragon", "type": "string"},
        {"name": "Damage Type", "type": "string"},
        {"name": "Breath Weapon", "type": "string"},
    ],
    "rows": [
        ["Black", "Acid", "5 by 30 ft. line (Dex. save)"],
        ["Blue", "Lightning", "5 by 30 ft. line (Dex. save)"],
        ["Brass", "Fire", "5 by 30 ft. line (Dex. save)"],
        ["Bronze", "Lightning", "5 by 30 ft. line (Dex. save)"],
        ["Copper", "Acid", "5 by 30 ft. line (Dex. save)"],
        ["Gold", "Fire", "15 ft. cone (Dex. save)"],
        ["Green", "Poison", "15 ft. cone (Con. save)"],
        ["Red", "Fire", "15 ft. cone (Dex. save)"],
        ["Silver", "Cold", "15 ft. cone (Con. save)"],
        ["White", "Cold", "15 ft. cone (Con. save)"],
    ],
}


def derive_reference_tables(existing_tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the 6 derived reference tables.

    Caller is responsible for appending these to ``existing_tables`` before
    writing tables.json. The function is pure (no I/O) and idempotent: passing
    the same input always returns the same output.
    """

    return [
        _derive_proficiency_bonus(existing_tables),
        _derive_spell_slot_table(
            existing_tables,
            table_id="table:spell_slots_full_caster",
            simple_name="spell_slots_full_caster",
            display_name="Spell Slots per Spell Level (Full Caster)",
            progression_id="table:bard_progression",
            slot_levels=_SPELL_SLOT_LEVELS_FULL,
            page=11,
            section="Chapter 3: Classes - Bard (also Cleric, Druid, Sorcerer, Wizard)",
            notes=(
                "Derived from the bard class progression; the spell slot columns "
                "1st-9th are byte-identical across all five full-caster classes "
                "(bard, cleric, druid, sorcerer, wizard)."
            ),
        ),
        _derive_spell_slot_table(
            existing_tables,
            table_id="table:paladin_spell_slots",
            simple_name="paladin_spell_slots",
            display_name="Paladin Spell Slots",
            progression_id="table:paladin_progression",
            slot_levels=_SPELL_SLOT_LEVELS_HALF,
            page=42,
            section="Chapter 3: Classes - Paladin",
            notes=(
                "Derived from the paladin class progression (half-caster slot "
                "columns 1st-5th, starting at class level 2)."
            ),
        ),
        _derive_spell_slot_table(
            existing_tables,
            table_id="table:ranger_spell_slots",
            simple_name="ranger_spell_slots",
            display_name="Ranger Spell Slots",
            progression_id="table:ranger_progression",
            slot_levels=_SPELL_SLOT_LEVELS_HALF,
            page=46,
            section="Chapter 3: Classes - Ranger",
            notes=(
                "Derived from the ranger class progression (half-caster slot "
                "columns 1st-5th, starting at class level 2)."
            ),
        ),
        _derive_warlock_spell_slots(existing_tables),
        _DRACONIC_ANCESTRY,
    ]
