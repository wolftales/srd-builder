"""Postprocessing helpers for spell records."""

from __future__ import annotations

from typing import Any

from .ids import normalize_id

__all__ = ["clean_spell_record"]


def clean_spell_record(
    spell: dict[str, Any],
    *,
    spell_classes_map: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Run the canonical post-processing pipeline over a spell record.

    Args:
        spell: A single raw spell record.
        spell_classes_map: Mapping of spell ``simple_name`` → sorted list of
            class names that can cast it, as produced by
            :func:`srd_builder.extract.datasets.extract_spell_classes.build_spell_to_classes_map`.
            When ``None`` (default), the ``classes`` field is not attached;
            callers that need it must supply the map.
    """

    patched = {**spell}

    if "simple_name" not in patched and "name" in patched:
        patched["simple_name"] = normalize_id(patched["name"])

    if "simple_name" in patched and isinstance(patched["simple_name"], str):
        patched["simple_name"] = normalize_id(patched["simple_name"])

    if "id" not in patched and "simple_name" in patched:
        patched["id"] = f"spell:{patched['simple_name']}"

    if "school" in patched and isinstance(patched["school"], str):
        patched["school"] = patched["school"].lower()

    if spell_classes_map is not None and "simple_name" in patched:
        classes = spell_classes_map.get(patched["simple_name"])
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
        if value is None or (isinstance(value, list | dict | str) and not value):
            patched.pop(key)

    return patched
