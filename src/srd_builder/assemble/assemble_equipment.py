#!/usr/bin/env python3
"""Assemble equipment from normalized tables.

Replaces PyMuPDF-based extract_equipment.py with table-based assembly.
Reads from tables.json (already normalized) and assembles equipment items.

Flow:
    tables.json → assemble_equipment() → equipment items
    └─ Reuses parse_equipment.py parsers for complex fields
"""

from __future__ import annotations

import logging
from typing import Any

from ..parse.parse_equipment import (
    _generate_id,
    _generate_simple_name,
    _parse_armor_class,
    _parse_cost_value,
    _parse_damage,
    _parse_properties,
    _parse_range_from_raw_text,
    _parse_stealth,
    _parse_strength_requirement,
    _parse_versatile_damage_from_raw_text,
    _parse_weight_value,
)

logger = logging.getLogger(__name__)


def _extract_page(table: dict[str, Any]) -> int:
    """Extract page number from table metadata.

    Page can be an int or a list[int]. Returns first page if list.
    """
    page = table.get("page", 0)
    if isinstance(page, list):
        return page[0] if page else 0
    return page if isinstance(page, int) else 0


# Equipment table names (from tables.json)
EQUIPMENT_TABLES = [
    "armor",
    "weapons",
    "tools",
    "adventure_gear",
    "container_capacity",
    "mounts_and_other_animals",
    "food_drink_lodging",
    "services",
    "tack_harness_vehicles",
    "waterborne_vehicles",
]


