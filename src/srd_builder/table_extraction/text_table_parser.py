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
            f"Expected 13 armor items, found {len(parsed_rows)}. Extraction may be incomplete."
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
            f"Expected 37 weapons, found {len(parsed_rows)}. Extraction may be incomplete."
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
            f"Expected 5 currency types, found {len(cleaned_rows)}. Extraction may be incomplete."
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
            f"Expected 4 armor categories, found {len(parsed_rows)}. Extraction may be incomplete."
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
                        weight = f"{words[i - 1]} lb."
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


def parse_tools_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Tools table from PDF.

    Single-column table on page 70 right side.
    Contains 35 items with 3 category headers:
    - Artisan's tools (17 items)
    - Gaming set (2 items)
    - Musical instrument (8 items)

    Headers: Item | Cost | Weight
    """
    import fitz

    doc = fitz.open(pdf_path)
    headers = ["Item", "Cost", "Weight"]
    items: list[list[str]] = []

    page = doc[pages[0] - 1]
    words = page.get_text("words")

    rows: dict[float, list[tuple[float, str]]] = {}
    y_grouping_tolerance = 2

    for word in words:
        x0, y0, x1, y1, text, *_ = word
        if x0 > 300 and 140 < y0 < 565:  # Right column, Tools section
            y_key = round(y0 / y_grouping_tolerance) * y_grouping_tolerance
            if y_key not in rows:
                rows[y_key] = []
            rows[y_key].append((x0, text))

    # Track categories
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None

    for y_pos in sorted(rows.keys()):
        row_words = sorted(rows[y_pos], key=lambda w: w[0])
        row_text = " ".join([text for x, text in row_words])

        # Skip main header
        if row_text in ["Item Cost Weight", "Tools"]:
            continue

        # Check if this is a category header (no price/weight)
        has_currency = any(curr in row_text for curr in ["gp", "sp", "cp"])
        has_dash = "—" in row_text

        if not has_currency and not has_dash:
            # Category header
            current_category = row_text
            categories[current_category] = {"row_index": len(items), "items": []}
            items.append([row_text, "—", "—"])
        else:
            # Regular item - parse into [Item, Cost, Weight]
            words_list = [text for x, text in row_words]

            # Find currency position
            currency_idx = None
            for i, word in enumerate(words_list):
                if word in ["gp", "sp", "cp"]:
                    currency_idx = i
                    break

            if currency_idx:
                # Item name: everything before cost amount
                name_parts = words_list[: currency_idx - 1]
                item_name = " ".join(name_parts)

                # Cost: amount + currency
                cost_amount = words_list[currency_idx - 1]
                currency = words_list[currency_idx]
                cost = f"{cost_amount} {currency}"

                # Weight: everything after currency
                weight_parts = words_list[currency_idx + 1 :]
                weight = " ".join(weight_parts) if weight_parts else "—"

                items.append([item_name, cost, weight])

                # Track category membership
                if current_category:
                    categories[current_category]["items"].append(
                        {"name": item_name, "row_index": len(items) - 1}
                    )

    doc.close()

    if len(items) != 38:  # 35 items + 3 category headers
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 38 total entries (35 items + 3 categories), found {len(items)}")

    return {"headers": headers, "rows": items, "categories": categories}


def parse_mounts_and_other_animals_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Mounts and Other Animals table from PDF.

    Split across pages:
    - Page 71 right column: First 3 animals (Camel, Donkey, Elephant)
    - Page 72 left column: Last 5 animals (Horses, Mastiff, Pony, Warhorse)

    Headers: Item | Cost | Speed | Carrying Capacity
    """
    import fitz

    doc = fitz.open(pdf_path)
    headers = ["Item", "Cost", "Speed", "Carrying Capacity"]
    items: list[list[str]] = []

    # Page 71 - Right column
    page71 = doc[pages[0] - 1]
    words71 = page71.get_text("words")

    rows_p71: dict[float, list[tuple[float, str]]] = {}
    y_grouping_tolerance = 2

    for word in words71:
        x0, y0, x1, y1, text, *_ = word
        if x0 > 300 and 655 < y0 < 750:  # Right column, mounts section
            y_key = round(y0 / y_grouping_tolerance) * y_grouping_tolerance
            if y_key not in rows_p71:
                rows_p71[y_key] = []
            rows_p71[y_key].append((x0, text))

    for y_pos in sorted(rows_p71.keys()):
        row_words = sorted(rows_p71[y_pos], key=lambda w: w[0])
        row_text = " ".join([text for x, text in row_words])

        # Skip header and footer
        if "Item Cost Speed" in row_text or "System" in row_text or "Carrying" in row_text:
            continue

        # Parse: Item | Cost | Speed | Capacity
        words_list = [text for x, text in row_words]

        # Find "gp" for cost
        gp_idx = None
        for i, word in enumerate(words_list):
            if word == "gp":
                gp_idx = i
                break

        if gp_idx:
            # Item name: everything before cost amount
            name_parts = words_list[: gp_idx - 1]
            item_name = " ".join(name_parts)

            # Cost
            cost = f"{words_list[gp_idx - 1]} gp"

            # Speed: next value after gp (e.g., "50")
            speed_val = words_list[gp_idx + 1]
            speed_unit = words_list[gp_idx + 2] if gp_idx + 2 < len(words_list) else "ft."
            speed = f"{speed_val} {speed_unit}"

            # Capacity: remaining text
            capacity_parts = words_list[gp_idx + 3 :]
            capacity = " ".join(capacity_parts)

            items.append([item_name, cost, speed, capacity])

    # Page 72 - Left column
    page72 = doc[pages[1] - 1]
    words72 = page72.get_text("words")

    rows_p72: dict[float, list[tuple[float, str]]] = {}
    for word in words72:
        x0, y0, x1, y1, text, *_ = word
        if x0 < 300 and 70 < y0 < 120:  # Left column top, before Tack table
            y_key = round(y0 / y_grouping_tolerance) * y_grouping_tolerance
            if y_key not in rows_p72:
                rows_p72[y_key] = []
            rows_p72[y_key].append((x0, text))

    for y_pos in sorted(rows_p72.keys()):
        row_words = sorted(rows_p72[y_pos], key=lambda w: w[0])
        row_text = " ".join([text for x, text in row_words])

        # Stop at next table header
        if "Tack" in row_text:
            break

        words_list = [text for x, text in row_words]

        # Find "gp"
        gp_idx = None
        for i, word in enumerate(words_list):
            if word == "gp":
                gp_idx = i
                break

        if gp_idx:
            name_parts = words_list[: gp_idx - 1]
            item_name = " ".join(name_parts)
            cost = f"{words_list[gp_idx - 1]} gp"
            speed_val = words_list[gp_idx + 1]
            speed_unit = words_list[gp_idx + 2] if gp_idx + 2 < len(words_list) else "ft."
            speed = f"{speed_val} {speed_unit}"
            capacity_parts = words_list[gp_idx + 3 :]
            capacity = " ".join(capacity_parts)

            items.append([item_name, cost, speed, capacity])

    doc.close()

    if len(items) != 8:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 8 mounts/animals, found {len(items)}")

    return {"headers": headers, "rows": items}


