"""Postprocess damage_types dataset."""

from __future__ import annotations

from .ids import normalize_id
from .text import polish_text


def clean_damage_type_record(record: dict) -> dict:
    """Clean and normalize a single damage type record.

    Args:
        record: Raw damage type record from parse layer

    Returns:
        Cleaned damage type record
    """
    # The ID is already in "damage_type:simple_name" format from parse layer
    # We normalize to ensure consistent format
    if ":" in record["id"]:
        prefix, name = record["id"].split(":", 1)
        record["id"] = f"{prefix}:{normalize_id(name)}"

    # Polish description text
    if "description" in record:
        record["description"] = [polish_text(p) for p in record["description"]]

    return record