def assemble_equipment_from_tables(tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Assemble equipment items from normalized tables.

    Args:
        tables: List of table dictionaries from tables.json

    Returns:
        List of equipment item dictionaries
    """
    logger.info("Assembling equipment from tables...")

    equipment_items: list[dict[str, Any]] = []
    items_by_id: dict[str, dict[str, Any]] = {}

    # Build container capacity lookup first (for cross-reference)
    container_capacities = _build_container_capacity_map(tables)

    # Process each equipment table
    for table in tables:
        simple_name = table.get("simple_name", "")
        if simple_name not in EQUIPMENT_TABLES:
            continue

        logger.debug(f"Processing table: {simple_name}")

        # Route to appropriate assembler
        if simple_name == "armor":
            items = _assemble_armor(table)
        elif simple_name == "weapons":
            items = _assemble_weapons(table)
        elif simple_name == "tools":
            items = _assemble_tools(table)
        elif simple_name == "adventure_gear":
            items = _assemble_adventure_gear(table, container_capacities)
        elif simple_name == "container_capacity":
            # Already processed for cross-reference, skip item creation
            continue
        elif simple_name == "mounts_and_other_animals":
            items = _assemble_mounts(table)
        elif simple_name == "food_drink_lodging":
            items = _assemble_food_drink_lodging(table)
        elif simple_name == "services":
            items = _assemble_services(table)
        elif simple_name == "tack_harness_vehicles":
            items = _assemble_tack_vehicles(table)
        elif simple_name == "waterborne_vehicles":
            items = _assemble_waterborne_vehicles(table)
        else:
            logger.warning(f"Unknown equipment table: {simple_name}")
            continue

        # Merge items (handle potential duplicates)
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            if item_id in items_by_id:
                # Merge strategy: prefer items with more data
                existing = items_by_id[item_id]
                if item.get("cost") and not existing.get("cost"):
                    items_by_id[item_id] = item
                elif item.get("capacity") and not existing.get("capacity"):
                    existing["capacity"] = item["capacity"]
            else:
                items_by_id[item_id] = item

    equipment_items = list(items_by_id.values())

    # Add extended items (items referenced but not in SRD tables)
    extended_items = _add_extended_equipment(items_by_id)
    equipment_items.extend(extended_items)

    # Add equipment packs (from prose extraction, not tables)
    pack_items = _assemble_equipment_packs(items_by_id)
    equipment_items.extend(pack_items)

    # Add descriptions to items (from prose sections)
    _add_item_descriptions(equipment_items)

    logger.info(
        f"Assembled {len(equipment_items)} equipment items "
        f"({len(extended_items)} extended, {len(pack_items)} packs)"
    )

    return equipment_items


def _build_container_capacity_map(tables: list[dict[str, Any]]) -> dict[str, str]:
    """Build lookup map of container names to capacity strings.

    Args:
        tables: List of all tables

    Returns:
        Dict mapping simple_name → capacity string
    """
    capacity_map: dict[str, str] = {}

    for table in tables:
        if table.get("simple_name") != "container_capacity":
            continue

        columns = table.get("columns", [])
        rows = table.get("rows", [])

        # Find column indices
        container_idx = next(
            (i for i, col in enumerate(columns) if "container" in col["name"].lower()), 0
        )
        capacity_idx = next(
            (i for i, col in enumerate(columns) if "capacity" in col["name"].lower()), 1
        )

        for row in rows:
            if len(row) > max(container_idx, capacity_idx):
                container_name = str(row[container_idx]).strip()
                capacity = str(row[capacity_idx]).strip()

                if container_name and capacity:
                    simple_name = _generate_simple_name(container_name)
                    capacity_map[simple_name] = capacity

    logger.debug(f"Built container capacity map: {len(capacity_map)} containers")
    return capacity_map


def _assemble_armor(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble armor items from armor table.

    Table columns: Armor | Cost | Armor Class (AC) | Strength | Stealth | Weight
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    # Detect column indices
    col_map = _build_column_map(columns, ["armor", "name", "item"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)
    ac_idx = col_map.get("armor_class", col_map.get("ac", 2))
    strength_idx = col_map.get("strength", None)  # May not exist in all armor tables
    stealth_idx = col_map.get("stealth", 3)
    weight_idx = col_map.get("weight", 4)

    # Track current subcategory from category headers
    current_sub_category = None

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        # Check if this is a category header row (no cost, empty other cells)
        is_header = len(row) > cost_idx and not str(row[cost_idx]).strip()
        if is_header and name:
            # Update current category based on header text
            name_lower = name.lower()
            if "light" in name_lower:
                current_sub_category = "light"
            elif "medium" in name_lower:
                current_sub_category = "medium"
            elif "heavy" in name_lower:
                current_sub_category = "heavy"
            elif "shield" in name_lower:
                current_sub_category = "shield"
            continue  # Skip header rows

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "armor",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "armor",
            "row_index": row_index,
        }

        # Use current subcategory from most recent header
        if current_sub_category:
            item["sub_category"] = current_sub_category

        # Parse AC (may contain embedded max dex bonus)
        if len(row) > ac_idx:
            ac_text = str(row[ac_idx]).strip()
            # Check if stealth column contains the max bonus (table extraction issue)
            if len(row) > stealth_idx:
                stealth_or_max = str(row[stealth_idx]).strip()
                if stealth_or_max.startswith("(max") and ")" in stealth_or_max:
                    # This is actually part of AC, append it
                    ac_text = f"{ac_text} {stealth_or_max}"

            ac_value = _parse_armor_class(ac_text)
            if ac_value:
                item["armor_class"] = ac_value

        # Parse strength requirement (if column exists)
        if strength_idx is not None and len(row) > strength_idx:
            strength_text = str(row[strength_idx]).strip()
            if strength_text and strength_text != "—":
                strength_req = _parse_strength_requirement(strength_text)
                if strength_req is not None:
                    item["strength_req"] = strength_req

        # Parse stealth disadvantage (skip if it was actually AC max bonus)
        if len(row) > stealth_idx:
            stealth_text = str(row[stealth_idx]).strip()
            # Skip if this was actually the max dex bonus for AC
            if not stealth_text.startswith("(max"):
                # Fallback: Check if stealth column contains strength req (table may be misaligned)
                if "strength_req" not in item and (
                    "str" in stealth_text.lower()
                    or (stealth_text.isdigit() and len(stealth_text) <= 2)
                ):
                    strength_req = _parse_strength_requirement(stealth_text)
                    if strength_req is not None:
                        item["strength_req"] = strength_req
                else:
                    stealth = _parse_stealth(stealth_text)
                    if stealth is not None:
                        item["stealth_disadvantage"] = stealth

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        # Parse weight (skip em-dash which means no data)
        if len(row) > weight_idx:
            weight_text = str(row[weight_idx]).strip()
            # Skip unicode em-dash (—) and regular dash
            if weight_text not in ["—", "—", "-", ""]:
                weight_lb, weight_raw = _parse_weight_value(weight_text)
                if weight_lb is not None:
                    item["weight_lb"] = weight_lb
                if weight_raw:
                    item["weight_raw"] = weight_raw

        items.append(item)

    logger.debug(f"Assembled {len(items)} armor items")
    return items


def _assemble_weapons(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble weapon items from weapons table.

    Table columns: Name | Cost | Damage | Weight | Properties
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    # Detect column indices
    col_map = _build_column_map(columns, ["name", "weapon"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)
    damage_idx = col_map.get("damage", 2)
    weight_idx = col_map.get("weight", 3)
    properties_idx = col_map.get("properties", 4)

    # Track current weapon category from headers
    current_proficiency = None  # simple or martial
    current_weapon_type = None  # melee or ranged

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        # Check if this is a category header row (no cost)
        is_header = len(row) > cost_idx and not str(row[cost_idx]).strip()
        if is_header and name:
            # Update current category from header text
            name_lower = name.lower()
            if "simple" in name_lower:
                current_proficiency = "simple"
            elif "martial" in name_lower:
                current_proficiency = "martial"

            if "melee" in name_lower:
                current_weapon_type = "melee"
            elif "ranged" in name_lower:
                current_weapon_type = "ranged"
            continue  # Skip header rows

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "weapon",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "weapons",
            "row_index": row_index,
        }

        # Use current proficiency and weapon_type from most recent header
        proficiency = current_proficiency
        weapon_type = current_weapon_type

        if proficiency:
            item["proficiency"] = proficiency
        if weapon_type:
            item["weapon_type"] = weapon_type

        # Build subcategory from proficiency + weapon_type
        if proficiency and weapon_type:
            item["sub_category"] = f"{proficiency}-{weapon_type}"

        # Parse damage
        if len(row) > damage_idx:
            damage_text = str(row[damage_idx]).strip()
            damage = _parse_damage(damage_text)
            if damage:
                item["damage"] = damage

        # Parse properties (includes embedded range/versatile data)
        if len(row) > properties_idx:
            properties_text = str(row[properties_idx]).strip()

            # Extract embedded data BEFORE cleaning
            versatile = _parse_versatile_damage_from_raw_text(properties_text)
            if versatile:
                item["versatile_damage"] = versatile

            range_info = _parse_range_from_raw_text(properties_text)
            if range_info:
                item["range"] = range_info

            # Parse and clean properties
            properties = _parse_properties(properties_text)
            if properties:
                item["properties"] = properties

                # Infer weapon_type from properties if not set
                if not weapon_type:
                    ranged_props = any(p in ["thrown", "ammunition", "range"] for p in properties)
                    item["weapon_type"] = "ranged" if ranged_props else "melee"

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        # Parse weight
        if len(row) > weight_idx:
            weight_text = str(row[weight_idx]).strip()
            weight_lb, weight_raw = _parse_weight_value(weight_text)
            if weight_lb is not None or weight_raw is not None:
                item["weight_lb"] = weight_lb
                item["weight_raw"] = weight_raw

        items.append(item)

    logger.debug(f"Assembled {len(items)} weapon items")
    return items


def _assemble_tools(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble tool items from tools table.

    Table columns: Item | Cost | Weight
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    col_map = _build_column_map(columns, ["item", "name"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)
    weight_idx = col_map.get("weight", 2)

    # Get category metadata
    category_metadata = table.get("category_metadata", {})
    categories = category_metadata.get("categories", {})

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "gear",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "tools",
            "row_index": row_index,
        }

        # Infer subcategory from table categories
        sub_category = _infer_tool_subcategory(name, categories, row_index)
        if sub_category:
            item["sub_category"] = sub_category

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        # Parse weight
        if len(row) > weight_idx:
            weight_text = str(row[weight_idx]).strip()
            weight_lb, weight_raw = _parse_weight_value(weight_text)
            if weight_lb is not None or weight_raw is not None:
                item["weight_lb"] = weight_lb
                item["weight_raw"] = weight_raw

        items.append(item)

    logger.debug(f"Assembled {len(items)} tool items")
    return items


def _assemble_adventure_gear(
    table: dict[str, Any], container_capacities: dict[str, str]
) -> list[dict[str, Any]]:
    """Assemble adventure gear items.

    Table columns: Item | Cost | Weight
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    col_map = _build_column_map(columns, ["item", "name"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)
    weight_idx = col_map.get("weight", 2)

    # Get category metadata
    category_metadata = table.get("category_metadata", {})
    categories = category_metadata.get("categories", {})

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "gear",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "adventure_gear",
            "row_index": row_index,
        }

        # Infer subcategories from table categories
        sub_categories = _infer_gear_subcategories(name, categories, row_index)

        # Check if this is a container (from cross-reference)
        simple_name = item["simple_name"]
        if simple_name in container_capacities:
            item["capacity"] = container_capacities[simple_name]
            if "container" not in sub_categories:
                sub_categories.append("container")

        if sub_categories:
            item["sub_category"] = sub_categories if len(sub_categories) > 1 else sub_categories[0]

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        # Parse weight
        if len(row) > weight_idx:
            weight_text = str(row[weight_idx]).strip()
            weight_lb, weight_raw = _parse_weight_value(weight_text)
            if weight_lb is not None or weight_raw is not None:
                item["weight_lb"] = weight_lb
                item["weight_raw"] = weight_raw

        items.append(item)

    logger.debug(f"Assembled {len(items)} adventure gear items")
    return items


def _assemble_mounts(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble mount/animal items.

    Table columns: Item | Cost | Speed | Carrying Capacity
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    col_map = _build_column_map(columns, ["item", "name"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "mount",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "mounts_and_other_animals",
            "row_index": row_index,
        }

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        # Note: Speed and carrying capacity could be parsed here if needed
        # For now, keeping minimal implementation

        items.append(item)

    logger.debug(f"Assembled {len(items)} mount items")
    return items


def _assemble_food_drink_lodging(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble food/drink/lodging items.

    Table columns: Item | Cost
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    col_map = _build_column_map(columns, ["item", "name"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "consumable",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "food_drink_lodging",
            "row_index": row_index,
        }

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        items.append(item)

    logger.debug(f"Assembled {len(items)} food/drink/lodging items")
    return items


def _assemble_services(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble service items.

    Table columns: Service | Cost
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    col_map = _build_column_map(columns, ["service", "name"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "service",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "services",
            "row_index": row_index,
        }

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        items.append(item)

    logger.debug(f"Assembled {len(items)} service items")
    return items


def _assemble_tack_vehicles(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble tack/harness/vehicle items.

    Table columns: Item | Cost | Weight
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    col_map = _build_column_map(columns, ["item", "name"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)
    weight_idx = col_map.get("weight", 2)

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        # Determine if vehicle or tack
        name_lower = name.lower()
        is_vehicle = any(v in name_lower for v in ["cart", "carriage", "chariot", "sled", "wagon"])
        category = "vehicle" if is_vehicle else "gear"
        sub_category = "land" if is_vehicle else None

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": category,
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "tack_harness_vehicles",
            "row_index": row_index,
        }

        if sub_category:
            item["sub_category"] = sub_category

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        # Parse weight
        if len(row) > weight_idx:
            weight_text = str(row[weight_idx]).strip()
            weight_lb, weight_raw = _parse_weight_value(weight_text)
            if weight_lb is not None or weight_raw is not None:
                item["weight_lb"] = weight_lb
                item["weight_raw"] = weight_raw

        items.append(item)

    logger.debug(f"Assembled {len(items)} tack/vehicle items")
    return items


def _assemble_waterborne_vehicles(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble waterborne vehicle items.

    Table columns: Item | Cost | Speed
    """
    items: list[dict[str, Any]] = []
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    page = _extract_page(table)

    col_map = _build_column_map(columns, ["item", "name"])
    name_idx = col_map.get("name", 0)
    cost_idx = col_map.get("cost", 1)

    for row_index, row in enumerate(rows):
        if len(row) <= name_idx:
            continue

        name = str(row[name_idx]).strip()
        if not name:
            continue

        item: dict[str, Any] = {
            "id": _generate_id(name),
            "name": name,
            "simple_name": _generate_simple_name(name),
            "category": "vehicle",
            "sub_category": "water",
            "page": page,
            "source": "SRD 5.1",
            "is_magic": False,
            "source_table": "waterborne_vehicles",
            "row_index": row_index,
        }

        # Parse cost
        if len(row) > cost_idx:
            cost_text = str(row[cost_idx]).strip()
            cost = _parse_cost_value(cost_text)
            if cost:
                item["cost"] = cost

        # Note: Speed could be parsed here if needed

        items.append(item)

    logger.debug(f"Assembled {len(items)} waterborne vehicle items")
    return items


# Helper functions for column mapping and subcategory inference


def _build_column_map(columns: list[dict[str, Any]], name_hints: list[str]) -> dict[str, int]:
    """Build column name → index mapping.

    Args:
        columns: List of column definitions from table
        name_hints: Possible names for the "name" column

    Returns:
        Dict mapping field names to column indices
    """
    col_map: dict[str, int] = {}

    for idx, col in enumerate(columns):
        col_name = col.get("name", "").lower().strip()

        # Map common column names (order matters - check specific patterns first)
        # Check AC/armor class before name hints (since "armor class" contains substrings)
        if "ac" in col_name or "armor class" in col_name:
            col_map["armor_class"] = idx
        elif "cost" in col_name or "price" in col_name:
            col_map["cost"] = idx
        elif "weight" in col_name:
            col_map["weight"] = idx
        elif "damage" in col_name:
            col_map["damage"] = idx
        elif "properties" in col_name or "property" in col_name:
            col_map["properties"] = idx
        elif "strength" in col_name or "str" == col_name:
            col_map["strength"] = idx
        elif "stealth" in col_name:
            col_map["stealth"] = idx
        # Check name hints last (after all other specific patterns)
        elif any(hint in col_name for hint in name_hints):
            col_map["name"] = idx

    return col_map


def _infer_armor_subcategory(name: str, categories: dict[str, Any], row_index: int) -> str | None:
    """Infer armor subcategory from table categories or name.

    Args:
        name: Armor name
        categories: Category metadata from table
        row_index: Row index in table

    Returns:
        Subcategory: "light", "medium", "heavy", or "shield"
    """
    # Check if this row is in a category
    for cat_name, cat_data in categories.items():
        cat_items = cat_data.get("items", [])
        if any(item.get("row_index") == row_index for item in cat_items):
            cat_lower = cat_name.lower()
            if "light" in cat_lower:
                return "light"
            elif "medium" in cat_lower:
                return "medium"
            elif "heavy" in cat_lower:
                return "heavy"

    # Fallback: name-based inference
    name_lower = name.lower()
    if name_lower == "shield":
        return "shield"

    # Light armor
    if any(a in name_lower for a in ["padded", "leather", "studded"]):
        return "light"

    # Medium armor
    if any(a in name_lower for a in ["hide", "chain shirt", "scale", "breastplate", "half plate"]):
        return "medium"

    # Heavy armor
    if any(a in name_lower for a in ["ring mail", "chain mail", "splint", "plate"]):
        return "heavy"

    return None


def _infer_weapon_subcategory(
    name: str, categories: dict[str, Any], row_index: int
) -> tuple[str | None, str | None, str | None]:
    """Infer weapon subcategory, proficiency, and type from table categories.

    Args:
        name: Weapon name
        categories: Category metadata from table
        row_index: Row index in table

    Returns:
        Tuple of (subcategory, proficiency, weapon_type)
    """
    for cat_name, cat_data in categories.items():
        cat_items = cat_data.get("items", [])
        if any(item.get("row_index") == row_index for item in cat_items):
            cat_lower = cat_name.lower()

            # Determine proficiency and attack type
            proficiency = (
                "simple" if "simple" in cat_lower else "martial" if "martial" in cat_lower else None
            )
            weapon_type = (
                "melee" if "melee" in cat_lower else "ranged" if "ranged" in cat_lower else None
            )

            # Build subcategory
            if proficiency and weapon_type:
                subcategory = f"{proficiency}-{weapon_type}"
                return (subcategory, proficiency, weapon_type)

    return (None, None, None)


def _infer_tool_subcategory(name: str, categories: dict[str, Any], row_index: int) -> str | None:
    """Infer tool subcategory from table categories.

    Args:
        name: Tool name
        categories: Category metadata from table
        row_index: Row index in table

    Returns:
        Subcategory: "artisan", "gaming", "musical", or "other"
    """
    for cat_name, cat_data in categories.items():
        cat_items = cat_data.get("items", [])
        if any(item.get("row_index") == row_index for item in cat_items):
            cat_lower = cat_name.lower()
            if "artisan" in cat_lower:
                return "artisan"
            elif "gaming" in cat_lower or "game" in cat_lower:
                return "gaming"
            elif "musical" in cat_lower or "instrument" in cat_lower:
                return "musical"

    return "other"


def _infer_gear_subcategories(name: str, categories: dict[str, Any], row_index: int) -> list[str]:
    """Infer gear subcategories from table categories.

    Args:
        name: Gear name
        categories: Category metadata from table
        row_index: Row index in table

    Returns:
        List of subcategory strings
    """
    sub_categories: list[str] = []

    # Check table categories
    for cat_name, cat_data in categories.items():
        cat_items = cat_data.get("items", [])
        if any(item.get("row_index") == row_index for item in cat_items):
            cat_lower = cat_name.lower()

            if "ammunition" in cat_lower:
                sub_categories.append("ammunition")
            elif "arcane focus" in cat_lower or "arcane" in cat_lower:
                sub_categories.append("focus")
            elif "druidic focus" in cat_lower or "druidic" in cat_lower:
                sub_categories.append("druidic_focus")
            elif "holy symbol" in cat_lower or "holy" in cat_lower:
                sub_categories.append("holy_symbol")

    return sub_categories


def _assemble_equipment_packs(items_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Assemble equipment pack items from prose data.

    Equipment packs are described in prose on page 70, not in tables.
    This function creates structured pack items with validated contents.

    Args:
        items_by_id: Dict of existing equipment items (for validation)

    Returns:
        List of equipment pack items
    """
    from src.srd_builder.equipment_packs import (
        EQUIPMENT_PACKS,
        calculate_pack_weight,
        validate_pack_contents,
    )

    pack_items = []

    for pack_data in EQUIPMENT_PACKS:
        # Calculate total weight from contents
        total_weight = calculate_pack_weight(pack_data, items_by_id)

        # Validate contents
        validation = validate_pack_contents(pack_data, items_by_id)
        if validation["missing_count"] > 0:
            logger.warning(
                f"{pack_data['name']}: {validation['missing_count']} items not in equipment.json"
            )
            for missing in validation["missing_items"][:3]:
                logger.debug(f"  Missing: {missing}")

        # Create pack item
        simple_name = pack_data["name"].lower().replace("'", "").replace(" ", "_")
        item_id = f"item:{simple_name}"

        pack_item = {
            "id": item_id,
            "name": pack_data["name"],
            "simple_name": simple_name,
            "category": "gear",
            "sub_category": "equipment_pack",
            "description": pack_data["description"],
            "cost": {"amount": pack_data["cost_gp"], "currency": "gp"},
            "weight_lb": total_weight,
            "pack_contents": pack_data["contents"],
            "page": 70,
            "source": "SRD 5.1",
            "is_magic": False,
        }

        pack_items.append(pack_item)

    logger.info(f"Created {len(pack_items)} equipment packs")
    return pack_items


def _add_extended_equipment(items_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Add extended equipment items (referenced but not in SRD tables).

    These are items like "String" or "Alms box" that are referenced in equipment
    packs but don't appear in the SRD tables. Costs and weights are estimated
    based on similar items.

    Args:
        items_by_id: Dict of existing equipment items

    Returns:
        List of extended items that were added
    """
    from src.srd_builder.equipment_extended import get_extended_equipment

    extended = get_extended_equipment()
    added_items = []

    for item in extended:
        item_id = item["id"]
        # Only add if not already present
        if item_id not in items_by_id:
            items_by_id[item_id] = item
            added_items.append(item)
            logger.debug(f"Added extended item: {item['name']}")

    logger.info(f"Added {len(added_items)} extended equipment items")
    return added_items


def _add_item_descriptions(items: list[dict[str, Any]]) -> None:
    """Add prose descriptions to equipment items.

    Mutates items in place by adding 'description' field where available.

    Args:
        items: List of equipment items
    """
    from src.srd_builder.equipment_descriptions import get_description_lookup

    descriptions = get_description_lookup()
    added_count = 0

    for item in items:
        item_id = item.get("id")
        if item_id in descriptions:
            item["description"] = descriptions[item_id]
            added_count += 1

    logger.info(f"Added descriptions to {added_count} items")
