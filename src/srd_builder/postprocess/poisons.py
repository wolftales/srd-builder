"""Postprocess poison records.

This module normalizes parsed poison data using shared utilities.
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text


def clean_poison_record(poison: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single poison record using shared utilities.

    Postprocess stage: Add id/simple_name if missing, polish text fields.

    Args:
        poison: Raw poison dict from parse stage

    Returns:
        Normalized poison with consistent id/simple_name and polished text
    """
    # Ensure id and simple_name are present
    if "simple_name" not in poison:
        poison["simple_name"] = normalize_id(poison["name"])
    if "id" not in poison:
        poison["id"] = f"poison:{poison['simple_name']}"

    # Polish text fields
    if "description" in poison and isinstance(poison["description"], str):
        poison["description"] = polish_text(poison["description"])

    return poison
