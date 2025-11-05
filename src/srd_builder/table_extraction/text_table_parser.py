"""Text-based table parser for SRD 5.1.

Extracts tables from PDF text by analyzing word positions and grouping into rows/columns.
Used for tables that lack grid borders and aren't detected by PyMuPDF's table detection.
"""

from typing import Any

# Coordinate grouping tolerance (pixels)
# Words within this Y-distance are considered on the same horizontal line
Y_GROUPING_TOLERANCE = 2


def parse_armor_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse armor table from PDF.

    Armor rows contain 'gp' (cost) and have 8-15 words.

    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers containing armor table

    Returns:
        Dict with structured armor table data including headers and parsed rows
    """
    from .text_parser_utils import extract_multipage_rows, rows_to_sorted_text

    # Extract rows from pages 63-64 (armor table spans bottom of p63 and top of p64)
    rows = extract_multipage_rows(
        pdf_path,
        [
            {"page": pages[0], "y_min": 680, "y_max": 750},  # Bottom of page 63 (Padded at Y=689)
            {"page": pages[1], "y_min": 70, "y_max": 430},  # Top of page 64 (armor rows Y=72-420)
        ],
    )

    headers = [
        "Armor",
        "Cost",
        "Armor Class (AC)",
        "Strength",
        "Stealth",
        "Weight",
    ]

    parsed_rows: list[list[str]] = []

    for _y_pos, words in rows_to_sorted_text(rows):
        # Filter for armor rows (have 'gp' cost marker and reasonable word count)
        if "gp" not in words or not (8 <= len(words) <= 15):
            continue

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
    from .text_parser_utils import extract_multipage_rows, rows_to_sorted_text

    # Extract rows from pages 65-66 with proper Y-coordinate ranges
    rows = extract_multipage_rows(
        pdf_path,
        [
            {"page": pages[0], "y_min": 675, "y_max": 750},
            {"page": pages[1], "y_min": 70, "y_max": 510},
        ],
    )

    headers = [
        "Name",
        "Cost",
        "Damage",
        "Weight",
        "Properties",
    ]

    parsed_rows: list[list[str]] = []

    for _y_pos, words in rows_to_sorted_text(rows):
        # Filter for weapon rows (have cost AND damage indicators)
        has_cost = any(x in words for x in ["gp", "sp", "cp"])
        has_damage = any("d" in x or x in ["bludgeoning", "piercing", "slashing"] for x in words)
        if not (has_cost and (has_damage or "—" in words)):
            continue

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
    5x6 grid on page 62.

    Headers: Coin | CP | SP | EP | GP | PP
    """
    from .text_parser_utils import extract_region_rows, rows_to_sorted_text

    headers = ["Coin", "CP", "SP", "EP", "GP", "PP"]
    items: list[list[str]] = []

    rows = extract_region_rows(pdf_path, pages[0], y_min=530, y_max=590)

    currency_markers = ["(cp)", "(sp)", "(ep)", "(gp)", "(pp)"]

    for _y_pos, words_list in rows_to_sorted_text(rows):
        # Currency rows have 7 words: ['Copper', '(cp)', '1', '1/10', '1/50', '1/100', '1/1,000']
        if len(words_list) == 7 and any(marker in words_list for marker in currency_markers):
            coin_name = f"{words_list[0]} {words_list[1]}"
            row = [coin_name] + words_list[2:]
            items.append(row)

    if len(items) != 5:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 5 currency types, found {len(items)}")

    return {"headers": headers, "rows": items}