def parse_tack_harness_vehicles_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Tack, Harness, and Drawn Vehicles table from PDF.

    Single column on page 72 left, Y-range 144-328.
    Contains ~17 items including Saddle subcategories.

    Headers: Item | Cost | Weight
    """
    import fitz

    doc = fitz.open(pdf_path)
    headers = ["Item", "Cost", "Weight"]
    items: list[list[str]] = []

    page = doc[pages[0] - 1]
    words = page.get_text("words")

    rows: dict[float, list[tuple[float, str]]] = {}
    y_grouping_tolerance = 2

    for word in words:
        x0, y0, x1, y1, text, *_ = word
        if x0 < 300 and 162 < y0 < 330:  # Left column, skip table header at ~144
            y_key = round(y0 / y_grouping_tolerance) * y_grouping_tolerance
            if y_key not in rows:
                rows[y_key] = []
            rows[y_key].append((x0, text))

    saddle_types_remaining = 0  # Track saddle type subcategories

    for y_pos in sorted(rows.keys()):
        row_words = sorted(rows[y_pos], key=lambda w: w[0])
        row_text = " ".join([text for x, text in row_words])

        # Skip headers and next table
        if "Item Cost Weight" in row_text or "Waterborne" in row_text:
            continue

        words_list = [text for x, text in row_words]

        # Find currency (gp, sp, cp) or special markers (×4, ×2)
        currency_idx = None
        for i, word in enumerate(words_list):
            if word in ["gp", "sp", "cp", "×2", "×4"]:
                currency_idx = i
                break

        if currency_idx:
            # Item name: everything before cost/marker
            name_parts = (
                words_list[: currency_idx - 1]
                if words_list[currency_idx] in ["gp", "sp", "cp"]
                else words_list[:currency_idx]
            )
            item_name = " ".join(name_parts)

            # Check if this is "Feed" - next 4 items are saddle types
            if "Feed" in item_name:
                saddle_types_remaining = 4
            # Check if this is a saddle type (indented subcategory)
            elif saddle_types_remaining > 0 and item_name in [
                "Exotic",
                "Military",
                "Pack",
                "Riding",
            ]:
                item_name = f"Saddle, {item_name.lower()}"
                saddle_types_remaining -= 1

            # Cost: amount + currency OR special marker (×4, ×2)
            if words_list[currency_idx] in ["×2", "×4"]:
                cost = words_list[currency_idx]
                # Weight follows cost
                weight_parts = words_list[currency_idx + 1 :]
                weight = " ".join(weight_parts) if weight_parts else "—"
            else:
                cost = f"{words_list[currency_idx - 1]} {words_list[currency_idx]}"
                # Weight: after currency
                weight_parts = words_list[currency_idx + 1 :]
                weight = " ".join(weight_parts) if weight_parts else "—"

            items.append([item_name, cost, weight])

    doc.close()

    if len(items) < 15 or len(items) > 20:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected ~17 tack/vehicle items, found {len(items)}")

    return {"headers": headers, "rows": items}


def parse_waterborne_vehicles_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Waterborne Vehicles table from PDF.

    Single column on page 72 left, Y-range 358-442.
    Contains 6 vehicles.

    Headers: Item | Cost | Speed
    """
    from .text_parser_utils import extract_region_rows, rows_to_sorted_text, should_skip_header

    headers = ["Item", "Cost", "Speed"]
    items: list[list[str]] = []

    rows = extract_region_rows(pdf_path, pages[0], x_max=300, y_min=376, y_max=445)

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip headers
        if should_skip_header(row_text, ["Item Cost Speed"]):
            continue

        # Find "gp" for cost
        gp_idx = None
        for i, word in enumerate(words_list):
            if word == "gp":
                gp_idx = i
                break

        if gp_idx:
            # Item name: everything before cost amount
            name_parts = words_list[: gp_idx - 1]
            item_name = " ".join(name_parts)

            # Cost
            cost = f"{words_list[gp_idx - 1]} gp"

            # Speed: after gp (value + unit)
            speed_parts = words_list[gp_idx + 1 :]
            speed = " ".join(speed_parts)

            items.append([item_name, cost, speed])

    if len(items) != 6:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 6 waterborne vehicles, found {len(items)}")

    return {"headers": headers, "rows": items}


