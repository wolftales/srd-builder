"""Parse class data from canonical targets into validated records.

GUARDRAILS: Pure parsing/mapping only (no I/O/logging)
BOUNDARIES: Transforms CLASS_DATA → structured records with metadata

NOTE: Each class references its progression table (e.g., table:barbarian_progression)
      These tables contain level-by-level features, abilities, and class-specific values.
      Class progression tables need to be extracted from SRD PDF pages 8-55 and added
      to scripts/table_targets.py for complete dataset.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from srd_builder.srd_5_1.class_targets import CLASS_DATA
from srd_builder.utils.constants import DATA_SOURCE


def parse_classes() -> list[dict[str, Any]]:
    """Parse all classes from canonical target data.

    Returns:
        List of class records with complete progression data.
        Each record includes extraction_metadata for provenance.
    """
    classes: list[dict[str, Any]] = []

    for class_data in CLASS_DATA:
        class_record = _build_class_record(class_data)
        classes.append(class_record)

    return classes


def _build_class_record(data: dict[str, Any]) -> dict[str, Any]:
    """Build a complete class record from target data.

    Args:
        data: Class data from CLASS_DATA

    Returns:
        Fully structured class record with metadata
    """
    simple_name = data["simple_name"]

    record: dict[str, Any] = {
        "id": f"class:{simple_name}",
        "simple_name": simple_name,
        "name": data["name"],
        "hit_die": data["hit_die"],
        "primary_abilities": data["primary_abilities"],
        "saving_throw_proficiencies": data["saving_throw_proficiencies"],
        "proficiencies": data["proficiencies"],
        "features": data["features"],
        "subclasses": data.get("subclasses", []),
        "progression": data["progression"],
        "source": DATA_SOURCE,
        "page": data["page"],
        "extraction_metadata": {
            "source_pages": [data["page"]],
            "section": "classes",
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "extraction_notes": f"{data['name']} class from SRD 5.1",
        },
    }

    # Optional fields
    if "spellcasting" in data:
        record["spellcasting"] = data["spellcasting"]

    if "equipment" in data:
        record["equipment"] = data["equipment"]

    # Add tables_referenced for classes that use standard tables
    # All classes reference proficiency_bonus table
    tables_referenced = ["table:proficiency_bonus"]

    # Each class has its own progression table with class-specific features
    # These tables need to be extracted and added to table_targets.py
    class_table_id = f"table:{simple_name}_progression"
    tables_referenced.append(class_table_id)

    # Spellcasters reference spell slot tables
    if "spellcasting" in data:
        spell_list = data["spellcasting"]["spell_list"]
        # Map spell lists to their table IDs
        # Note: Class-specific spell slot tables need to be extracted from PDF
        if spell_list in ["wizard", "cleric", "druid"]:
            # Full casters use standard spell slot progression
            tables_referenced.append("table:spell_slots_full_caster")
        elif spell_list in ["bard", "sorcerer"]:
            # Full casters use standard spell slot progression
            tables_referenced.append("table:spell_slots_full_caster")
        elif spell_list == "paladin":
            # Half caster - separate table
            tables_referenced.append("table:paladin_spell_slots")
        elif spell_list == "ranger":
            # Half caster - separate table
            tables_referenced.append("table:ranger_spell_slots")
        elif spell_list == "warlock":
            # Pact magic - unique spell slot progression
            tables_referenced.append("table:warlock_spell_slots")

    record["tables_referenced"] = sorted(tables_referenced)

    return record
