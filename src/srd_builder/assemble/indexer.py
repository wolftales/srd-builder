"""Index construction helpers for SRD entities."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from srd_builder.postprocess import normalize_id

__all__ = [
    "build_monster_index",
    "build_spell_index",
    "build_equipment_index",
    "build_lineage_index",
    "build_class_index",
    "build_condition_index",
    "build_rule_index",
    "build_indexes",
    "build_cross_reference_indexes",
]


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

        # Add entity-level aliases to by_name map
        aliases = monster.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                alias_key = str(alias).lower()
                # Skip if alias conflicts with existing entry
                if alias_key in by_name and by_name[alias_key] != monster_id:
                    conflicts.setdefault(alias_key, []).append(monster_id)
                    continue
                by_name[alias_key] = monster_id

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


def _build_entity_index_for_type(
    entities: list[dict[str, Any]], *, entity_type: str, file_name: str
) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for entity in entities:
        entity_id = fallback_id(entity)
        index[entity_id] = {
            "type": entity_type,
            "file": file_name,
            "name": entity.get("name", ""),
        }
    return index


def build_spell_index(spells: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical spell lookup tables."""

    by_name, _ = _build_by_name_map(spells)
    by_level: defaultdict[str, list[str]] = defaultdict(list)
    by_school: defaultdict[str, list[str]] = defaultdict(list)
    by_concentration: defaultdict[str, list[str]] = defaultdict(list)
    by_ritual: defaultdict[str, list[str]] = defaultdict(list)
    by_class: defaultdict[str, list[str]] = defaultdict(list)

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

        # Check duration.requires_concentration field (v0.8.6 schema)
        concentration = spell.get("duration", {}).get("requires_concentration", False)
        if concentration:
            by_concentration["true"].append(spell_id)
        else:
            by_concentration["false"].append(spell_id)

        if ritual:
            by_ritual["true"].append(spell_id)
        else:
            by_ritual["false"].append(spell_id)

        # Index by class (v0.8.0)
        classes = spell.get("classes", [])
        for class_name in classes:
            by_class[class_name].append(spell_id)

    # Sort by level (numeric)
    sorted_by_level = _stable_dict(sorted(by_level.items(), key=lambda item: int(item[0])))
    sorted_by_school = _stable_dict(sorted(by_school.items()))
    sorted_by_concentration = _stable_dict(sorted(by_concentration.items()))
    sorted_by_ritual = _stable_dict(sorted(by_ritual.items()))
    sorted_by_class = _stable_dict(sorted(by_class.items()))

    for mapping in (
        sorted_by_level,
        sorted_by_school,
        sorted_by_concentration,
        sorted_by_ritual,
        sorted_by_class,
    ):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_level": sorted_by_level,
        "by_school": sorted_by_school,
        "by_concentration": sorted_by_concentration,
        "by_ritual": sorted_by_ritual,
        "by_class": sorted_by_class,
    }


def _build_spell_entity_index(spells: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for spells."""
    return _build_simple_entity_index(spells, "spell", "spells.json")


def build_equipment_index(equipment: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical equipment lookup tables."""

    by_name, _ = _build_by_name_map(equipment)
    by_category: defaultdict[str, list[str]] = defaultdict(list)
    by_rarity: defaultdict[str, list[str]] = defaultdict(list)
    by_proficiency: defaultdict[str, list[str]] = defaultdict(list)
    by_weapon_type: defaultdict[str, list[str]] = defaultdict(list)

    for item in equipment:
        item_id = fallback_id(item)
        category = str(item.get("category", "unknown"))
        rarity = str(item.get("rarity", "common"))

        by_category[category].append(item_id)
        by_rarity[rarity].append(item_id)

        # Index by proficiency (weapons only)
        proficiency = item.get("proficiency")
        if proficiency:
            by_proficiency[str(proficiency)].append(item_id)

        # Index by weapon_type (weapons only)
        weapon_type = item.get("weapon_type")
        if weapon_type:
            by_weapon_type[str(weapon_type)].append(item_id)

    sorted_by_category = _stable_dict(sorted(by_category.items()))
    sorted_by_rarity = _stable_dict(sorted(by_rarity.items()))
    sorted_by_proficiency = _stable_dict(sorted(by_proficiency.items()))
    sorted_by_weapon_type = _stable_dict(sorted(by_weapon_type.items()))

    for mapping in (
        sorted_by_category,
        sorted_by_rarity,
        sorted_by_proficiency,
        sorted_by_weapon_type,
    ):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_category": sorted_by_category,
        "by_rarity": sorted_by_rarity,
        "by_proficiency": sorted_by_proficiency,
        "by_weapon_type": sorted_by_weapon_type,
    }