def parse_trade_goods_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Trade Goods table from PDF.

    Single column on page 72 right, Y-range 72-232.
    Contains 13 goods.

    Headers: Cost | Goods
    Format: "1 cp | 1 lb. of wheat"
    """
    from .text_parser_utils import (
        extract_region_rows,
        find_currency_index,
        rows_to_sorted_text,
        should_skip_header,
    )

    headers = ["Cost", "Goods"]
    items: list[list[str]] = []

    # Extract rows from page 72 right column
    rows = extract_region_rows(pdf_path, pages[0], x_min=300, y_min=90, y_max=235)

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip header
        if should_skip_header(row_text, ["Cost Goods"]):
            continue

        # Find currency (cp, sp, gp) - cost comes first
        currency_idx = find_currency_index(words_list)

        if currency_idx:
            # Cost: amount + currency
            cost = f"{words_list[currency_idx - 1]} {words_list[currency_idx]}"

            # Goods: everything after currency
            goods_parts = words_list[currency_idx + 1 :]
            goods = " ".join(goods_parts)

            items.append([cost, goods])

    if len(items) != 13:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 13 trade goods, found {len(items)}")

    return {"headers": headers, "rows": items}


def parse_lifestyle_expenses_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Lifestyle Expenses table from PDF.

    Spans pages 72 (bottom right) to 73 (top left).
    Contains lifestyle categories with costs.

    Headers: Lifestyle | Price/Day
    """
    from .text_parser_utils import (
        extract_multipage_rows,
        find_currency_index,
        rows_to_sorted_text,
        should_skip_header,
    )

    headers = ["Lifestyle", "Price/Day"]
    items: list[list[str]] = []

    # Extract from page 72 bottom right + page 73 top left
    rows = extract_multipage_rows(
        pdf_path,
        [
            {"page": pages[0], "x_min": 300, "y_min": 260, "y_max": 750},
            {"page": pages[1], "x_max": 300, "y_min": 70, "y_max": 200},
        ],
    )

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip headers and stop at prose
        if should_skip_header(row_text, ["Lifestyle Expenses", "Lifestyle Price"]):
            continue
        if "Food" in row_text or "particular" in row_text:
            break

        currency_idx = find_currency_index(words_list)

        if currency_idx:
            # Lifestyle name: everything before cost
            name_parts = words_list[: currency_idx - 1]
            lifestyle = " ".join(name_parts)

            # Price: amount + currency
            price = f"{words_list[currency_idx - 1]} {words_list[currency_idx]}"

            items.append([lifestyle, price])

    if len(items) < 4 or len(items) > 8:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected ~5 lifestyle categories, found {len(items)}")

    return {"headers": headers, "rows": items}


