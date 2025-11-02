"""Index construction helpers for SRD entities."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from srd_builder.postprocess import normalize_id

__all__ = ["build_monster_index", "build_spell_index", "build_equipment_index", "build_indexes"]


def _stable_dict(values: Iterable[tuple[str, list[str]]]) -> dict[str, list[str]]:
    return {key: ids for key, ids in values}


def fallback_id(monster: dict[str, Any]) -> str:
    """Best-effort identifier for monsters missing explicit IDs."""

    if monster_id := monster.get("id"):
        return str(monster_id)
    if simple_name := monster.get("simple_name"):
        return str(simple_name)
    name = monster.get("name")
    if not isinstance(name, str):
        raise KeyError("name")
    return normalize_id(name)


def _build_by_name_map(
    monsters: Iterable[dict[str, Any]],
    *,
    display_normalizer: Callable[[str], str] | None = None,
) -> tuple[dict[str, str], dict[str, list[str]]]:
    by_name: dict[str, str] = {}
    conflicts: dict[str, list[str]] = {}
    for monster in monsters:
        name = str(monster.get("name", ""))
        normalized = display_normalizer(name) if display_normalizer else None
        key = (normalized or name).lower()
        monster_id = fallback_id(monster)
        existing = by_name.get(key)
        if existing is not None and existing != monster_id:
            conflicts.setdefault(key, []).append(monster_id)
            continue
        if key in by_name:
            # Same identifier encountered; skip without recording conflict.
            continue
        by_name[key] = monster_id
    sorted_conflicts = {key: sorted(ids) for key, ids in sorted(conflicts.items())}
    return dict(sorted(by_name.items())), sorted_conflicts


def build_monster_index(monsters: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical monster lookup tables."""

    by_name, _ = _build_by_name_map(monsters)
    by_cr: defaultdict[str, list[str]] = defaultdict(list)
    by_type: defaultdict[str, list[str]] = defaultdict(list)
    by_size: defaultdict[str, list[str]] = defaultdict(list)

    for monster in monsters:
        monster_id = fallback_id(monster)
        cr = monster.get("challenge_rating", 0)
        mtype = str(monster.get("type", "unknown"))
        size = str(monster.get("size", "Medium"))

        by_cr[str(cr)].append(monster_id)
        by_type[mtype].append(monster_id)
        by_size[size].append(monster_id)

    sorted_by_cr = _stable_dict(
        sorted(
            by_cr.items(),
            key=lambda item: float(item[0]) if _looks_numeric(item[0]) else 0.0,
        )
    )
    sorted_by_type = _stable_dict(sorted(by_type.items()))
    sorted_by_size = _stable_dict(sorted(by_size.items()))

    for mapping in (sorted_by_cr, sorted_by_type, sorted_by_size):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_cr": sorted_by_cr,
        "by_type": sorted_by_type,
        "by_size": sorted_by_size,
    }


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _build_entity_index(monsters: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for monster in monsters:
        monster_id = fallback_id(monster)
        index[monster_id] = {
            "type": "monster",
            "file": "monsters.json",
            "name": monster.get("name", ""),
        }
    return index


def build_spell_index(spells: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical spell lookup tables."""

    by_name, _ = _build_by_name_map(spells)
    by_level: defaultdict[str, list[str]] = defaultdict(list)
    by_school: defaultdict[str, list[str]] = defaultdict(list)
    by_concentration: defaultdict[str, list[str]] = defaultdict(list)
    by_ritual: defaultdict[str, list[str]] = defaultdict(list)

    for spell in spells:
        spell_id = fallback_id(spell)
        level = spell.get("level", 0)
        school = str(spell.get("school", "unknown"))

        # Extract concentration and ritual from casting object
        casting = spell.get("casting", {})
        concentration = casting.get("concentration", False)
        ritual = casting.get("ritual", False)

        by_level[str(level)].append(spell_id)
        by_school[school].append(spell_id)

        if concentration:
            by_concentration["true"].append(spell_id)
        else:
            by_concentration["false"].append(spell_id)

        if ritual:
            by_ritual["true"].append(spell_id)
        else:
            by_ritual["false"].append(spell_id)

    # Sort by level (numeric)
    sorted_by_level = _stable_dict(sorted(by_level.items(), key=lambda item: int(item[0])))
    sorted_by_school = _stable_dict(sorted(by_school.items()))
    sorted_by_concentration = _stable_dict(sorted(by_concentration.items()))
    sorted_by_ritual = _stable_dict(sorted(by_ritual.items()))

    for mapping in (sorted_by_level, sorted_by_school, sorted_by_concentration, sorted_by_ritual):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_level": sorted_by_level,
        "by_school": sorted_by_school,
        "by_concentration": sorted_by_concentration,
        "by_ritual": sorted_by_ritual,
    }


def _build_spell_entity_index(spells: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for spells."""
    index: dict[str, dict[str, str]] = {}
    for spell in spells:
        spell_id = fallback_id(spell)
        index[spell_id] = {
            "type": "spell",
            "file": "spells.json",
            "name": spell.get("name", ""),
        }
    return index


def build_equipment_index(equipment: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical equipment lookup tables."""

    by_name, _ = _build_by_name_map(equipment)
    by_category: defaultdict[str, list[str]] = defaultdict(list)
    by_rarity: defaultdict[str, list[str]] = defaultdict(list)

    for item in equipment:
        item_id = fallback_id(item)
        category = str(item.get("category", "unknown"))
        rarity = str(item.get("rarity", "common"))

        by_category[category].append(item_id)
        by_rarity[rarity].append(item_id)

    sorted_by_category = _stable_dict(sorted(by_category.items()))
    sorted_by_rarity = _stable_dict(sorted(by_rarity.items()))

    for mapping in (sorted_by_category, sorted_by_rarity):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_category": sorted_by_category,
        "by_rarity": sorted_by_rarity,
    }


def _build_equipment_entity_index(equipment: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for equipment."""
    index: dict[str, dict[str, str]] = {}
    for item in equipment:
        item_id = fallback_id(item)
        index[item_id] = {
            "type": "equipment",
            "file": "equipment.json",
            "name": item.get("name", ""),
        }
    return index


def build_table_index(tables: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical table lookup tables."""

    by_name, _ = _build_by_name_map(tables)
    by_category: defaultdict[str, list[str]] = defaultdict(list)

    for table in tables:
        table_id = fallback_id(table)
        category = str(table.get("category", "reference"))

        by_category[category].append(table_id)

    sorted_by_category = _stable_dict(sorted(by_category.items()))

    for key, ids in sorted_by_category.items():
        sorted_by_category[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_category": sorted_by_category,
    }


def _build_table_entity_index(tables: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for tables."""
    index: dict[str, dict[str, str]] = {}
    for table in tables:
        table_id = fallback_id(table)
        index[table_id] = {
            "type": "table",
            "file": "tables.json",
            "name": table.get("name", ""),
        }
    return index


def build_indexes(
    monsters: list[dict[str, Any]],
    spells: list[dict[str, Any]] | None = None,
    equipment: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    *,
    display_normalizer: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Aggregate monster, spell, equipment, table, and entity indexes for dataset output."""

    monster_indexes = build_monster_index(monsters)
    by_name, name_conflicts = _build_by_name_map(monsters, display_normalizer=display_normalizer)
    if by_name:
        monster_indexes["by_name"] = by_name
    monster_entity_index = _build_entity_index(monsters)

    # Build entity structure with nested type-specific keys
    entities: dict[str, dict[str, dict[str, str]]] = {
        "monsters": monster_entity_index,
    }

    payload: dict[str, Any] = {
        "monsters": monster_indexes,
        "entities": entities,
        "stats": {
            "total_monsters": len(monsters),
            "total_entities": len(monster_entity_index),
            "unique_crs": len(monster_indexes["by_cr"]),
            "unique_types": len(monster_indexes["by_type"]),
            "unique_sizes": len(monster_indexes["by_size"]),
        },
    }

    # Add spell indexes if spells provided (including empty list)
    if spells is not None:
        spell_indexes = build_spell_index(spells)
        spell_entity_index = _build_spell_entity_index(spells)

        payload["spells"] = spell_indexes
        entities["spells"] = spell_entity_index
        payload["stats"]["total_spells"] = len(spells)
        payload["stats"]["total_entities"] = len(monster_entity_index) + len(spell_entity_index)
        payload["stats"]["unique_spell_levels"] = len(spell_indexes["by_level"])
        payload["stats"]["unique_spell_schools"] = len(spell_indexes["by_school"])

    # Add equipment indexes if equipment provided (including empty list)
    if equipment is not None:
        equipment_indexes = build_equipment_index(equipment)
        equipment_entity_index = _build_equipment_entity_index(equipment)

        payload["equipment"] = equipment_indexes
        entities["equipment"] = equipment_entity_index
        payload["stats"]["total_equipment"] = len(equipment)
        # Recalculate total entities
        total = len(monster_entity_index)
        if spells is not None:
            total += len(spell_entity_index)
        total += len(equipment_entity_index)
        payload["stats"]["total_entities"] = total
        payload["stats"]["unique_equipment_categories"] = len(equipment_indexes["by_category"])
        payload["stats"]["unique_equipment_rarities"] = len(equipment_indexes["by_rarity"])

    # Add table indexes if tables provided (including empty list)
    if tables is not None:
        table_indexes = build_table_index(tables)
        table_entity_index = _build_table_entity_index(tables)

        payload["tables"] = table_indexes
        entities["tables"] = table_entity_index
        payload["stats"]["total_tables"] = len(tables)
        # Recalculate total entities
        total = len(monster_entity_index)
        if spells is not None:
            total += len(spell_entity_index)
        if equipment is not None:
            total += len(equipment_entity_index)
        total += len(table_entity_index)
        payload["stats"]["total_entities"] = total
        payload["stats"]["unique_table_categories"] = len(table_indexes["by_category"])

    if name_conflicts:
        payload["conflicts"] = {"by_name": name_conflicts}
    return payload
