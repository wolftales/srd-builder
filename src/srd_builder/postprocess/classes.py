"""Postprocess class records to ensure consistent normalization.

GUARDRAILS: Pure transformation (no I/O/logging)
BOUNDARIES: Receives parsed classes → returns normalized classes
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text


def clean_class_record(cls: dict[str, Any]) -> dict[str, Any]:
    """Normalize class record with IDs and polished text.

    Args:
        cls: Parsed class record (may or may not have id/simple_name)

    Returns:
        Normalized class with guaranteed id, simple_name, and polished text
    """
    # Ensure simple_name (normalize from name if missing)
    if "simple_name" not in cls:
        cls["simple_name"] = normalize_id(cls["name"])

    # Ensure id format
    if "id" not in cls:
        cls["id"] = f"class:{cls['simple_name']}"

    # Polish text fields
    if "description" in cls and isinstance(cls["description"], str):
        cls["description"] = polish_text(cls["description"])

    # Polish hit_die_description (if present)
    if "hit_die_description" in cls and isinstance(cls["hit_die_description"], str):
        cls["hit_die_description"] = polish_text(cls["hit_die_description"])

    # Polish proficiencies (if present)
    if "proficiencies" in cls:
        cls["proficiencies"] = _polish_proficiencies(cls["proficiencies"])

    # Polish equipment (if present)
    if "equipment" in cls and isinstance(cls["equipment"], list):
        cls["equipment"] = [polish_text(e) if isinstance(e, str) else e for e in cls["equipment"]]

    return cls


def _polish_proficiencies(prof: dict[str, Any]) -> dict[str, Any]:
    """Polish proficiencies text fields."""
    for key in ["armor", "weapons", "tools", "saving_throws", "skills"]:
        if key in prof and isinstance(prof[key], list):
            prof[key] = [polish_text(item) if isinstance(item, str) else item for item in prof[key]]
    return prof
