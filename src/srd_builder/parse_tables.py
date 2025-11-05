#!/usr/bin/env python3
"""Parse and normalize raw table data to schema format.

This module takes raw table data from extract_tables.py and normalizes it
to match the table.schema.json format, including:
- ID validation and normalization
- Column type detection
- Summary generation
- Data type conversion
- Schema compliance validation
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

# CLI constants
MIN_CLI_ARGS = 2  # Minimum command-line arguments required
CLI_OUTPUT_PATH_ARG_INDEX = 2  # Index of optional output path in sys.argv

try:
    from scripts.table_targets import TARGET_TABLES
except ModuleNotFoundError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from scripts.table_targets import TARGET_TABLES

logger = logging.getLogger(__name__)


def detect_column_type(values: list[Any]) -> str:
    """Detect the type of a column based on its values.

    Args:
        values: List of values from the column

    Returns:
        Type string: "integer", "number", "string", "dice", "range", "mixed"
    """
    if not values:
        return "string"

    # Filter out empty values
    non_empty = [v for v in values if v not in (None, "", 0)]
    if not non_empty:
        return "string"

    # Check if all are integers
    if all(isinstance(v, int) or (isinstance(v, str) and v.isdigit()) for v in non_empty):
        return "integer"

    # Check if all are numbers
    if all(isinstance(v, int | float) for v in non_empty):
        return "number"

    # Check for dice notation (e.g., "1d6", "2d8+3")
    dice_pattern = re.compile(r"^\d+d\d+(?:[+-]\d+)?$", re.IGNORECASE)
    if all(isinstance(v, str) and dice_pattern.match(v) for v in non_empty):
        return "dice"

    # Check for ranges (e.g., "1-5", "10-20", "1st-4th")
    range_pattern = re.compile(r"^\d+(?:st|nd|rd|th)?[-–]\d+(?:st|nd|rd|th)?$", re.IGNORECASE)
    if all(isinstance(v, str) and range_pattern.match(v) for v in non_empty):
        return "range"

    # Check for mixed numeric and string
    has_numbers = any(isinstance(v, int | float) for v in non_empty)
    has_strings = any(isinstance(v, str) for v in non_empty)
    if has_numbers and has_strings:
        return "mixed"

    return "string"


def parse_tables(raw_tables_path: str | Path, output_path: str | Path) -> list[dict[str, Any]]:
    """Parse raw tables and normalize to schema format.

    Args:
        raw_tables_path: Path to tables_raw.json
        output_path: Path to save tables.json

    Returns:
        List of normalized table dictionaries
    """
    raw_tables_path = Path(raw_tables_path)
    output_path = Path(output_path)

    # Load raw tables
    with open(raw_tables_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    raw_tables = raw_data["tables"]
    logger.info(f"Loaded {len(raw_tables)} raw tables from {raw_tables_path}")

    # Load target metadata
    targets_by_id = {t["id"]: t for t in TARGET_TABLES}

    # Parse each table
    parsed_tables = []
    for raw in raw_tables:
        try:
            parsed = parse_single_table(raw, targets_by_id)
            parsed_tables.append(parsed)
            logger.info(f"  ✓ Parsed: {parsed['simple_name']}")
        except Exception as e:
            logger.error(f"  ✗ Failed to parse {raw['simple_name']}: {e}")
            raise

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_tables, f, indent=2, ensure_ascii=False)

    logger.info(f"\nSaved {len(parsed_tables)} tables to {output_path}")
    return parsed_tables


def parse_single_table(raw: dict[str, Any], targets_by_id: dict[str, Any]) -> dict[str, Any]:
    """Parse a single raw table to schema format.

    Args:
        raw: Raw table data
        targets_by_id: Dictionary of target metadata by table ID

    Returns:
        Normalized table dictionary
    """
    table_id = raw["table_id"]
    target = targets_by_id.get(table_id, {})

    # Detect column types
    columns = []
    for i, header in enumerate(raw["headers"]):
        # Get all values for this column
        col_values = [row[i] if i < len(row) else None for row in raw["rows"]]
        col_type = detect_column_type(col_values)

        columns.append(
            {
                "name": header,
                "type": col_type,
            }
        )

    # Build normalized table
    parsed = {
        "id": table_id,
        "simple_name": raw["simple_name"],
        "name": target.get("name", raw["simple_name"].replace("_", " ").title()),
        "columns": columns,
        "rows": raw["rows"],
        "page": raw["page"],
        "category": target.get("category", "reference"),
    }

    # Add optional fields
    if target.get("section"):
        parsed["section"] = target["section"]

    if raw.get("notes"):
        parsed["notes"] = raw["notes"]

    # Add metadata if present (e.g., category information for adventure gear)
    if raw.get("metadata"):
        parsed["metadata"] = raw["metadata"]

    # Generate summary if target has one
    if target.get("notes"):
        # Use the target notes as a summary
        parsed["summary"] = target["notes"]

    return parsed


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < MIN_CLI_ARGS:
        print("Usage: python -m srd_builder.parse_tables <raw_tables.json> [output.json]")
        sys.exit(1)

    raw_path = sys.argv[1]
    output_path = (
        sys.argv[CLI_OUTPUT_PATH_ARG_INDEX]
        if len(sys.argv) > CLI_OUTPUT_PATH_ARG_INDEX
        else "tables.json"
    )

    parse_tables(raw_path, output_path)
    print(f"\n✓ Parsing complete: {output_path}")
