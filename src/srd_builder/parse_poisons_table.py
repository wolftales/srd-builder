"""Parse poison table data into individual poison item records.

This module takes raw poison table rows from table extraction
and returns individual poison items (equipment-style records).

KNOWN LIMITATION: Poison descriptions are manually maintained in
data/poison_descriptions_manual.py due to corrupted PDF text on pages 204-205.
"""

from __future__ import annotations

import re
from typing import Any

from .data.poison_descriptions_manual import POISON_DESCRIPTIONS
from .postprocess import normalize_id


def parse_poisons_table(
    table: dict[str, Any], descriptions: dict[str, dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Parse poison table into list of individual poison item records.

    Args:
        table: Raw poison table from table extraction with rows [[name, type, price], ...]
        descriptions: Optional dict mapping simple_name to {description, save, damage}

    Returns:
        List of poison items with equipment-style structure (id, name, category, cost, description, etc.)
    """
    rows = table.get("rows", [])
    page = table.get("page", 204)

    # Filter out header rows
    data_rows = _filter_header_rows(rows)

    # Optional: map descriptions by simple_name
    descriptions_map = descriptions or {}

    # Build individual poison item records
    poisons = []
    for idx, row in enumerate(data_rows):
        if len(row) >= 3:
            name = row[0]
            poison_type = row[1]  # Ingested, Inhaled, Injury, Contact
            price_str = row[2]

            simple_name = normalize_id(name)

            # Parse cost from price string (e.g., "150 gp" -> {"amount": 150, "currency": "gp"})
            cost = _parse_cost(price_str)

            poison = {
                "id": f"poison:{simple_name}",
                "name": name,
                "simple_name": simple_name,
                "page": page,
                "source": "SRD 5.1",
                "source_table": "poisons",
                "row_index": idx,
                "poison_type": poison_type.lower(),  # ingested, inhaled, injury, contact
                "cost": cost,
            }

            # Merge description fields
            # Use manual descriptions (PDF pages 204-205 have corrupted text)
            desc_data = {}
            if simple_name in POISON_DESCRIPTIONS:
                desc_data = POISON_DESCRIPTIONS[simple_name]
            elif simple_name in descriptions_map:
                # Fallback to extracted if manual not available (for future use)
                desc_data = descriptions_map[simple_name]

            # Merge fields into poison record
            if desc_data:
                if "description" in desc_data:
                    poison["description"] = desc_data["description"]
                if "save" in desc_data:
                    poison["save"] = desc_data["save"]
                if "damage" in desc_data:
                    poison["damage"] = desc_data["damage"]

            poisons.append(poison)

    return poisons


def _parse_cost(price_str: str) -> dict[str, Any]:
    """Parse price string into cost dict.

    Args:
        price_str: Price string like "150 gp" or "500 gp"

    Returns:
        Dict with amount and currency, e.g., {"amount": 150, "currency": "gp"}
    """
    # Match patterns like "150 gp", "2,000 gp", etc.
    match = re.match(r"([\d,]+)\s*(\w+)", price_str.strip())
    if match:
        amount_str = match.group(1).replace(",", "")
        currency = match.group(2)
        try:
            amount = int(amount_str)
            return {"amount": amount, "currency": currency}
        except ValueError:
            pass

    # Fallback: return raw string
    return {"amount": 0, "currency": "gp", "raw": price_str}


def _filter_header_rows(rows: list[list[str]]) -> list[list[str]]:
    """Remove header rows from table data.

    Filters out rows where columns match header keywords.

    Args:
        rows: Raw table rows

    Returns:
        Filtered rows without headers
    """
    return [
        row
        for row in rows
        if len(row) >= 3
        and row[0].strip()
        and row[0].lower() != "item"
        and "type" not in row[1].lower()
    ]
