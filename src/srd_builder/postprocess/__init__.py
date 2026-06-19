"""Domain-specific postprocessing helpers for SRD datasets.

12 simple datasets are normalized by the config-driven engine
(see `engine.clean_records` + `configs.DATASET_CONFIGS`). The 4 datasets
re-exported here (monsters, equipment, spells, rules) keep custom
per-record cleaners because they carry real domain logic or take extra
kwargs the engine cannot model.
"""

from .equipment import clean_equipment_record
from .ids import normalize_id
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
from .rules import clean_rule_record
from .spells import clean_spell_record
from .text import polish_text, polish_text_fields

__all__ = [
    "add_ability_modifiers",
    "clean_equipment_record",
    "clean_monster_record",
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
