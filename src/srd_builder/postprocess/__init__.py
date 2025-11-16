"""Domain-specific postprocessing helpers for SRD datasets."""

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
from .spells import clean_spell_record
from .text import polish_text, polish_text_fields

__all__ = [
    "add_ability_modifiers",
    "clean_equipment_record",
    "clean_monster_record",
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
