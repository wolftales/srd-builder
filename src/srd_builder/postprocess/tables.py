"""Postprocess table records to ensure consistent normalization.

GUARDRAILS: Pure transformation (no I/O/logging)
BOUNDARIES: Receives parsed tables → returns normalized tables
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import polish_text


def clean_table_record(table: dict[str, Any]) -> dict[str, Any]:
    """Normalize table record with IDs and polished text.

    Args:
        table: Parsed table record (may or may not have id/simple_name)

    Returns:
        Normalized table with guaranteed id, simple_name, and polished text
    """
    # Ensure simple_name (normalize from name if missing)
    if "simple_name" not in table:
        table["simple_name"] = normalize_id(table["name"])

    # Ensure id format
    if "id" not in table:
        table["id"] = f"table:{table['simple_name']}"

    # Polish text fields
    if "name" in table and isinstance(table["name"], str):
        table["name"] = polish_text(table["name"])

    # Polish headers and cells (tables have structure with headers + rows)
    if "headers" in table and isinstance(table["headers"], list):
        table["headers"] = [polish_text(h) if isinstance(h, str) else h for h in table["headers"]]

    if "rows" in table and isinstance(table["rows"], list):
        table["rows"] = [_polish_row(row) for row in table["rows"]]

    return table


def _polish_row(row: list[Any]) -> list[Any]:
    """Polish each cell in a table row."""
    return [polish_text(cell) if isinstance(cell, str) else cell for cell in row]
