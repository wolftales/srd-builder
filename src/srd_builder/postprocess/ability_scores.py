"""Postprocess ability_scores dataset."""

from __future__ import annotations

from .ids import normalize_id
from .text import polish_text


def clean_ability_score_record(record: dict) -> dict:
    """Clean and normalize a single ability score record.

    Args:
        record: Raw ability score record from parse layer

    Returns:
        Cleaned ability score record
    """
    # The ID is already in "ability:simple_name" format from parse layer
    # We normalize to ensure consistent format
    if ":" in record["id"]:
        prefix, name = record["id"].split(":", 1)
        record["id"] = f"{prefix}:{normalize_id(name)}"

    # Polish description text
    if "description" in record:
        record["description"] = [polish_text(p) for p in record["description"]]

    return record