def parse_donning_doffing_armor_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Donning and Doffing Armor table from PDF.

    Time requirements for putting on and taking off armor.
    4 rows on page 64: Light Armor, Medium Armor, Heavy Armor, Shield.

    Headers: Category | Don | Doff
    """
    from .text_parser_utils import extract_region_rows, rows_to_sorted_text

    headers = ["Category", "Don", "Doff"]
    items: list[list[str]] = []

    rows = extract_region_rows(pdf_path, pages[0], y_min=100, y_max=600)

    time_keywords = ["minute", "minutes", "action"]
    armor_types = ["Light", "Medium", "Heavy", "Shield"]

    for _y_pos, words_list in rows_to_sorted_text(rows):
        # Filter: must contain armor type and time keywords
        if not any(armor_type in words_list for armor_type in armor_types):
            continue
        if not any(keyword in words_list for keyword in time_keywords):
            continue
        if len(words_list) < 5 or len(words_list) > 8:
            continue

        # Pattern: ["Light", "Armor", "1", "minute", "1", "minute"]
        # or: ["Shield", "1", "action", "1", "action"]
        if "Armor" in words_list and words_list.index("Armor") == 1:
            category = f"{words_list[0]} {words_list[1]}"
            time_start = 2
        else:
            category = words_list[0]
            time_start = 1

        don = f"{words_list[time_start]} {words_list[time_start + 1]}"
        doff = f"{words_list[time_start + 2]} {words_list[time_start + 3]}"

        items.append([category, don, doff])

    if len(items) != 4:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 4 armor categories, found {len(items)}")

    return {"headers": headers, "rows": items}


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

    Two-column alphabetically-sorted layout with categories.
    Left column: A-G items, Right column: H-W items
    Categories (Ammunition, Arcane focus, etc.) followed by indented items.

    Headers: Item | Cost | Weight
    """
    import fitz

    from .text_parser_utils import detect_indentation, find_currency_index, group_words_by_y

    doc = fitz.open(pdf_path)
    column_split = 300
    left_items = []
    right_items = []

    for page_num in pages:
        page = doc[page_num - 1]
        words = page.get_text("words")
        rows_dict = group_words_by_y(words)

        for y_pos in sorted(rows_dict.keys()):
            row_words = sorted(rows_dict[y_pos], key=lambda w: w[0])

            # Split into left and right columns
            left_col_words = [(x, text) for x, text in row_words if x < column_split]
            right_col_words = [(x, text) for x, text in row_words if x >= column_split]

            # Process left column
            if left_col_words:
                left_text = [text for x, text in left_col_words]
                is_indented = detect_indentation(left_col_words, 60)
                has_price = find_currency_index(left_text) is not None

                if has_price:
                    item = _parse_gear_item(left_text)
                    if item and is_indented:
                        item.append("__INDENTED__")
                    if item:
                        left_items.append(item)
                elif not is_indented:
                    category_text = " ".join(left_text)
                    if (
                        category_text not in ["Item Cost Weight", ""]
                        and not category_text.startswith("System")
                        and any(
                            cat in category_text for cat in ["Ammunition", "focus", "Holy symbol"]
                        )
                    ):
                        left_items.append([category_text, "—", "—"])

            # Process right column
            if right_col_words:
                right_text = [text for x, text in right_col_words]
                if find_currency_index(right_text) is not None:
                    item = _parse_gear_item(right_text)
                    if item:
                        right_items.append(item)

    doc.close()

    # Combine and deduplicate
    all_items = left_items + right_items
    seen = set()
    unique_items = []
    for item in all_items:
        item_key = item[0].lower()
        if item_key not in seen:
            seen.add(item_key)
            unique_items.append(item)

    # Build category metadata
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None
    final_items: list[list[str]] = []

    for i, item in enumerate(unique_items):
        is_category_header = item[1] == "—" and item[2] == "—"
        is_indented = len(item) > 3 and item[3] == "__INDENTED__"

        clean_item = item[:3] if len(item) > 3 else item
        final_items.append(clean_item)

        if is_category_header:
            current_category = clean_item[0]
            categories[current_category] = {"row_index": i, "items": []}
        elif current_category and is_indented:
            categories[current_category]["items"].append({"name": clean_item[0], "row_index": i})
        elif current_category and not is_category_header:
            current_category = None

    if len(final_items) < 50:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected ~50+ adventure gear items, found {len(final_items)}")

    return {"headers": ["Item", "Cost", "Weight"], "rows": final_items, "categories": categories}


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
    from .text_parser_utils import (
        extract_region_rows,
        find_currency_index,
        rows_to_sorted_text,
        should_skip_header,
    )

    headers = ["Item", "Cost", "Weight"]
    items: list[list[str]] = []
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None

    rows = extract_region_rows(pdf_path, pages[0], x_min=300, y_min=140, y_max=565)

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip headers
        if should_skip_header(row_text, ["Item Cost Weight", "Tools"]):
            continue

        # Check if category header (no price/weight)
        has_currency = any(curr in words_list for curr in ["gp", "sp", "cp"])
        has_dash = "—" in words_list

        if not has_currency and not has_dash:
            # Category header
            current_category = row_text
            categories[current_category] = {"row_index": len(items), "items": []}
            items.append([row_text, "—", "—"])
        else:
            # Regular item
            currency_idx = find_currency_index(words_list)

            if currency_idx:
                item_name = " ".join(words_list[: currency_idx - 1])
                cost = f"{words_list[currency_idx - 1]} {words_list[currency_idx]}"
                weight = (
                    " ".join(words_list[currency_idx + 1 :])
                    if currency_idx + 1 < len(words_list)
                    else "—"
                )

                items.append([item_name, cost, weight])

                if current_category:
                    categories[current_category]["items"].append(
                        {"name": item_name, "row_index": len(items) - 1}
                    )

    if len(items) != 38:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 38 total entries (35 items + 3 categories), found {len(items)}")

    return {"headers": headers, "rows": items, "categories": categories}


