"""Postprocessing helpers specific to magic items."""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text

__all__ = ["clean_magic_item_record"]


def clean_magic_item_record(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize and clean a single magic item record.

    Args:
        item: Raw parsed magic item dict

    Returns:
        Cleaned magic item dict with normalized IDs and polished text
    """
    cleaned = {**item}

    # Generate normalized IDs using shared utility
    name = cleaned.get("name", "")
    if name:
        # Remove trailing periods from name
        name = name.rstrip(".")
        cleaned["name"] = name

        # Generate simple_name and ID using shared normalize_id()
        simple_name = normalize_id(name)
        cleaned["simple_name"] = simple_name
        cleaned["id"] = f"magic_item:{simple_name}"

    # Polish description text
    description = cleaned.get("description")
    if description and isinstance(description, list):
        cleaned["description"] = [polish_text(para) for para in description]

    # Polish attunement requirements if present
    if "attunement_requirements" in cleaned:
        req = cleaned["attunement_requirements"]
        if isinstance(req, str):
            cleaned["attunement_requirements"] = polish_text(req)

    return cleaned
