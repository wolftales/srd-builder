"""Postprocess disease records.

This module normalizes parsed disease data using shared utilities.
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text


def clean_disease_record(disease: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single disease record using shared utilities.

    Postprocess stage: Add id/simple_name if missing, polish text fields.

    Args:
        disease: Raw disease dict from parse stage

    Returns:
        Normalized disease with consistent id/simple_name and polished text
    """
    # Ensure id and simple_name are present
    if "simple_name" not in disease:
        disease["simple_name"] = normalize_id(disease["name"])
    if "id" not in disease:
        disease["id"] = f"disease:{disease['simple_name']}"

    # Polish text fields
    if "description" in disease and isinstance(disease["description"], str):
        disease["description"] = polish_text(disease["description"])

    if "summary" in disease and isinstance(disease["summary"], str):
        disease["summary"] = polish_text(disease["summary"])

    # Polish effects array if present
    if "effects" in disease and isinstance(disease["effects"], list):
        disease["effects"] = [
            polish_text(e) if isinstance(e, str) else e for e in disease["effects"]
        ]

    return disease