def _build_equipment_entity_index(equipment: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for equipment."""
    return _build_simple_entity_index(equipment, "equipment", "equipment.json")


def build_magic_item_index(magic_items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical magic item lookup tables."""

    by_name, _ = _build_by_name_map(magic_items)
    by_rarity: defaultdict[str, list[str]] = defaultdict(list)
    by_type: defaultdict[str, list[str]] = defaultdict(list)
    by_attunement: defaultdict[str, list[str]] = defaultdict(list)

    for item in magic_items:
        item_id = fallback_id(item)
        rarity = str(item.get("rarity", "common"))
        item_type = str(item.get("type", "unknown"))
        requires_attunement = item.get("requires_attunement", False)

        by_rarity[rarity].append(item_id)
        by_type[item_type].append(item_id)
        by_attunement[str(requires_attunement)].append(item_id)

    sorted_by_rarity = _stable_dict(sorted(by_rarity.items()))
    sorted_by_type = _stable_dict(sorted(by_type.items()))
    sorted_by_attunement = _stable_dict(sorted(by_attunement.items()))

    for mapping in (sorted_by_rarity, sorted_by_type, sorted_by_attunement):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_rarity": sorted_by_rarity,
        "by_type": sorted_by_type,
        "by_attunement": sorted_by_attunement,
    }


def _build_magic_item_entity_index(magic_items: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for magic items."""
    return _build_simple_entity_index(magic_items, "magic_item", "magic_items.json")


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
    return _build_simple_entity_index(tables, "table", "tables.json")


def build_lineage_index(lineages: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical lineage lookup tables."""

    by_name, _ = _build_by_name_map(lineages)
    by_size: defaultdict[str, list[str]] = defaultdict(list)
    by_speed: defaultdict[str, list[str]] = defaultdict(list)

    for lineage in lineages:
        lineage_id = fallback_id(lineage)
        size = str(lineage.get("size", "Medium"))
        speed = str(lineage.get("speed", 30))

        by_size[size].append(lineage_id)
        by_speed[speed].append(lineage_id)

    sorted_by_size = _stable_dict(sorted(by_size.items()))
    sorted_by_speed = _stable_dict(
        sorted(by_speed.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 0)
    )

    for mapping in (sorted_by_size, sorted_by_speed):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_size": sorted_by_size,
        "by_speed": sorted_by_speed,
    }


def _build_lineage_entity_index(lineages: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for lineages."""
    return _build_simple_entity_index(lineages, "lineage", "lineages.json")


def build_class_index(classes: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical class lookup tables."""

    by_name, _ = _build_by_name_map(classes)
    by_hit_die: defaultdict[str, list[str]] = defaultdict(list)
    by_primary_ability: defaultdict[str, list[str]] = defaultdict(list)

    for class_record in classes:
        class_id = fallback_id(class_record)
        hit_die = str(class_record.get("hit_die", "d8"))
        primary_abilities = class_record.get("primary_abilities", [])

        by_hit_die[hit_die].append(class_id)

        # Add to each primary ability (some classes have multiple)
        if isinstance(primary_abilities, list):
            for ability in primary_abilities:
                by_primary_ability[str(ability)].append(class_id)

    sorted_by_hit_die = _stable_dict(sorted(by_hit_die.items()))
    sorted_by_primary_ability = _stable_dict(sorted(by_primary_ability.items()))

    for mapping in (sorted_by_hit_die, sorted_by_primary_ability):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_hit_die": sorted_by_hit_die,
        "by_primary_ability": sorted_by_primary_ability,
    }


