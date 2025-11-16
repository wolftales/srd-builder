"""Postprocessing helpers for spell records."""

from __future__ import annotations

from typing import Any

from srd_builder.spell_class_targets import get_spell_classes

from .ids import normalize_id

__all__ = ["clean_spell_record"]


def clean_spell_record(spell: dict[str, Any]) -> dict[str, Any]:
    """Run the canonical post-processing pipeline over a spell record."""

    patched = {**spell}

    if "simple_name" not in patched and "name" in patched:
        patched["simple_name"] = normalize_id(patched["name"])

    if "simple_name" in patched and isinstance(patched["simple_name"], str):
        patched["simple_name"] = normalize_id(patched["simple_name"])

    if "id" not in patched and "simple_name" in patched:
        patched["id"] = f"spell:{patched['simple_name']}"

    if "school" in patched and isinstance(patched["school"], str):
        patched["school"] = patched["school"].lower()

    if "simple_name" in patched:
        classes = get_spell_classes(patched["simple_name"])
        if classes:
            patched["classes"] = classes

    spell_optional_fields = {
        "effects",
        "scaling",
        "classes",
        "source",
        "summary",
    }

    for key in list(patched.keys()):
        if key not in spell_optional_fields:
            continue
        value = patched[key]
        if value is None or (isinstance(value, (list, dict, str)) and not value):
            patched.pop(key)

    return patched
