"""Text-based table parser for SRD 5.1.

Extracts tables from PDF text by analyzing word positions and grouping into rows/columns.
Used for tables that lack grid borders and aren't detected by PyMuPDF's table detection.
"""

from collections import defaultdict
from typing import Any

import pymupdf

# Coordinate grouping tolerance (pixels)
# Words within this Y-distance are considered on the same horizontal line
Y_GROUPING_TOLERANCE = 2


def _extract_rows_by_coordinate(pdf_path: str, pages: list[int]) -> list[list[str]]:
    """Extract all text rows from PDF pages using coordinate analysis.

    Groups words by Y-coordinate (horizontal lines) and sorts by X-coordinate
    (left to right) to reconstruct table structure.

    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers (1-indexed)

    Returns:
        List of rows, where each row is a list of words in left-to-right order
    """
    doc = pymupdf.open(pdf_path)
    all_rows = []

    for page_num in pages:
        page = doc[page_num - 1]  # Convert to 0-indexed
        words = page.get_text("words")

        # Group words by y-coordinate (rows)
        rows_dict = defaultdict(list)
        for word in words:
            x0, y0, x1, y1, text, *_ = word
            # Round y to group words on same horizontal line
            y_key = round(y0 / Y_GROUPING_TOLERANCE) * Y_GROUPING_TOLERANCE
            rows_dict[y_key].append((x0, text))

        # Sort rows by y-position (top to bottom)
        for y_pos in sorted(rows_dict.keys()):
            # Sort words by x-position (left to right)
            row_words = sorted(rows_dict[y_pos], key=lambda w: w[0])
            word_list = [w[1] for w in row_words]
            all_rows.append(word_list)

    doc.close()
    return all_rows


def parse_armor_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse armor table from PDF.

    Armor rows contain 'gp' (cost) and have 8-15 words.

    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers containing armor table

    Returns:
        Dict with structured armor table data including headers and parsed rows
    """
    # Extract all rows using coordinate analysis
    all_rows = _extract_rows_by_coordinate(pdf_path, pages)

    # Filter for armor rows (have 'gp' cost marker and reasonable word count)
    armor_rows = [row for row in all_rows if "gp" in row and 8 <= len(row) <= 15]

    # Define headers
    headers = [
        "Armor",
        "Cost",
        "Armor Class (AC)",
        "Strength",
        "Stealth",
        "Weight",
    ]

    # Parse rows into structured format
    parsed_rows: list[list[str]] = []
    for words in armor_rows:
        row = _parse_armor_row(words)
        if row is not None:
            parsed_rows.append(row)

    # Validate expected armor count (SRD 5.1 has 13: 3 light + 6 medium + 4 heavy)
    if len(parsed_rows) != 13:
        import logging

        logging.warning(
            f"Expected 13 armor items, found {len(parsed_rows)}. " f"Extraction may be incomplete."
        )

    return {
        "headers": headers,
        "rows": parsed_rows,
    }


def _parse_armor_row(words: list[str]) -> list[str] | None:
    """Parse armor row words into structured columns."""
    try:
        # Find key positions
        gp_idx = words.index("gp")
        lb_idx = words.index("lb.")

        # Name: everything before cost number
        name_parts = words[: gp_idx - 1]
        name = " ".join(name_parts)

        # Cost: number + gp
        cost = f"{words[gp_idx - 1]} gp"

        # Weight: number + lb. (at end)
        weight = f"{words[lb_idx - 1]} lb."

        # AC: between cost and weight
        ac_parts = words[gp_idx + 1 : lb_idx - 1]

        # Stealth: "Disadvantage" or "—"
        stealth = "Disadvantage" if "Disadvantage" in ac_parts else "—"
        if stealth == "Disadvantage":
            ac_parts.remove("Disadvantage")

        # Strength: "Str XX" or "—"
        strength = "—"
        if "Str" in ac_parts:
            str_idx = ac_parts.index("Str")
            strength = f"Str {ac_parts[str_idx + 1]}"
            ac_parts = ac_parts[:str_idx] + ac_parts[str_idx + 2 :]

        # Remove trailing "—" symbols from AC (they're for empty strength/stealth columns)
        while ac_parts and ac_parts[-1] == "—":
            ac_parts.pop()

        # AC: remaining parts
        ac = " ".join(ac_parts)

        return [name, cost, ac, strength, stealth, weight]

    except (ValueError, IndexError):
        return None


def parse_weapons_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse weapons table from PDF.

    Weapon rows have cost markers (gp/sp/cp) and damage indicators.

    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers containing weapons table

    Returns:
        Dict with structured weapons table data including headers and parsed rows
    """
    # Extract all rows using coordinate analysis
    all_rows = _extract_rows_by_coordinate(pdf_path, pages)

    # Filter for weapon rows (have cost AND damage indicators)
    weapon_rows = []
    for row in all_rows:
        has_cost = any(x in row for x in ["gp", "sp", "cp"])
        has_damage = any("d" in x or x in ["bludgeoning", "piercing", "slashing"] for x in row)
        if has_cost and (has_damage or "—" in row):
            weapon_rows.append(row)

    # Define headers
    headers = [
        "Name",
        "Cost",
        "Damage",
        "Weight",
        "Properties",
    ]

    # Parse rows
    parsed_rows: list[list[str]] = []
    for words in weapon_rows:
        parsed_row = _parse_weapon_row(words)
        if parsed_row is not None:
            parsed_rows.append(parsed_row)

    # Validate expected weapon count (SRD 5.1 has 37: 14 simple + 23 martial)
    if len(parsed_rows) != 37:
        import logging

        logging.warning(
            f"Expected 37 weapons, found {len(parsed_rows)}. " f"Extraction may be incomplete."
        )

    return {
        "headers": headers,
        "rows": parsed_rows,
    }