def _build_class_entity_index(classes: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for classes."""
    return _build_simple_entity_index(classes, "class", "classes.json")


def build_condition_index(conditions: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical condition lookup tables."""

    by_name, _ = _build_by_name_map(conditions)
    by_has_levels: defaultdict[str, list[str]] = defaultdict(list)

    for condition in conditions:
        condition_id = fallback_id(condition)
        has_levels = "levels" in condition

        if has_levels:
            by_has_levels["true"].append(condition_id)
        else:
            by_has_levels["false"].append(condition_id)

    sorted_by_has_levels = _stable_dict(sorted(by_has_levels.items()))

    for key, ids in sorted_by_has_levels.items():
        sorted_by_has_levels[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_has_levels": sorted_by_has_levels,
    }


def _build_condition_entity_index(conditions: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build entity index for conditions."""
    return _build_simple_entity_index(conditions, "condition", "conditions.json")


def _build_simple_entity_index(
    records: list[dict[str, Any]], entity_type: str, filename: str
) -> dict[str, dict[str, str]]:
    """Build entity index for simple name-based datasets (diseases, madness, poisons, features)."""
    index: dict[str, dict[str, str]] = {}
    for record in records:
        record_id = fallback_id(record)
        index[record_id] = {
            "type": entity_type,
            "file": filename,
            "name": record.get("name", ""),
        }
    return index


def _sorted_xref_dict(index: dict[str, list[str]]) -> dict[str, list[str]]:
    """Sort cross-reference dict by keys, with sorted value lists."""
    return {k: sorted(v) for k, v in sorted(index.items())}


def build_cross_reference_indexes(
    *,
    monsters: list[dict[str, Any]] | None = None,
    spells: list[dict[str, Any]] | None = None,
    equipment: list[dict[str, Any]] | None = None,
    magic_items: list[dict[str, Any]] | None = None,
    damage_types: list[dict[str, Any]] | None = None,
    conditions: list[dict[str, Any]] | None = None,
    skills: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build cross-reference indexes for efficient lookups.

    These indexes enable reverse lookups and relationship queries without
    requiring clients to iterate through all entities.

    Examples:
        - Which spells deal fire damage?
        - Which monsters are immune to poison?
        - Which spells can cause the blinded condition?

    Note: Expects normalized data with full ID prefixes (e.g., "damage:fire").
    """
    xref: dict[str, Any] = {}

    # Damage type cross-references
    if damage_types is not None and (monsters is not None or spells is not None):
        damage_type_ids = {fallback_id(dt) for dt in damage_types if "id" in dt}

        # Spells by damage type
        if spells is not None:
            spells_by_damage: defaultdict[str, list[str]] = defaultdict(list)
            for spell in spells:
                spell_id = fallback_id(spell)
                effects = spell.get("effects", {})
                if isinstance(effects, dict):
                    damage = effects.get("damage", {})
                    if isinstance(damage, dict) and "type_id" in damage:
                        type_id = damage["type_id"]
                        if type_id in damage_type_ids:
                            spells_by_damage[type_id].append(spell_id)

            xref["spells_by_damage_type"] = _sorted_xref_dict(spells_by_damage)

        # Monsters by damage vulnerabilities/resistances/immunities
        if monsters is not None:
            monsters_vulnerable: defaultdict[str, list[str]] = defaultdict(list)
            monsters_resistant: defaultdict[str, list[str]] = defaultdict(list)
            monsters_immune: defaultdict[str, list[str]] = defaultdict(list)

            for monster in monsters:
                monster_id = fallback_id(monster)

                for vuln in monster.get("damage_vulnerabilities", []):
                    if isinstance(vuln, dict) and "type_id" in vuln:
                        type_id = vuln["type_id"]
                        if type_id in damage_type_ids:
                            monsters_vulnerable[type_id].append(monster_id)

                for resist in monster.get("damage_resistances", []):
                    if isinstance(resist, dict) and "type_id" in resist:
                        type_id = resist["type_id"]
                        if type_id in damage_type_ids:
                            monsters_resistant[type_id].append(monster_id)

                for immune in monster.get("damage_immunities", []):
                    if isinstance(immune, dict) and "type_id" in immune:
                        type_id = immune["type_id"]
                        if type_id in damage_type_ids:
                            monsters_immune[type_id].append(monster_id)

            xref["monsters_vulnerable_to_damage_type"] = _sorted_xref_dict(monsters_vulnerable)
            xref["monsters_resistant_to_damage_type"] = _sorted_xref_dict(monsters_resistant)
            xref["monsters_immune_to_damage_type"] = _sorted_xref_dict(monsters_immune)

    # Condition cross-references
    if conditions is not None and (monsters is not None or spells is not None):
        condition_ids = {fallback_id(c) for c in conditions if "id" in c}

        # Spells that inflict conditions
        if spells is not None:
            spells_by_condition: defaultdict[str, list[str]] = defaultdict(list)
            for spell in spells:
                spell_id = fallback_id(spell)
                inflicts = spell.get("inflicts_conditions", [])
                if isinstance(inflicts, list):
                    for item in inflicts:
                        condition_id = item.get("condition_id") if isinstance(item, dict) else item
                        if condition_id and condition_id in condition_ids:
                            spells_by_condition[condition_id].append(spell_id)

            xref["spells_by_condition"] = _sorted_xref_dict(spells_by_condition)

        # Monsters immune to conditions
        if monsters is not None:
            monsters_immune_condition: defaultdict[str, list[str]] = defaultdict(list)
            for monster in monsters:
                monster_id = fallback_id(monster)
                immunities = monster.get("condition_immunities", [])
                if isinstance(immunities, list):
                    for item in immunities:
                        condition_id = item.get("condition_id") if isinstance(item, dict) else item
                        if condition_id and condition_id in condition_ids:
                            monsters_immune_condition[condition_id].append(monster_id)

            xref["monsters_immune_to_condition"] = _sorted_xref_dict(monsters_immune_condition)

    # Skill cross-references
    if skills is not None and equipment is not None:
        skill_ids = {fallback_id(s) for s in skills if "id" in s}

        equipment_by_skill: defaultdict[str, list[str]] = defaultdict(list)
        for item in equipment:
            item_id = fallback_id(item)
            grants_skill = item.get("grants_skill_proficiency")
            if grants_skill and grants_skill in skill_ids:
                equipment_by_skill[grants_skill].append(item_id)

        xref["equipment_by_skill_proficiency"] = _sorted_xref_dict(equipment_by_skill)

    # Magic item to spell cross-references
    if magic_items is not None and spells is not None:
        spell_ids = {fallback_id(s) for s in spells if "id" in s}

        magic_items_by_spell: defaultdict[str, list[str]] = defaultdict(list)
        for item in magic_items:
            item_id = fallback_id(item)
            grants = item.get("grants_spells", [])
            if isinstance(grants, list):
                for spell_ref in grants:
                    if spell_ref in spell_ids:
                        magic_items_by_spell[spell_ref].append(item_id)

        xref["magic_items_by_granted_spell"] = _sorted_xref_dict(magic_items_by_spell)

    return xref


def build_feature_index(features: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical feature lookup tables."""

    by_name, _ = _build_by_name_map(features)
    by_source: defaultdict[str, list[str]] = defaultdict(list)

    for feature in features:
        feature_id = fallback_id(feature)
        source = str(feature.get("source", "unknown"))

        by_source[source].append(feature_id)

    sorted_by_source = _stable_dict(sorted(by_source.items()))

    for key, ids in sorted_by_source.items():
        sorted_by_source[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_source": sorted_by_source,
    }


def build_rule_index(rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical rule lookup tables."""

    by_name, _ = _build_by_name_map(rules)
    by_category: defaultdict[str, list[str]] = defaultdict(list)
    by_subcategory: defaultdict[str, list[str]] = defaultdict(list)

    for rule in rules:
        rule_id = fallback_id(rule)
        category = str(rule.get("category", "unknown"))
        subcategory = rule.get("subcategory")

        by_category[category].append(rule_id)

        if subcategory:
            by_subcategory[str(subcategory)].append(rule_id)

    sorted_by_category = _stable_dict(sorted(by_category.items()))
    sorted_by_subcategory = _stable_dict(sorted(by_subcategory.items()))

    for key, ids in sorted_by_category.items():
        sorted_by_category[key] = sorted(ids)
    for key, ids in sorted_by_subcategory.items():
        sorted_by_subcategory[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_category": sorted_by_category,
        "by_subcategory": sorted_by_subcategory,
    }


def build_indexes(  # noqa: C901, PLR0912, PLR0913, PLR0915
    monsters: list[dict[str, Any]],
    spells: list[dict[str, Any]] | None = None,
    equipment: list[dict[str, Any]] | None = None,
    magic_items: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    lineages: list[dict[str, Any]] | None = None,
    classes: list[dict[str, Any]] | None = None,
    conditions: list[dict[str, Any]] | None = None,
    diseases: list[dict[str, Any]] | None = None,
    poisons: list[dict[str, Any]] | None = None,
    features: list[dict[str, Any]] | None = None,
    rules: list[dict[str, Any]] | None = None,
    damage_types: list[dict[str, Any]] | None = None,
    ability_scores: list[dict[str, Any]] | None = None,
    skills: list[dict[str, Any]] | None = None,
    *,
    display_normalizer: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Aggregate monster, spell, equipment, magic item, table, lineage, class, condition, disease, poison, feature, rule, damage type, ability, skill, and entity indexes for dataset output."""

    # Split into monsters, creatures (MM-A), and NPCs (MM-B) based on ID prefix
    actual_monsters = [m for m in monsters if fallback_id(m).startswith("monster:")]
    misc_creatures = [m for m in monsters if fallback_id(m).startswith("creature:")]
    npcs = [m for m in monsters if fallback_id(m).startswith("npc:")]

    # Build indexes for monsters (main section, pages 261-365)
    monster_indexes = build_monster_index(actual_monsters)
    by_name, name_conflicts = _build_by_name_map(
        actual_monsters, display_normalizer=display_normalizer
    )
    if by_name:
        monster_indexes["by_name"] = by_name
    monster_entity_index = _build_entity_index_for_type(
        actual_monsters, entity_type="monster", file_name="monsters.json"
    )

    # Build indexes for misc creatures (Appendix MM-A, pages 366-394)
    creature_indexes = build_monster_index(misc_creatures)
    creature_by_name, _ = _build_by_name_map(misc_creatures, display_normalizer=display_normalizer)
    if creature_by_name:
        creature_indexes["by_name"] = creature_by_name
    creature_entity_index = _build_entity_index_for_type(
        misc_creatures, entity_type="creature", file_name="monsters.json"
    )

    # Build indexes for NPCs (Appendix MM-B, pages 395-403)
    npc_indexes = build_monster_index(npcs)
    npc_by_name, _ = _build_by_name_map(npcs, display_normalizer=display_normalizer)
    if npc_by_name:
        npc_indexes["by_name"] = npc_by_name
    npc_entity_index = _build_entity_index_for_type(
        npcs, entity_type="npc", file_name="monsters.json"
    )

    # Build entity structure with nested type-specific keys
    entities: dict[str, dict[str, dict[str, str]]] = {
        "monsters": monster_entity_index,
        "creatures": creature_entity_index,
        "npcs": npc_entity_index,
    }

    payload: dict[str, Any] = {
        "monsters": monster_indexes,
        "creatures": creature_indexes,
        "npcs": npc_indexes,
        "entities": entities,
        "stats": {
            "total_monsters": len(actual_monsters),
            "total_creatures": len(misc_creatures),
            "total_npcs": len(npcs),
            "total_all_creatures": len(monsters),  # Combined count
            "total_entities": len(monster_entity_index)
            + len(creature_entity_index)
            + len(npc_entity_index),
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

    # Add magic item indexes if magic_items provided (including empty list)
    if magic_items is not None:
        magic_item_indexes = build_magic_item_index(magic_items)
        magic_item_entity_index = _build_magic_item_entity_index(magic_items)

        payload["magic_items"] = magic_item_indexes
        entities["magic_items"] = magic_item_entity_index
        payload["stats"]["total_magic_items"] = len(magic_items)
        # Recalculate total entities
        total = len(monster_entity_index)
        if spells is not None:
            total += len(spell_entity_index)
        if equipment is not None:
            total += len(equipment_entity_index)
        total += len(magic_item_entity_index)
        payload["stats"]["total_entities"] = total
        payload["stats"]["unique_magic_item_rarities"] = len(magic_item_indexes["by_rarity"])
        payload["stats"]["unique_magic_item_types"] = len(magic_item_indexes["by_type"])

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
        if magic_items is not None:
            total += len(magic_item_entity_index)
        total += len(table_entity_index)
        payload["stats"]["total_entities"] = total
        payload["stats"]["unique_table_categories"] = len(table_indexes["by_category"])

    # Add lineage indexes if lineages provided (including empty list)
    if lineages is not None:
        lineage_indexes = build_lineage_index(lineages)
        lineage_entity_index = _build_lineage_entity_index(lineages)

        payload["lineages"] = lineage_indexes
        entities["lineages"] = lineage_entity_index
        payload["stats"]["total_lineages"] = len(lineages)
        # Recalculate total entities
        total = len(monster_entity_index)
        if spells is not None:
            total += len(spell_entity_index)
        if equipment is not None:
            total += len(equipment_entity_index)
        if magic_items is not None:
            total += len(magic_item_entity_index)
        if tables is not None:
            total += len(table_entity_index)
        total += len(lineage_entity_index)
        payload["stats"]["total_entities"] = total
        payload["stats"]["unique_lineage_sizes"] = len(lineage_indexes["by_size"])
        payload["stats"]["unique_lineage_speeds"] = len(lineage_indexes["by_speed"])

    # Add class indexes if classes provided (including empty list)
    if classes is not None:
        class_indexes = build_class_index(classes)
        class_entity_index = _build_class_entity_index(classes)

        payload["classes"] = class_indexes
        entities["classes"] = class_entity_index
        payload["stats"]["total_classes"] = len(classes)
        # Recalculate total entities
        total = len(monster_entity_index)
        if spells is not None:
            total += len(spell_entity_index)
        if equipment is not None:
            total += len(equipment_entity_index)
        if magic_items is not None:
            total += len(magic_item_entity_index)
        if tables is not None:
            total += len(table_entity_index)
        if lineages is not None:
            total += len(lineage_entity_index)
        total += len(class_entity_index)
        payload["stats"]["total_entities"] = total
        payload["stats"]["unique_hit_dice"] = len(class_indexes["by_hit_die"])
        payload["stats"]["unique_primary_abilities"] = len(class_indexes["by_primary_ability"])

    # Add condition indexes if conditions provided (including empty list)
    if conditions is not None:
        condition_indexes = build_condition_index(conditions)
        condition_entity_index = _build_condition_entity_index(conditions)

        payload["conditions"] = condition_indexes
        entities["conditions"] = condition_entity_index
        payload["stats"]["total_conditions"] = len(conditions)
        # Recalculate total entities
        total = len(monster_entity_index)
        if spells is not None:
            total += len(spell_entity_index)
        if equipment is not None:
            total += len(equipment_entity_index)
        if magic_items is not None:
            total += len(magic_item_entity_index)
        if tables is not None:
            total += len(table_entity_index)
        if lineages is not None:
            total += len(lineage_entity_index)
        if classes is not None:
            total += len(class_entity_index)
        total += len(condition_entity_index)
        payload["stats"]["total_entities"] = total
        payload["stats"]["conditions_with_levels"] = len(
            condition_indexes["by_has_levels"].get("true", [])
        )

    # Add disease indexes if provided
    if diseases is not None:
        disease_entity_index = _build_simple_entity_index(diseases, "disease", "diseases.json")
        by_name, _ = _build_by_name_map(diseases)

        payload["diseases"] = {"by_name": by_name}
        entities["diseases"] = disease_entity_index
        payload["stats"]["total_diseases"] = len(diseases)

    # Add poison indexes if provided
    if poisons is not None:
        poison_entity_index = _build_simple_entity_index(poisons, "poison", "poisons.json")
        by_name, _ = _build_by_name_map(poisons)

        payload["poisons"] = {"by_name": by_name}
        entities["poisons"] = poison_entity_index
        payload["stats"]["total_poisons"] = len(poisons)

    # Add feature indexes if provided
    if features is not None:
        feature_indexes = build_feature_index(features)
        feature_entity_index = _build_simple_entity_index(features, "feature", "features.json")

        payload["features"] = feature_indexes
        entities["features"] = feature_entity_index
        payload["stats"]["total_features"] = len(features)

    # Add rule indexes if provided
    if rules is not None:
        rule_indexes = build_rule_index(rules)
        rule_entity_index = _build_simple_entity_index(rules, "rule", "rules.json")

        payload["rules"] = rule_indexes
        entities["rules"] = rule_entity_index
        payload["stats"]["total_rules"] = len(rules)

    # Add damage_types to entities index if provided
    damage_type_entity_index: dict[str, Any] = {}
    if damage_types is not None:
        damage_type_entity_index = _build_simple_entity_index(
            damage_types, "damage", "damage_types.json"
        )
        by_name, _ = _build_by_name_map(damage_types)
        payload["damage_types"] = {"by_name": by_name}
        entities["damage_types"] = damage_type_entity_index
        payload["stats"]["total_damage_types"] = len(damage_types)

    # Add ability_scores to entities index if provided
    ability_score_entity_index: dict[str, Any] = {}
    if ability_scores is not None:
        ability_score_entity_index = _build_simple_entity_index(
            ability_scores, "ability", "ability_scores.json"
        )
        by_name, _ = _build_by_name_map(ability_scores)
        payload["ability_scores"] = {"by_name": by_name}
        entities["ability_scores"] = ability_score_entity_index
        payload["stats"]["total_ability_scores"] = len(ability_scores)

    # Add skills to entities index if provided
    skill_entity_index: dict[str, Any] = {}
    if skills is not None:
        skill_entity_index = _build_simple_entity_index(skills, "skill", "skills.json")
        by_name, _ = _build_by_name_map(skills)
        payload["skills"] = {"by_name": by_name}
        entities["skills"] = skill_entity_index
        payload["stats"]["total_skills"] = len(skills)

    # Recalculate total entities to include new datasets
    if (
        diseases is not None
        or poisons is not None
        or features is not None
        or rules is not None
        or damage_types is not None
        or ability_scores is not None
        or skills is not None
    ):
        total = len(monster_entity_index)
        if spells is not None:
            total += len(spell_entity_index)
        if equipment is not None:
            total += len(equipment_entity_index)
        if magic_items is not None:
            total += len(magic_item_entity_index)
        if tables is not None:
            total += len(table_entity_index)
        if lineages is not None:
            total += len(lineage_entity_index)
        if classes is not None:
            total += len(class_entity_index)
        if conditions is not None:
            total += len(condition_entity_index)
        if diseases is not None:
            total += len(disease_entity_index)
        if poisons is not None:
            total += len(poison_entity_index)
        if features is not None:
            total += len(feature_entity_index)
        if rules is not None:
            total += len(rule_entity_index)
        if damage_types is not None:
            total += len(damage_type_entity_index)
        if ability_scores is not None:
            total += len(ability_score_entity_index)
        if skills is not None:
            total += len(skill_entity_index)
        payload["stats"]["total_entities"] = total

    if name_conflicts:
        payload["conflicts"] = {"by_name": name_conflicts}

    # Add terminology aliases for categorical mappings
    payload["aliases"] = {
        "races": "lineages",
        "race": "lineage",
    }

    return payload
