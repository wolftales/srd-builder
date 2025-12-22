"""Postprocess condition records.

This module normalizes parsed condition data using shared utilities.
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text


def clean_condition_record(condition: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single condition record using shared utilities.

    Postprocess stage: Add id/simple_name if missing, polish text fields.

    Args:
        condition: Raw condition dict from parse stage

    Returns:
        Normalized condition with consistent id/simple_name and polished text
    """
    # Ensure id and simple_name are present
    if "simple_name" not in condition:
        condition["simple_name"] = normalize_id(condition["name"])
    if "id" not in condition:
        condition["id"] = f"condition:{condition['simple_name']}"

    # Polish text fields
    if "description" in condition and isinstance(condition["description"], str):
        condition["description"] = polish_text(condition["description"])

    if "summary" in condition and isinstance(condition["summary"], str):
        condition["summary"] = polish_text(condition["summary"])

    # Polish effects array if present
    if "effects" in condition and isinstance(condition["effects"], list):
        condition["effects"] = [
            polish_text(e) if isinstance(e, str) else e for e in condition["effects"]
        ]

    return condition