def parse_food_drink_lodging_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Food, Drink, and Lodging table from PDF.

    Spans pages 73 (bottom right) to 74 (top left).
    Contains food/drink/lodging items with costs.

    Categories:
    - Inn stay per day: Squalid, Poor, Modest, Comfortable, Wealthy, Aristocratic
    - Meals per day: Squalid, Poor, Modest, Comfortable, Wealthy, Aristocratic
    - Ale: Gallon, Mug

    Headers: Item | Cost
    """
    from .text_parser_utils import (
        extract_multipage_rows,
        find_currency_index,
        rows_to_sorted_text,
        should_skip_header,
    )

    headers = ["Item", "Cost"]
    items: list[list[str]] = []

    # Extract from page 73 bottom right + page 74 top left
    rows = extract_multipage_rows(
        pdf_path,
        [
            {"page": pages[0], "x_min": 300, "y_min": 650, "y_max": 750},
            {"page": pages[1], "x_max": 300, "y_min": 70, "y_max": 250},
        ],
    )

    # Track category metadata
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip headers and stop at next table
        if should_skip_header(row_text, ["Food, Drink", "Item Cost"]):
            continue
        if "Services" in row_text:
            break

        currency_idx = find_currency_index(words_list)

        if currency_idx:
            # Item name: everything before cost
            name_parts = words_list[: currency_idx - 1]
            item_name = " ".join(name_parts)

            # Cost: amount + currency
            cost = f"{words_list[currency_idx - 1]} {words_list[currency_idx]}"

            current_row = len(items)

            # Detect categories based on item name patterns
            lifestyle_levels = {
                "Squalid",
                "Poor",
                "Modest",
                "Comfortable",
                "Wealthy",
                "Aristocratic",
            }

            if item_name in lifestyle_levels:
                # Rows 3-8: Inn stay per day (first set of lifestyle levels)
                # Rows 9-14: Meals per day (second set of lifestyle levels)
                if current_row == 3 or (
                    current_category == "Inn stay per day" and current_row == 9
                ):
                    if current_row == 3:
                        current_category = "Inn stay per day"
                    else:
                        current_category = "Meals per day"
                    categories[current_category] = {"row_index": current_row, "items": []}

                if current_category:
                    categories[current_category]["items"].append(
                        {"name": item_name, "row_index": current_row}
                    )
            elif item_name in {"Gallon", "Mug"}:
                # Ale category
                if current_category != "Ale":
                    current_category = "Ale"
                    categories[current_category] = {"row_index": current_row, "items": []}
                categories[current_category]["items"].append(
                    {"name": item_name, "row_index": current_row}
                )
            else:
                # Standalone item, exit category
                current_category = None

            items.append([item_name, cost])

    if len(items) < 8 or len(items) > 20:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected ~17 food/drink/lodging items, found {len(items)}")

    return {"headers": headers, "rows": items, "categories": categories}


def parse_services_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Services table from PDF.

    Single column on page 74 top right.
    Contains service items with costs.

    Categories:
    - Coach cab: Between towns, Within a city
    - Hireling: Skilled, Untrained

    Headers: Service | Cost
    """
    from .text_parser_utils import (
        extract_region_rows,
        find_currency_index,
        rows_to_sorted_text,
        should_skip_header,
    )

    headers = ["Service", "Cost"]
    items: list[list[str]] = []

    # Track category metadata
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None

    rows = extract_region_rows(pdf_path, pages[0], x_min=300, y_min=70, y_max=350)

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip headers
        if should_skip_header(row_text, ["Services", "Service Cost", "Service Pay"]):
            continue

        currency_idx = find_currency_index(words_list)

        if currency_idx:
            # Service name: everything before cost
            name_parts = words_list[: currency_idx - 1]
            service_name = " ".join(name_parts)

            # Cost: amount + currency (may include "per" qualifier)
            cost_parts = words_list[currency_idx - 1 :]
            cost = " ".join(cost_parts)

            current_row = len(items)

            # Detect categories based on service name patterns
            if service_name in {"Between towns", "Within a city"}:
                if current_category != "Coach cab":
                    current_category = "Coach cab"
                    categories[current_category] = {"row_index": current_row, "items": []}
                categories[current_category]["items"].append(
                    {"name": service_name, "row_index": current_row}
                )
            elif service_name in {"Skilled", "Untrained"}:
                if current_category != "Hireling":
                    current_category = "Hireling"
                    categories[current_category] = {"row_index": current_row, "items": []}
                categories[current_category]["items"].append(
                    {"name": service_name, "row_index": current_row}
                )
            else:
                # Standalone service, exit category
                current_category = None

            items.append([service_name, cost])

    if len(items) < 6 or len(items) > 12:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected ~8 services, found {len(items)}")

    return {"headers": headers, "rows": items, "categories": categories}
