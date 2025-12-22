"""Postprocess feature records to ensure consistent normalization.

GUARDRAILS: Pure transformation (no I/O/logging)
BOUNDARIES: Receives parsed features → returns normalized features
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text


def clean_feature_record(feature: dict[str, Any]) -> dict[str, Any]:
    """Normalize feature record with IDs and polished text.

    Args:
        feature: Parsed feature record (may or may not have id/simple_name)

    Returns:
        Normalized feature with guaranteed id, simple_name, and polished text
    """
    # Ensure simple_name (normalize from name if missing)
    if "simple_name" not in feature:
        feature["simple_name"] = normalize_id(feature["name"])

    # Ensure id format
    if "id" not in feature:
        feature["id"] = f"feature:{feature['simple_name']}"

    # Polish text fields
    if "summary" in feature and isinstance(feature["summary"], str):
        feature["summary"] = polish_text(feature["summary"])

    if "text" in feature and isinstance(feature["text"], str):
        feature["text"] = polish_text(feature["text"])

    return feature
