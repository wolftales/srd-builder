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


def parse_donning_doffing_armor_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Donning and Doffing Armor table from PDF.

    Time requirements for putting on and taking off armor.

    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers containing the table (usually [64])

    Returns:
        Dict with structured donning/doffing armor table data
    """
    # Extract all rows using coordinate analysis
    all_rows = _extract_rows_by_coordinate(pdf_path, pages)

    # Filter for armor time rows
    # Pattern: armor type + two time values (with "minute" or "action")
    time_keywords = ["minute", "minutes", "action"]
    armor_types = ["Light", "Medium", "Heavy", "Shield"]

    armor_rows = [
        row
        for row in all_rows
        if any(armor_type in row for armor_type in armor_types)
        and any(keyword in row for keyword in time_keywords)
        and 5 <= len(row) <= 8
    ]

    # Define headers
    headers = [
        "Category",
        "Don",
        "Doff",
    ]

    # Parse rows
    parsed_rows: list[list[str]] = []
    for words in armor_rows:
        # Pattern: ["Light", "Armor", "1", "minute", "1", "minute"]
        # or: ["Shield", "1", "action", "1", "action"]
        if len(words) >= 5:
            # Category is first word (or first two words if "Armor" follows)
            if "Armor" in words and words.index("Armor") == 1:
                category = f"{words[0]} {words[1]}"
                time_start = 2
            else:
                category = words[0]
                time_start = 1

            # Extract don time (first time value)
            don_value = words[time_start]
            don_unit = words[time_start + 1]
            don = f"{don_value} {don_unit}"

            # Extract doff time (second time value)
            doff_value = words[time_start + 2]
            doff_unit = words[time_start + 3]
            doff = f"{doff_value} {doff_unit}"

            parsed_rows.append([category, don, doff])

    # Validate expected count (4 entries: Light, Medium, Heavy, Shield)
    if len(parsed_rows) != 4:
        import logging

        logging.warning(
            f"Expected 4 armor categories, found {len(parsed_rows)}. "
            f"Extraction may be incomplete."
        )

    return {
        "headers": headers,
        "rows": parsed_rows,
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


def parse_adventure_gear_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Adventure Gear table from PDF.

    This table has a two-column alphabetically-sorted layout.
    Left column: A-G items, Right column: H-W items
    Categories (Ammunition, Arcane focus, etc.) appear as headers without prices,
    followed by indented items with prices.
    Each item has: Name | Cost (amount + currency) | Weight

    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers to extract from

    Returns:
        Dictionary with headers and rows list
    """
    import pymupdf

    doc = pymupdf.open(pdf_path)

    # Column split threshold (X coordinate)
    column_split = 300

    # Collect rows for each column separately to preserve alphabetical order
    left_items = []
    right_items = []

    for page_num in pages:
        page = doc[page_num - 1]
        words = page.get_text("words")

        # Group by Y coordinate
        rows_dict = defaultdict(list)
        for word in words:
            x0, y0, x1, y1, text, *_ = word
            y_key = round(y0 / Y_GROUPING_TOLERANCE) * Y_GROUPING_TOLERANCE
            rows_dict[y_key].append((x0, text))

        # Process each row in order (top to bottom)
        for y_pos in sorted(rows_dict.keys()):
            row_words = sorted(rows_dict[y_pos], key=lambda w: w[0])

            # Split into left and right columns
            left_col = [text for x, text in row_words if x < column_split]
            right_col = [text for x, text in row_words if x >= column_split]

            # Process left column
            if left_col:
                # Get X position of first word to check indentation
                first_x = [x for x, text in row_words if x < column_split][0]
                is_indented = first_x > 60  # Indented items start at X ≈ 66.6

                has_price = any(coin in left_col for coin in ["gp", "sp", "cp"])

                if has_price:
                    item = _parse_gear_item(left_col)
                    if item:
                        # Mark indented items with special flag (temporary)
                        if is_indented:
                            item.append("__INDENTED__")
                        left_items.append(item)
                elif not is_indented:
                    # Category header (flush left, no price)
                    category_text = " ".join(left_col)
                    # Skip headers, page numbers, system text
                    if category_text not in [
                        "Item Cost Weight",
                        "",
                    ] and not category_text.startswith("System"):
                        # Check if it's a known category
                        if any(
                            cat in category_text for cat in ["Ammunition", "focus", "Holy symbol"]
                        ):
                            # Add category as a row with no cost/weight
                            left_items.append([category_text, "—", "—"])

            # Process right column
            if right_col:
                has_price = any(coin in right_col for coin in ["gp", "sp", "cp"])
                if has_price:
                    item = _parse_gear_item(right_col)
                    if item:
                        right_items.append(item)

    doc.close()

    # Combine: left column first (A-G), then right column (H-W)
    all_items = left_items + right_items

    # Remove duplicates while preserving order
    seen = set()
    unique_items = []
    for item in all_items:
        item_key = item[0].lower()
        if item_key not in seen:
            seen.add(item_key)
            unique_items.append(item)

    # Build category metadata for easy parsing
    # Category items are indented (marked with __INDENTED__ flag)
    # Non-indented items with prices end the current category
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None
    final_items: list[list[str]] = []

    for i, item in enumerate(unique_items):
        is_category_header = item[1] == "—" and item[2] == "—"
        is_indented = len(item) > 3 and item[3] == "__INDENTED__"

        # Remove indentation marker and save clean item
        clean_item = item[:3] if len(item) > 3 else item
        final_items.append(clean_item)

        if is_category_header:
            # Start new category
            current_category = clean_item[0]
            categories[current_category] = {"row_index": i, "items": []}
        elif current_category and is_indented:
            # Indented item belongs to current category
            categories[current_category]["items"].append({"name": clean_item[0], "row_index": i})
        elif current_category and not is_category_header:
            # Non-indented item with price ends the category
            current_category = None

    # Validation
    if len(final_items) < 50:
        print(f"Warning: Expected ~50+ adventure gear items, found {len(final_items)}")

    headers = ["Item", "Cost", "Weight"]
    return {"headers": headers, "rows": final_items, "categories": categories}


