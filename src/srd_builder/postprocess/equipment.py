"""Postprocessing helpers for equipment records."""

from __future__ import annotations

from typing import Any

from .ids import normalize_id

__all__ = ["clean_equipment_record"]


def clean_equipment_record(item: dict[str, Any]) -> dict[str, Any]:
    """Run the canonical post-processing pipeline over an equipment record."""

    patched = {**item}

    if "name" in patched and isinstance(patched["name"], str):
        patched["name"] = patched["name"].rstrip(".")

    if "simple_name" in patched and isinstance(patched["simple_name"], str):
        patched["simple_name"] = normalize_id(patched["simple_name"])

    if "properties" in patched and isinstance(patched["properties"], list):
        patched["properties"] = [
            prop.lower().strip() if isinstance(prop, str) else prop
            for prop in patched["properties"]
        ]

    equipment_optional_fields = {
        "properties",
        "sub_category",
        "weapon_type",
        "proficiency",
        "stealth_disadvantage",
        "strength_req",
        "versatile_damage",
        "range",
        "quantity",
        "weight_lb",
        "weight_raw",
        "section",
        "table_header",
        "row_index",
    }

    for key in list(patched.keys()):
        if key not in equipment_optional_fields:
            continue
        value = patched[key]
        if value is None or (isinstance(value, list | str) and not value):
            patched.pop(key)

    return patched
