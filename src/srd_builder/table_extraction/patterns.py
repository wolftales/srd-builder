"""Unified table extraction engine.

This module contains a single extraction function that interprets table configs
from reference_data.py. The config structure dictates the extraction behavior,
eliminating the need for pattern-specific extraction methods.

Design Philosophy:
- Data shapes extraction logic (not code)
- One engine handles all patterns
- Config metadata defines extraction rules
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RawTable:
    """Raw extracted table data before normalization."""

    table_id: str
    simple_name: str
    page: int | list[int]
    headers: list[str]
    rows: list[list[str | int | float]]
    extraction_method: str
    section: str | None = None
    notes: str | None = None


def extract_by_config(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None = None,
) -> RawTable:
    """Universal table extraction based on config structure.

    The config dict defines how to extract the table:

    1. **Static rows** - Config has "rows" key with hardcoded data:
       ```python
       config = {
           "headers": ["CR", "XP"],
           "rows": [["0", 0], ["1/8", 25], ...]
       }
       ```

    2. **Calculated rows** - Config has "formula" or "data" with generation logic:
       ```python
       # Formula-based (ability scores)
       config = {
           "formula": lambda score: (score - 10) // 2,
           "range": range(1, 31),
           "headers": ["Score", "Modifier"]
       }

       # Lookup-based (proficiency bonus)
       config = {
           "data": {
               range(1, 5): "+2",
               range(5, 9): "+3",
               ...
           },
           "headers": ["Level", "Bonus"]
       }
       ```

    3. **Metadata enrichment** - Config can have "notes" for additional context

    Args:
        table_id: Unique table identifier (e.g., "table:barbarian_progression")
        simple_name: Simple name (e.g., "barbarian_progression")
        page: Source page number(s)
        config: Table configuration dict from reference_data
        section: Optional section name

    Returns:
        RawTable with extracted data
    """
    # Determine extraction type from config structure
    if "rows" in config:
        # Static data - config explicitly provides rows
        rows = config["rows"]
        extraction_method = "reference"
        notes = config.get("notes", "Reference data from SRD 5.1")

    elif "formula" in config:
        # Formula-based calculation (ability scores, carrying capacity)
        rows = _generate_formula_rows(config)
        extraction_method = "calculated"
        notes = config.get("notes", "Calculated from formula")

    elif "data" in config:
        # Lookup-based calculation (proficiency bonus)
        rows = _generate_lookup_rows(config)
        extraction_method = "calculated"
        notes = config.get("notes", "Calculated from lookup table")

    else:
        raise ValueError(
            f"Invalid config for {simple_name}: must have 'rows', 'formula', or 'data'"
        )

    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page,
        headers=config["headers"],
        rows=rows,
        extraction_method=extraction_method,
        section=section,
        notes=notes,
    )


def _generate_formula_rows(config: dict[str, Any]) -> list[list[str | int | float]]:
    """Generate rows from formula config.

    Example config:
        {
            "formula": lambda x: x * 15,
            "range": range(1, 31),
            "headers": ["Strength", "Capacity"],
            "format": lambda val: f"{val} lbs"  # optional
        }
    """
    formula = config["formula"]
    value_range = config["range"]
    format_fn = config.get("format_modifier") or config.get("format", lambda x: x)

    rows: list[list[str | int | float]] = []
    for val in value_range:
        result = formula(val)
        formatted_result = format_fn(result)
        rows.append([val, formatted_result])

    return rows


def _generate_lookup_rows(config: dict[str, Any]) -> list[list[str | int | float]]:
    """Generate rows from lookup dict config.

    Example config:
        {
            "data": {
                range(1, 5): "+2",
                range(5, 9): "+3",
                ...
            },
            "headers": ["Level", "Bonus"]
        }
    """
    lookup = config["data"]
    rows: list[list[str | int | float]] = []

    # Build lookup by iterating ranges
    for range_obj, value in lookup.items():
        for key in range_obj:
            rows.append([key, value])

    return rows
