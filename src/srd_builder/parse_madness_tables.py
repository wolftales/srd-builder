"""Parse raw madness table data extracted from SRD PDF.

This module takes the raw madness table rows and parses them into
structured madness table records (one per madness type).

Output: 3 table records with rows arrays, matching tables.json schema.
"""

from __future__ import annotations

from typing import Any


def parse_madness_tables(tables_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse raw madness tables into 3 structured table records.

    Args:
        tables_data: Dict with table data keyed by simple_name

    Returns:
        List of 3 madness table records (short-term, long-term, indefinite)
    """
    madness_tables = []

    # 1. Short-Term Madness (merge parts 1 and 2)
    short_term_part1 = tables_data.get("short_term_madness", {})
    short_term_part2 = tables_data.get("short_term_madness_part2", {})

    short_term_rows = _filter_header_rows(short_term_part1.get("rows", [])) + _filter_header_rows(
        short_term_part2.get("rows", [])
    )

    if short_term_rows:
        madness_tables.append(
            {
                "id": "madness:short_term",
                "name": "Short-Term Madness",
                "simple_name": "short_term_madness",
                "page": short_term_part1.get("page", 201),
                "source": "SRD 5.1",
                "duration": "1d10 minutes",
                "columns": [
                    {"name": "d100", "type": "string"},
                    {"name": "Effect", "type": "string"},
                ],
                "rows": [[row[0], _clean_effect_text(row[1])] for row in short_term_rows],
            }
        )

    # 2. Long-Term Madness
    long_term_table = tables_data.get("long_term_madness", {})
    long_term_rows = _filter_header_rows(long_term_table.get("rows", []))

    if long_term_rows:
        madness_tables.append(
            {
                "id": "madness:long_term",
                "name": "Long-Term Madness",
                "simple_name": "long_term_madness",
                "page": long_term_table.get("page", 201),
                "source": "SRD 5.1",
                "duration": "1d10 × 10 hours",
                "columns": [
                    {"name": "d100", "type": "string"},
                    {"name": "Effect", "type": "string"},
                ],
                "rows": [[row[0], _clean_effect_text(row[1])] for row in long_term_rows],
            }
        )

    # 3. Indefinite Madness
    indefinite_table = tables_data.get("indefinite_madness", {})
    indefinite_rows = _filter_header_rows(indefinite_table.get("rows", []))

    if indefinite_rows:
        madness_tables.append(
            {
                "id": "madness:indefinite",
                "name": "Indefinite Madness",
                "simple_name": "indefinite_madness",
                "page": indefinite_table.get("page", 202),
                "source": "SRD 5.1",
                "duration": "until cured",
                "columns": [
                    {"name": "d100", "type": "string"},
                    {"name": "Effect", "type": "string"},
                ],
                "rows": [[row[0], _clean_effect_text(row[1])] for row in indefinite_rows],
            }
        )

    return madness_tables


def _filter_header_rows(rows: list[list[str]]) -> list[list[str]]:
    """Filter out header rows that contain 'd100' or 'Effect'."""
    filtered = []
    for row in rows:
        if len(row) >= 2:
            # Skip if first column is 'd100' or contains 'Effect'
            first_col = str(row[0]).lower()
            if first_col == "d100" or "effect" in first_col or "flaw" in first_col:
                continue
            filtered.append(row)
    return filtered


def _clean_effect_text(text: str) -> str:
    """Clean up PDF encoding issues in effect text.

    Args:
        text: Raw effect text from PDF

    Returns:
        Cleaned text
    """
    import re

    # Fix common PDF encoding issues
    text = text.replace("­‐‑", "-")  # Replace garbled dashes
    text = text.replace("­‐", "-")
    text = text.replace("‑", "-")
    text = text.replace("'", "'")  # Fix smart quotes
    text = text.replace(
        """, '"')
    text = text.replace(""",
        '"',
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()