def parse_mounts_and_other_animals_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Mounts and Other Animals table from PDF.

    Split across pages:
    - Page 71 right column: First 3 animals
    - Page 72 left column: Last 5 animals

    Headers: Item | Cost | Speed | Carrying Capacity
    """
    from .text_parser_utils import extract_multipage_rows, rows_to_sorted_text, should_skip_header

    headers = ["Item", "Cost", "Speed", "Carrying Capacity"]
    items: list[list[str]] = []

    # Extract from both pages
    rows = extract_multipage_rows(
        pdf_path,
        [
            {"page": pages[0], "x_min": 300, "y_min": 655, "y_max": 750},  # Page 71 right
            {"page": pages[1], "x_max": 300, "y_min": 70, "y_max": 120},  # Page 72 left
        ],
    )

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip headers and stop at next table
        if should_skip_header(row_text, ["Item Cost Speed", "System", "Carrying"]):
            continue
        if "Tack" in row_text:
            break

        # Find "gp" position
        gp_idx = next((i for i, word in enumerate(words_list) if word == "gp"), None)

        if gp_idx and gp_idx > 0:
            # Item name: everything before cost
            item_name = " ".join(words_list[: gp_idx - 1])

            # Cost
            cost = f"{words_list[gp_idx - 1]} gp"

            # Speed: next value after gp
            speed_val = words_list[gp_idx + 1] if gp_idx + 1 < len(words_list) else ""
            speed_unit = words_list[gp_idx + 2] if gp_idx + 2 < len(words_list) else "ft."
            speed = f"{speed_val} {speed_unit}"

            # Capacity: remaining text
            capacity = " ".join(words_list[gp_idx + 3 :])

            items.append([item_name, cost, speed, capacity])

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
    from .text_parser_utils import extract_region_rows, rows_to_sorted_text, should_skip_header

    headers = ["Item", "Cost", "Weight"]
    items: list[list[str]] = []
    saddle_types_remaining = 0

    rows = extract_region_rows(pdf_path, pages[0], x_max=300, y_min=162, y_max=330)

    for _y_pos, words_list in rows_to_sorted_text(rows):
        row_text = " ".join(words_list)

        # Skip headers and stop at next table
        if should_skip_header(row_text, ["Item Cost Weight", "Waterborne"]):
            continue

        # Find currency or special markers (×2, ×4)
        currency_idx = next(
            (i for i, word in enumerate(words_list) if word in ["gp", "sp", "cp", "×2", "×4"]), None
        )

        if currency_idx:
            # Item name
            if words_list[currency_idx] in ["gp", "sp", "cp"]:
                item_name = " ".join(words_list[: currency_idx - 1])
            else:
                item_name = " ".join(words_list[:currency_idx])

            # Saddle subcategory handling
            if "Feed" in item_name:
                saddle_types_remaining = 4
            elif saddle_types_remaining > 0 and item_name in [
                "Exotic",
                "Military",
                "Pack",
                "Riding",
            ]:
                item_name = f"Saddle, {item_name.lower()}"
                saddle_types_remaining -= 1

            # Cost
            if words_list[currency_idx] in ["×2", "×4"]:
                cost = words_list[currency_idx]
                weight = (
                    " ".join(words_list[currency_idx + 1 :])
                    if currency_idx + 1 < len(words_list)
                    else "—"
                )
            else:
                cost = f"{words_list[currency_idx - 1]} {words_list[currency_idx]}"
                weight = (
                    " ".join(words_list[currency_idx + 1 :])
                    if currency_idx + 1 < len(words_list)
                    else "—"
                )

            items.append([item_name, cost, weight])

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


def parse_ability_scores_and_modifiers_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Ability Scores and Modifiers table from PDF.

    This table is split across two columns on page 76:
    - Left column (bottom): Headers and first row (10-11, +0)
    - Right column (top): Remaining rows (12-13 through 30, +1 through +10)

    Args:
        pdf_path: Path to PDF file
        pages: List containing page number (should be [76])

    Returns:
        Dict with structured table data including headers and parsed rows
    """
    import pymupdf

    from .text_parser_utils import group_words_by_y

    doc = pymupdf.open(pdf_path)
    page = doc[pages[0] - 1]  # Convert to 0-indexed
    words = page.get_text("words")
    doc.close()

    # Split into left and right columns (X < 300 is left, >= 300 is right)
    # Left column: from headers (Y~615) down to bottom (Y~690)
    # Right column: from top (Y~70) down to end of table (Y~180)
    left_words = [w for w in words if w[0] < 300 and 615 <= w[1] <= 690]
    right_words = [w for w in words if w[0] >= 300 and 70 <= w[1] <= 180]

    # Group by Y-coordinate
    left_rows = group_words_by_y(left_words)
    right_rows = group_words_by_y(right_words)

    headers = ["Score", "Modifier"]
    parsed_rows: list[list[str]] = []

    # Process left column (scores 1-11, top to bottom)
    for _y_pos, row_words in sorted(left_rows.items()):  # Top to bottom
        # row_words is list of (x, text) tuples
        row_text = " ".join([text for x, text in sorted(row_words, key=lambda w: w[0])])

        # Skip header row
        if "Score" in row_text or "Modifier" in row_text:
            continue

        # Look for score-modifier pairs (e.g., "10–11 +0", "1 −5")
        # Note: PDF uses U+2212 (−) for negative, not hyphen-minus (-)
        words_list = row_text.split()
        if len(words_list) >= 2 and (
            words_list[1].startswith("+")
            or words_list[1].startswith("-")
            or words_list[1].startswith("−")
        ):
            score = words_list[0]
            modifier = words_list[1]
            parsed_rows.append([score, modifier])

    # Process right column (continuation, Y~72-171)
    for _y_pos, row_words in sorted(right_rows.items()):  # Top to bottom
        # row_words is list of (x, text) tuples
        row_text = " ".join([text for x, text in sorted(row_words, key=lambda w: w[0])])

        # Look for score-modifier pairs
        words_list = row_text.split()
        if len(words_list) >= 2 and (
            words_list[1].startswith("+")
            or words_list[1].startswith("-")
            or words_list[1].startswith("−")
        ):
            score = words_list[0]
            modifier = words_list[1]
            parsed_rows.append([score, modifier])

    if len(parsed_rows) < 15 or len(parsed_rows) > 17:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 16 ability score rows, found {len(parsed_rows)}")

    return {"headers": headers, "rows": parsed_rows}