def _parse_gear_item(words: list[str]) -> list[str] | None:
    """Parse a single gear item from word list.

    Pattern: Name parts... | Cost_amount | Currency | Weight parts...

    Args:
        words: List of words for this item

    Returns:
        [name, cost, weight] or None if invalid
    """
    # Find currency position
    cost_idx = -1
    for i, word in enumerate(words):
        if word in ["gp", "sp", "cp"]:
            cost_idx = i
            break

    if cost_idx < 2:  # Need at least: name + amount + currency
        return None

    # Skip header rows
    if "Item" in words or "Cost" in words or "System" in words or "Document" in words:
        return None

    currency = words[cost_idx]
    cost_amount = words[cost_idx - 1]

    # Item name: everything before cost amount
    name_parts = words[: cost_idx - 1]
    name = " ".join(name_parts)

    # Cost string
    cost = f"{cost_amount} {currency}"

    # Weight: everything after currency
    weight_parts = words[cost_idx + 1 :]
    weight = " ".join(weight_parts) if weight_parts else "—"

    return [name, cost, weight]


def parse_container_capacity_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Container Capacity table from PDF.

    Two-column table split across pages:
    - Page 69 right column: First 6 containers
    - Page 70 left column: Last 7 containers

    Headers: Container | Capacity
    """
    import fitz

    doc = fitz.open(pdf_path)
    headers = ["Container", "Capacity"]
    items: list[list[str]] = []

    # Page 69 - Right column (X > 300)
    page69 = doc[pages[0] - 1]
    words69 = page69.get_text("words")

    rows_p69: dict[float, list[tuple[float, str]]] = {}
    y_grouping_tolerance = 2

    for word in words69:
        x0, y0, x1, y1, text, *_ = word
        if x0 > 300 and 615 < y0 < 750:  # Right column, container section
            y_key = round(y0 / y_grouping_tolerance) * y_grouping_tolerance
            if y_key not in rows_p69:
                rows_p69[y_key] = []
            rows_p69[y_key].append((x0, text))

    for y_pos in sorted(rows_p69.keys()):
        row_words = sorted(rows_p69[y_pos], key=lambda w: w[0])
        row_text = " ".join([text for x, text in row_words])

        # Skip header and footer
        if "Container" in row_text or "System" in row_text:
            continue

        # Parse: Container name | Capacity description
        # Container name ends before first digit or measurement unit
        words = [text for x, text in row_words]

        # Find split point: first word that's a digit or starts with digit
        split_idx = None
        for i, word in enumerate(words):
            if word[0].isdigit() or word in ["1½", "1/2", "1/5"]:
                split_idx = i
                break

        if split_idx:
            container_name = " ".join(words[:split_idx])
            capacity = " ".join(words[split_idx:])
            items.append([container_name, capacity])

    # Page 70 - Left column (X < 300)
    page70 = doc[pages[1] - 1]
    words70 = page70.get_text("words")

    rows_p70: dict[float, list[tuple[float, str]]] = {}
    for word in words70:
        x0, y0, x1, y1, text, *_ = word
        if x0 < 300 and 70 < y0 < 150:  # Left column, before footnote
            y_key = round(y0 / y_grouping_tolerance) * y_grouping_tolerance
            if y_key not in rows_p70:
                rows_p70[y_key] = []
            rows_p70[y_key].append((x0, text))

    for y_pos in sorted(rows_p70.keys()):
        row_words = sorted(rows_p70[y_pos], key=lambda w: w[0])
        row_text = " ".join([text for x, text in row_words])

        # Stop at footnote
        if "*" in row_text or "You can" in row_text:
            break

        words = [text for x, text in row_words]

        # Find split point
        split_idx = None
        for i, word in enumerate(words):
            if word[0].isdigit() or word in ["1½", "1/2", "1/5"]:
                split_idx = i
                break

        if split_idx:
            container_name = " ".join(words[:split_idx])
            capacity = " ".join(words[split_idx:])
            items.append([container_name, capacity])

    doc.close()

    if len(items) != 13:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 13 container capacity entries, found {len(items)}")

    return {"headers": headers, "rows": items}