def parse_exchange_rates_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Standard Exchange Rates table from PDF.

    Currency conversion table showing CP/SP/EP/GP/PP equivalencies.

    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers containing the table (usually [62])

    Returns:
        Dict with structured exchange rates table data
    """
    # Extract all rows using coordinate analysis
    all_rows = _extract_rows_by_coordinate(pdf_path, pages)

    # Filter for currency rows (contain currency abbreviations in parentheses)
    currency_markers = ["(cp)", "(sp)", "(ep)", "(gp)", "(pp)"]
    exchange_rows = [
        row
        for row in all_rows
        if any(marker in row for marker in currency_markers) and len(row) == 7
    ]

    # Define headers
    headers = [
        "Coin",
        "CP",
        "SP",
        "EP",
        "GP",
        "PP",
    ]

    # Clean up rows: combine first two columns (e.g., "Copper (cp)" -> "Copper (cp)")
    cleaned_rows = []
    for row in exchange_rows:
        # Row format: ['Copper', '(cp)', '1', '1/10', '1/50', '1/100', '1/1,000']
        coin_name = f"{row[0]} {row[1]}"
        cleaned_row = [coin_name] + row[2:]
        cleaned_rows.append(cleaned_row)

    # Validate expected count (5 currencies: cp, sp, ep, gp, pp)
    if len(cleaned_rows) != 5:
        import logging

        logging.warning(
            f"Expected 5 currency types, found {len(cleaned_rows)}. "
            f"Extraction may be incomplete."
        )

    return {
        "headers": headers,
        "rows": cleaned_rows,
    }


def _parse_weapon_row(words: list[str]) -> list[str] | None:
    """Parse weapon row words into structured columns."""
    try:
        # Find cost unit (gp, sp, or cp)
        cost_unit = None
        cost_idx = -1
        for unit in ["gp", "sp", "cp"]:
            if unit in words:
                cost_unit = unit
                cost_idx = words.index(unit)
                break

        if cost_unit is None:
            return None

        # Name: everything before cost number
        name_parts = words[: cost_idx - 1]
        name = " ".join(name_parts)

        # Cost: number + unit
        cost = f"{words[cost_idx - 1]} {cost_unit}"

        # Damage: after cost, before weight
        # Damage is usually 2 words (e.g., "1d6 piercing", "1 piercing", or "—")
        damage_start = cost_idx + 1
        damage_words = []

        for i in range(damage_start, min(damage_start + 4, len(words))):
            part = words[i]
            # Collect damage parts (dice, numbers, damage types)
            if (
                part in ["bludgeoning", "piercing", "slashing"]
                or "d" in part
                or part == "—"
                or part.isdigit()
            ):
                damage_words.append(part)
                # Single "—" is complete damage (no dice, like Net)
                if part == "—":
                    break
                # After damage type, we're done (e.g., "1d6 piercing" or "1 piercing")
                if part in ["bludgeoning", "piercing", "slashing"]:
                    break
            # Stop at weight indicator
            elif part == "lb.":
                break

        damage = " ".join(damage_words) if damage_words else "—"
        damage_end_idx = damage_start + len(damage_words)

        # Weight: right after damage
        # Could be "X lb." or just "—"
        weight_idx = -1
        weight = "—"

        if damage_end_idx < len(words):
            # Check if next word is a number (weight value)
            next_word = words[damage_end_idx]
            if damage_end_idx + 1 < len(words) and words[damage_end_idx + 1] == "lb.":
                # Pattern: "X lb."
                weight = f"{next_word} lb."
                weight_idx = damage_end_idx + 1
            elif next_word == "—":
                # Pattern: just "—"
                weight = "—"
                weight_idx = damage_end_idx
            elif "lb." in words[damage_end_idx:]:
                # Search for lb. after damage
                for i in range(damage_end_idx, len(words)):
                    if words[i] == "lb.":
                        weight = f"{words[i-1]} lb."
                        weight_idx = i
                        break

        # Weight: find it properly
        if weight_idx > 0:
            # Properties: everything after weight
            if weight_idx + 1 < len(words):
                properties_parts = words[weight_idx + 1 :]
                # Remove leading "—" if present (from Sling)
                if properties_parts and properties_parts[0] == "—":
                    properties_parts = properties_parts[1:]
                properties = " ".join(properties_parts) if properties_parts else "—"
            else:
                properties = "—"
        else:
            # No explicit weight, properties after damage
            prop_start = damage_start + len(damage_words)
            properties_parts = words[prop_start:]
            properties = " ".join(properties_parts) if properties_parts else "—"

        return [name, cost, damage, weight, properties]

    except (ValueError, IndexError):
        return None
