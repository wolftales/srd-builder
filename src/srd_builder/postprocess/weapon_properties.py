"""Postprocess weapon_properties dataset."""

from __future__ import annotations

from .ids import normalize_id
from .text import polish_text


def clean_weapon_property_record(record: dict) -> dict:
    """Clean and normalize a single weapon property record.

    Args:
        record: Raw weapon property record from parse layer

    Returns:
        Cleaned weapon property record
    """
    # The ID is already in "weapon_property:simple_name" format from parse layer
    # We normalize to ensure consistent format
    if ":" in record["id"]:
        prefix, name = record["id"].split(":", 1)
        record["id"] = f"{prefix}:{normalize_id(name)}"

    # Polish description text
    if "description" in record:
        record["description"] = [polish_text(p) for p in record["description"]]

    return record
