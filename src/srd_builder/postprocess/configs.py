"""
Configuration for dataset record normalization.

Each dataset has a RecordConfig specifying how to normalize its records.
This declarative approach eliminates duplicate normalization logic.

Adding a new dataset:
    1. Add entry to DATASET_CONFIGS
    2. Specify id_prefix, text_fields, nested_structures
    3. Optionally provide custom_transform for special cases

Example:
    "poison": RecordConfig(
        id_prefix="poison",
        text_fields=["description"],
    )
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecordConfig:
    """
    Configuration for normalizing a dataset's records.

    Attributes:
        id_prefix: Prefix for generated IDs (e.g., "monster" → "monster:giant_rat")
        name_field: Field to derive simple_name from (default: "name")
        text_fields: Top-level string fields to polish
        text_arrays: Top-level list fields where each element is text to polish
        nested_structures: Dict of field → subfields, for lists of dicts
        custom_transform: Optional function for dataset-specific logic
    """

    id_prefix: str
    name_field: str = "name"
    text_fields: list[str] = field(default_factory=list)
    text_arrays: list[str] = field(default_factory=list)
    nested_structures: dict[str, list[str]] = field(default_factory=dict)
    custom_transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None


# ============================================================================
# Dataset Configurations
# ============================================================================

DATASET_CONFIGS = {
    # Simple datasets (text fields only)
    "poison": RecordConfig(
        id_prefix="poison",
        text_fields=["description"],
    ),
    "disease": RecordConfig(
        id_prefix="disease",
        text_fields=["description", "summary"],
        text_arrays=["effects"],
    ),
    "condition": RecordConfig(
        id_prefix="condition",
        text_fields=["description", "summary"],
        text_arrays=["effects"],
    ),
    "feature": RecordConfig(
        id_prefix="feature",
        text_fields=["summary", "text"],
    ),
    # Complex datasets (nested structures)
    "lineage": RecordConfig(
        id_prefix="lineage",
        text_fields=["age", "alignment", "size_description", "ability_modifier_note"],
        nested_structures={
            "traits": ["name", "description"],
        },
    ),
    "table": RecordConfig(
        id_prefix="table",
        text_fields=["name"],
        text_arrays=["headers"],
        nested_structures={
            "rows": [],  # Rows are lists of strings, handled specially
        },
    ),
    "class": RecordConfig(
        id_prefix="class",
        text_fields=["description", "hit_die_description"],
        text_arrays=["equipment"],
        nested_structures={
            "proficiencies.armor": [],
            "proficiencies.weapons": [],
            "proficiencies.tools": [],
            "proficiencies.saving_throws": [],
            "proficiencies.skills": [],
        },
    ),
    # NOTE: Monster, spell, equipment, magic_item, rule configs
    # would go here once we migrate those modules to engine
}


# ============================================================================
# Custom Transformations (Escape Hatch)
# ============================================================================


def _clean_table_rows(table: dict[str, Any]) -> dict[str, Any]:
    """Custom logic for table rows (list of list of strings)."""
    from .text import polish_text

    if "rows" in table:
        table["rows"] = [
            [polish_text(cell) if isinstance(cell, str) else cell for cell in row]
            for row in table["rows"]
        ]
    return table


def _clean_class_proficiencies(cls: dict[str, Any]) -> dict[str, Any]:
    """Custom logic for class proficiencies (nested dict)."""
    if "proficiencies" in cls:
        prof = cls["proficiencies"]
        for key in ["armor", "weapons", "tools", "saving_throws", "skills"]:
            if key in prof and isinstance(prof[key], list):
                from .text import polish_text

                prof[key] = [
                    polish_text(item) if isinstance(item, str) else item for item in prof[key]
                ]
    return cls


# Attach custom transforms to configs
DATASET_CONFIGS["table"].custom_transform = _clean_table_rows
DATASET_CONFIGS["class"].custom_transform = _clean_class_proficiencies
