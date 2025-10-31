"""Parse raw equipment table data into structured records.

This module converts raw table_row data from extract_equipment.py into
structured equipment objects matching the equipment.schema.json.

Pure transformation - no I/O or logging at module level.
"""

from __future__ import annotations

import re
from typing import Any


def parse_equipment_records(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw equipment items into structured records.

    Args:
        raw_items: List of dicts with table_row, page, section, bbox

    Returns:
        List of structured equipment dicts matching schema
    """
    parsed = []
    for item in raw_items:
        try:
            parsed_item = _parse_single_item(item)
            if parsed_item:
                parsed.append(parsed_item)
        except Exception as e:
            # Skip items that fail parsing but log enough context to debug
            name = item.get("table_row", [None])[0] if item.get("table_row") else "unknown"
            print(f"Warning: Failed to parse {name}: {e}")
            continue

    return parsed


def _parse_single_item(raw_item: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single equipment item from raw table data."""
    table_row = raw_item.get("table_row", [])
    if not table_row:
        return None

    name = table_row[0].strip()
    if not name:
        return None

    section = raw_item.get("section", {})
    category = section.get("category", "gear")
    page = raw_item.get("page", 0)

    # Build base item
    item: dict[str, Any] = {
        "id": _generate_id(name),
        "name": name,
        "simple_name": _generate_simple_name(name),
        "category": category,
        "page": page,
        "src": "SRD 5.1",
    }

    # Parse category-specific fields
    if category == "armor":
        _parse_armor_fields(item, table_row, section)
    elif category == "weapon":
        _parse_weapon_fields(item, table_row, section)
    else:
        # gear, mount, trade_good, etc.
        _parse_general_fields(item, table_row)

    return item


def _parse_armor_fields(
    item: dict[str, Any], table_row: list[str], section: dict[str, Any]
) -> None:
    """Parse armor-specific fields from table row.

    Armor table columns (approx): Name | Type | Armor Class | Strength | Stealth | Weight | Cost
    """
    # Armor category from section context
    subcategory = section.get("subcategory")
    if subcategory:
        item["armor_category"] = subcategory  # light, medium, heavy

    # Column mapping (may vary by page layout)
    if len(table_row) >= 3:
        # Try to parse AC (usually column 2 or 3)
        for col_idx in range(1, min(len(table_row), 4)):
            ac_text = table_row[col_idx].strip()
            if ac_text and any(c.isdigit() for c in ac_text):
                ac_value = _parse_armor_class(ac_text)
                if ac_value:
                    item["armor_class"] = ac_value
                break

    # Parse cost (usually last or second-to-last column)
    cost = _parse_cost(table_row)
    if cost:
        item["cost"] = cost

    # Parse weight (column before cost, or earlier)
    weight = _parse_weight(table_row)
    if weight:
        item["weight"] = weight

    # Check for stealth disadvantage
    if any("disadvantage" in col.lower() for col in table_row):
        item["stealth_disadvantage"] = True


def _parse_weapon_fields(  # noqa: C901
    item: dict[str, Any], table_row: list[str], section: dict[str, Any]
) -> None:
    """Parse weapon-specific fields from table row.

    Weapon table columns (approx): Name | Cost | Damage | Weight | Properties
    """
    # Weapon category from section context (simple/martial)
    subcategory = section.get("subcategory")
    if subcategory:
        # subcategory is like "simple_melee", "martial_ranged"
        if "simple" in subcategory:
            item["weapon_category"] = "simple"
        elif "martial" in subcategory:
            item["weapon_category"] = "martial"

        if "melee" in subcategory:
            item["weapon_type"] = "melee"
        elif "ranged" in subcategory:
            item["weapon_type"] = "ranged"

    # Parse damage (usually column 2 or 3)
    damage = None
    for col_idx in range(1, min(len(table_row), 5)):
        damage = _parse_damage(table_row[col_idx])
        if damage:
            item["damage"] = damage
            break

    # Parse properties (usually last column)
    if len(table_row) >= 4:
        properties = _parse_properties(table_row[-1])
        if properties:
            item["properties"] = properties

            # Check for versatile in properties
            for prop in properties:
                if prop.startswith("versatile"):
                    versatile_dmg = _parse_versatile_damage(prop)
                    if versatile_dmg:
                        item["versatile_damage"] = versatile_dmg

            # Infer weapon_type from properties if not set
            if "weapon_type" not in item:
                if "thrown" in properties or "ammunition" in properties:
                    item["weapon_type"] = "ranged"
                else:
                    item["weapon_type"] = "melee"

    # Parse cost
    cost = _parse_cost(table_row)
    if cost:
        item["cost"] = cost

    # Parse weight
    weight = _parse_weight(table_row)
    if weight:
        item["weight"] = weight


def _parse_general_fields(item: dict[str, Any], table_row: list[str]) -> None:
    """Parse fields for general items (gear, mounts, trade goods)."""
    # Parse cost
    cost = _parse_cost(table_row)
    if cost:
        item["cost"] = cost

    # Parse weight if present
    weight = _parse_weight(table_row)
    if weight:
        item["weight"] = weight

    # Quantity if present (for trade goods like "1 lb of wheat")
    if len(table_row) >= 2:
        qty_text = table_row[1].strip()
        if qty_text and any(c.isdigit() for c in qty_text) and "lb" not in qty_text.lower():
            # Might be quantity
            item["quantity"] = qty_text


def _parse_cost(table_row: list[str]) -> dict[str, Any] | None:
    """Parse cost from table row.

    Examples: "15 gp", "5 sp", "1 cp", "50 gp"
    Returns: {"amount": 15, "currency": "gp"}
    """
    for col in table_row:
        col_lower = col.lower().strip()
        # Match patterns like "15 gp", "5 sp"
        match = re.search(r"(\d+(?:,\d{3})*)\s*(cp|sp|ep|gp|pp)", col_lower)
        if match:
            amount_str = match.group(1).replace(",", "")
            currency = match.group(2)
            try:
                amount = int(amount_str)
                return {"amount": amount, "currency": currency}
            except ValueError:
                continue

    return None


def _parse_weight(table_row: list[str]) -> str | None:
    """Parse weight from table row.

    Examples: "10 lb.", "3 lb", "1/4 lb"
    Returns: "10 lb." as string
    """
    for col in table_row:
        col_lower = col.lower().strip()
        if "lb" in col_lower and any(c.isdigit() for c in col_lower):
            # Clean up weight string
            weight = col.strip()
            # Remove trailing period if present, then add back for consistency
            weight = weight.rstrip(".")
            if weight:
                return f"{weight}."

    return None


def _parse_armor_class(ac_text: str) -> dict[str, Any] | None:
    """Parse armor class value.

    Examples:
        "11 + Dex modifier" -> {"base": 11, "dex_bonus": true}
        "16" -> {"base": 16, "dex_bonus": false}
        "12 + Dex modifier (max 2)" -> {"base": 12, "dex_bonus": true, "max_bonus": 2}
    """
    ac_text = ac_text.strip()

    # Extract base AC number
    match = re.search(r"(\d+)", ac_text)
    if not match:
        return None

    base = int(match.group(1))
    ac_dict: dict[str, Any] = {"base": base}

    # Check for dex modifier
    if "dex" in ac_text.lower():
        ac_dict["dex_bonus"] = True

        # Check for max bonus
        max_match = re.search(r"max[^\d]*(\d+)", ac_text.lower())
        if max_match:
            ac_dict["max_bonus"] = int(max_match.group(1))
    else:
        ac_dict["dex_bonus"] = False

    return ac_dict


def _parse_damage(damage_text: str) -> dict[str, str] | None:
    """Parse weapon damage.

    Examples:
        "1d8 slashing" -> {"dice": "1d8", "type": "slashing"}
        "1d6 piercing" -> {"dice": "1d6", "type": "piercing"}
    """
    damage_text = damage_text.strip()

    # Match patterns like "1d8 slashing", "2d6 bludgeoning"
    match = re.match(r"(\d+d\d+)\s+(\w+)", damage_text)
    if match:
        return {"dice": match.group(1), "type": match.group(2)}

    return None


def _parse_properties(prop_text: str) -> list[str] | None:
    """Parse weapon/item properties.

    Examples:
        "Finesse, light, thrown (range 20/60)" -> ["finesse", "light", "thrown", "range 20/60"]
        "Heavy, two-handed" -> ["heavy", "two-handed"]
    """
    if not prop_text or prop_text.strip() in ["—", "-", ""]:
        return None

    # Split on commas
    props = []
    parts = prop_text.split(",")

    for part in parts:
        part = part.strip()
        if part and part not in ["—", "-"]:
            # Normalize to lowercase except for values in parentheses
            if "(" in part:
                # Keep range values intact
                props.append(part.lower())
            else:
                props.append(part.lower())

    return props if props else None


def _parse_versatile_damage(versatile_prop: str) -> dict[str, str] | None:
    """Parse versatile damage from property string.

    Example: "versatile (1d10)" -> {"dice": "1d10"}
    """
    match = re.search(r"versatile\s*\(([^)]+)\)", versatile_prop, re.IGNORECASE)
    if match:
        damage_str = match.group(1).strip()
        # Extract just the dice (1d10) without damage type
        dice_match = re.search(r"(\d+d\d+)", damage_str)
        if dice_match:
            return {"dice": dice_match.group(1)}

    return None


def _generate_id(name: str) -> str:
    """Generate ID from item name.

    Examples:
        "Longsword" -> "longsword"
        "Chain Mail" -> "chain-mail"
        "Rope, hempen (50 feet)" -> "rope-hempen-50-feet"
    """
    # Lowercase and replace spaces/punctuation with hyphens
    id_str = name.lower()
    id_str = re.sub(r"[^\w\s-]", "", id_str)  # Remove special chars except space/hyphen
    id_str = re.sub(r"[\s_]+", "-", id_str)  # Replace spaces/underscores with hyphen
    id_str = re.sub(r"-+", "-", id_str)  # Collapse multiple hyphens
    id_str = id_str.strip("-")  # Remove leading/trailing hyphens

    return id_str


def _generate_simple_name(name: str) -> str:
    """Generate simple name for sorting/display.

    Examples:
        "Longsword" -> "longsword"
        "Chain Mail" -> "chain mail"
        "Rope, hempen (50 feet)" -> "rope hempen"
    """
    # Remove parenthetical content
    simple = re.sub(r"\([^)]*\)", "", name)
    # Remove commas
    simple = simple.replace(",", "")
    # Lowercase and strip
    simple = simple.lower().strip()
    # Collapse multiple spaces
    simple = re.sub(r"\s+", " ", simple)

    return simple
