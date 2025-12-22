"""Postprocess lineage records to ensure consistent normalization.

GUARDRAILS: Pure transformation (no I/O/logging/timestamps)
BOUNDARIES: Receives parsed lineages → returns normalized lineages
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text


def clean_lineage_record(lineage: dict[str, Any]) -> dict[str, Any]:
    """Normalize lineage record with IDs and polished text.

    Args:
        lineage: Parsed lineage record (may or may not have id/simple_name)

    Returns:
        Normalized lineage with guaranteed id, simple_name, and polished text
    """
    # Ensure simple_name (normalize from name if missing)
    if "simple_name" not in lineage:
        lineage["simple_name"] = normalize_id(lineage["name"])

    # Ensure id format
    if "id" not in lineage:
        lineage["id"] = f"lineage:{lineage['simple_name']}"

    # Polish text fields (traits have name + description)
    if "traits" in lineage:
        lineage["traits"] = [_polish_trait(trait) for trait in lineage["traits"]]

    # Polish optional text fields
    for field in ["age", "alignment", "size_description", "ability_modifier_note"]:
        if field in lineage and isinstance(lineage[field], str):
            lineage[field] = polish_text(lineage[field])

    return lineage


def _polish_trait(trait: dict[str, Any]) -> dict[str, Any]:
    """Polish trait name and description."""
    if "name" in trait and isinstance(trait["name"], str):
        trait["name"] = polish_text(trait["name"])

    if "description" in trait and isinstance(trait["description"], str):
        trait["description"] = polish_text(trait["description"])

    return trait
