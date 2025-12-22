"""Domain-specific postprocessing helpers for SRD datasets."""

from .conditions import clean_condition_record
from .diseases import clean_disease_record
from .equipment import clean_equipment_record
from .ids import normalize_id
from .lineages import clean_lineage_record
from .magic_items import clean_magic_item_record
from .monsters import (
    add_ability_modifiers,
    clean_monster_record,
    dedup_defensive_lists,
    parse_action_structures,
    prune_empty_fields,
    rename_abilities_to_traits,
    split_legendary,
    standardize_challenge,
    structure_defenses,
    unify_simple_name,
)
from .poisons import clean_poison_record
from .rules import clean_rule_record
from .spells import clean_spell_record
from .text import polish_text, polish_text_fields

__all__ = [
    "add_ability_modifiers",
    "clean_condition_record",
    "clean_disease_record",
    "clean_equipment_record",
    "clean_lineage_record",
    "clean_magic_item_record",
    "clean_monster_record",
    "clean_poison_record",
    "clean_rule_record",
    "clean_spell_record",
    "dedup_defensive_lists",
    "normalize_id",
    "parse_action_structures",
    "polish_text",
    "polish_text_fields",
    "prune_empty_fields",
    "rename_abilities_to_traits",
    "split_legendary",
    "standardize_challenge",
    "structure_defenses",
    "unify_simple_name",
]