def parse_experience_by_cr_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    """Parse Experience Points by Challenge Rating table from PDF.

    This table is on page 258 in a two side-by-side format within the left column:
    - Left sub-table (X<130): CR 0-13 with XP values
    - Right sub-table (130<X<250): CR 14-30 with XP values
    - Both in Y range 445-665

    Args:
        pdf_path: Path to PDF file
        pages: List containing page number (should be [258])

    Returns:
        Dict with structured table data including headers and parsed rows
    """
    import pymupdf

    from .text_parser_utils import group_words_by_y

    doc = pymupdf.open(pdf_path)
    page = doc[pages[0] - 1]  # Convert to 0-indexed
    words = page.get_text("words")
    doc.close()

    # Split into left and right sub-tables within the left column of the page
    # Left sub-table: X < 130, Right sub-table: 130 <= X < 250
    left_words = [w for w in words if w[0] < 130 and 445 <= w[1] <= 665]
    right_words = [w for w in words if 130 <= w[0] < 250 and 445 <= w[1] <= 665]

    # Group by Y-coordinate
    left_rows = group_words_by_y(left_words)
    right_rows = group_words_by_y(right_words)

    headers = ["Challenge Rating", "XP"]
    parsed_rows: list[list[str | int]] = []

    # Process left sub-table (CR 0-13)
    for _y_pos, row_words in sorted(left_rows.items()):
        row_text = " ".join([text for x, text in sorted(row_words, key=lambda w: w[0])])

        # Skip header rows
        if "Challenge" in row_text or "Rating" in row_text or "XP" in row_text:
            continue

        words_list = row_text.split()
        if len(words_list) >= 2:
            cr = words_list[0]
            # Handle "0 or 10" case - take just "0"
            if cr == "0" and "or" in words_list:
                xp_idx = 3 if len(words_list) > 3 else 1
            else:
                xp_idx = 1

            if xp_idx < len(words_list):
                xp = words_list[xp_idx].replace(",", "")  # Remove commas
                try:
                    parsed_rows.append([cr, int(xp)])
                except ValueError:
                    pass  # Skip if XP is not a number

    # Process right sub-table (CR 14-30)
    for _y_pos, row_words in sorted(right_rows.items()):
        row_text = " ".join([text for x, text in sorted(row_words, key=lambda w: w[0])])

        # Skip header rows
        if "Challenge" in row_text or "Rating" in row_text or "XP" in row_text:
            continue

        words_list = row_text.split()
        if len(words_list) >= 2:
            cr = words_list[0]
            xp = words_list[1].replace(",", "")  # Remove commas
            try:
                parsed_rows.append([cr, int(xp)])
            except ValueError:
                pass  # Skip if XP is not a number

    if len(parsed_rows) < 33 or len(parsed_rows) > 35:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Expected 34 XP/CR rows, found {len(parsed_rows)}")

    return {"headers": headers, "rows": parsed_rows}
