"""Parse raw equipment table data into structured records."""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

from .column_mapper import ColumnMapper

# Container capacity data from SRD 5.1 Container Capacity table (pages 69-70)
# Maps simple_name to capacity string
CONTAINER_CAPACITIES = {
    "backpack": "1 cubic foot/30 pounds of gear",
    "barrel": "40 gallons liquid, 4 cubic feet solid",
    "basket": "2 cubic feet/40 pounds of gear",
    "bottle_glass": "1½ pints liquid",
    "bucket": "3 gallons liquid, 1/2 cubic foot solid",
    "chest": "12 cubic feet/300 pounds of gear",
    "flask_or_tankard": "1 pint liquid",
    "jug_or_pitcher": "1 gallon liquid",
    "pot_iron": "1 gallon liquid",
    "pouch": "1/5 cubic foot/6 pounds of gear",
    "sack": "1 cubic foot/30 pounds of gear",
    "vial": "4 ounces liquid",
    "waterskin": "4 pints liquid",
}


def parse_equipment_records(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:  # noqa: C901
    """Parse raw equipment items into structured records."""

    parsed: list[dict[str, Any]] = []
    items_by_id: dict[str, dict[str, Any]] = {}

    for raw_item in raw_items:
        try:
            parsed_item = _parse_single_item(raw_item)
        except Exception as exc:  # pragma: no cover - defensive fallback
            name = raw_item.get("table_row", ["unknown"])[0]
            print(f"Warning: Failed to parse {name}: {exc}")
            continue

        if parsed_item:
            item_id = parsed_item.get("id", "")

            # Handle duplicates by merging information
            if item_id in items_by_id:
                existing = items_by_id[item_id]

                # Merge capacity info from container capacity tables
                # (entries without cost but with capacity data)
                if not parsed_item.get("cost"):
                    table_row = raw_item.get("table_row", [])
                    # Check columns for capacity text (pint/gallon/cubic)
                    for col_text in table_row[1:]:
                        if col_text and any(
                            unit in col_text.lower() for unit in ["pint", "gallon", "cubic"]
                        ):
                            existing["capacity"] = col_text.strip()
                            break
                    # Don't add this entry to parsed list, just enriched existing
                    continue

                # If new item has cost but existing doesn't, replace
                if parsed_item.get("cost") and not existing.get("cost"):
                    items_by_id[item_id] = parsed_item
            else:
                # New entry - check if it's a capacity-only entry (no cost but has capacity)
                table_row = raw_item.get("table_row", [])
                has_capacity = any(
                    col and any(unit in str(col).lower() for unit in ["pint", "gallon", "cubic"])
                    for col in table_row[1:]
                )

                # Add capacity field if found
                if has_capacity and not parsed_item.get("cost"):
                    for col_text in table_row[1:]:
                        if col_text and any(
                            unit in str(col_text).lower() for unit in ["pint", "gallon", "cubic"]
                        ):
                            parsed_item["capacity"] = col_text.strip()
                            break

                items_by_id[item_id] = parsed_item

    # Apply known container capacities from Container Capacity table
    # This ensures all 13 containers have capacity data even if PDF extraction missed them
    for item in items_by_id.values():
        simple_name = item.get("simple_name", "")
        if simple_name in CONTAINER_CAPACITIES and not item.get("capacity"):
            item["capacity"] = CONTAINER_CAPACITIES[simple_name]

    # Add container property to items with capacity
    for item in items_by_id.values():
        if item.get("capacity"):
            item["container"] = True

    # Convert dict back to list
    parsed = list(items_by_id.values())
    return parsed


def _parse_single_item(raw_item: dict[str, Any]) -> dict[str, Any] | None:
    table_row = raw_item.get("table_row", [])
    if not table_row:
        return None

    name = table_row[0].strip()
    if not name:
        return None

    section = raw_item.get("section", {})
    category = section.get("category", "gear")
    headers = raw_item.get("table_headers")
    row_index = raw_item.get("row_index")

    item: dict[str, Any] = {
        "id": _generate_id(name),
        "name": name,
        "simple_name": _generate_simple_name(name),
        "category": category,
        "page": raw_item.get("page", 0),
        "source": "SRD 5.1",
        "is_magic": False,
    }

    if headers:
        item["table_header"] = headers

    if isinstance(row_index, int):
        item["row_index"] = row_index

    section_value = _stringify_section(section)
    if section_value:
        item["section"] = section_value

    column_map = _detect_column_map(headers, table_row, category)

    if category == "armor":
        _parse_armor_fields(item, table_row, section, column_map)
    elif category == "weapon":
        _parse_weapon_fields(item, table_row, section, column_map)
    else:
        _parse_general_fields(item, table_row, section, column_map)

    return item


def _parse_armor_fields(
    item: dict[str, Any],
    table_row: list[str],
    section: dict[str, Any],
    column_map: dict[str, int],
) -> None:
    # Use name-based inference for armor subcategory since PDF multi-column layout
    # makes section context unreliable (subcategories propagate incorrectly across columns)
    subcategory = _infer_armor_subcategory(item["name"])

    # Fallback to section context if name-based inference fails
    if not subcategory:
        subcategory = section.get("subcategory")

    if subcategory:
        item["sub_category"] = subcategory

    ac_text = _get_column_value(table_row, column_map, "armor_class")
    if ac_text:
        ac_value = _parse_armor_class(ac_text)
        if ac_value:
            item["armor_class"] = ac_value

    strength_text = _get_column_value(table_row, column_map, "strength")
    strength_req = _parse_strength_requirement(strength_text)
    if strength_req is not None:
        item["strength_req"] = strength_req

    stealth_text = _get_column_value(table_row, column_map, "stealth")
    stealth = _parse_stealth(stealth_text)
    if stealth is not None:
        item["stealth_disadvantage"] = stealth

    _apply_common_fields(item, table_row, column_map)


def _parse_weapon_fields(  # noqa: C901
    item: dict[str, Any],
    table_row: list[str],
    section: dict[str, Any],
    column_map: dict[str, int],
) -> None:
    subcategory = section.get("subcategory")
    if subcategory:
        item["sub_category"] = subcategory
        if "melee" in subcategory:
            item["weapon_type"] = "melee"
        elif "ranged" in subcategory:
            item["weapon_type"] = "ranged"

    # Extract proficiency level (simple/martial) from section context
    proficiency = _determine_weapon_proficiency(item, section)
    if proficiency:
        item["proficiency"] = proficiency

    damage_text = _get_column_value(table_row, column_map, "damage")
    if damage_text:
        damage = _parse_damage(damage_text)
        if damage:
            item["damage"] = damage

    properties_text = _get_column_value(table_row, column_map, "properties")

    # Extract embedded data from RAW properties text BEFORE cleaning
    if properties_text:
        versatile = _parse_versatile_damage_from_raw_text(properties_text)
        if versatile:
            item["versatile_damage"] = versatile

        range_info = _parse_range_from_raw_text(properties_text)
        if range_info:
            item["range"] = range_info

    # Now parse and clean properties (removes embedded data)
    properties = _parse_properties(properties_text)
    if properties:
        item["properties"] = properties

        # Determine weapon type from property names
        ranged_prop = any(prop in ["thrown", "ammunition", "range"] for prop in properties)

        if ranged_prop:
            item["weapon_type"] = "ranged"
        elif "weapon_type" not in item:
            item["weapon_type"] = "melee"

    _apply_common_fields(item, table_row, column_map)


def _parse_general_fields(
    item: dict[str, Any],
    table_row: list[str],
    section: dict[str, Any],
    column_map: dict[str, int],
) -> None:
    subcategory = section.get("subcategory")
    if subcategory:
        item["sub_category"] = subcategory

    _apply_common_fields(item, table_row, column_map)


def _apply_common_fields(
    item: dict[str, Any], table_row: list[str], column_map: dict[str, int]
) -> None:
    cost = _parse_cost(table_row, column_map)
    if cost:
        item["cost"] = cost

    weight_lb, weight_raw = _parse_weight(table_row, column_map)
    if weight_lb is not None or weight_raw is not None:
        item["weight_lb"] = weight_lb
        item["weight_raw"] = weight_raw


def _detect_column_map(
    headers: list[str] | None, table_row: list[str], category: str
) -> dict[str, int]:
    """Detect column mapping using ColumnMapper.

    Args:
        headers: Column headers if available
        table_row: Sample data row for heuristic detection
        category: Equipment category (armor, weapon, gear, etc.)

    Returns:
        Dictionary mapping field names to column indices
    """
    mapper = ColumnMapper(category=category)
    return mapper.build_map(headers, table_row)


def _parse_cost(table_row: list[str], column_map: dict[str, int]) -> dict[str, Any] | None:
    cost_text = _get_column_value(table_row, column_map, "cost")
    if cost_text:
        cost = _parse_cost_value(cost_text)
        if cost:
            return cost

    for cell in table_row:
        cost = _parse_cost_value(cell)
        if cost:
            return cost

    return None


_COST_PATTERN = re.compile(r"(\d+(?:,\d{3})*)\s*(cp|sp|ep|gp|pp)", re.IGNORECASE)


def _parse_cost_value(cell: str | None) -> dict[str, Any] | None:
    if not cell:
        return None

    match = _COST_PATTERN.search(cell.lower())
    if not match:
        return None

    amount = int(match.group(1).replace(",", ""))
    currency = match.group(2)
    return {"amount": amount, "currency": currency}


def _parse_weight(
    table_row: list[str], column_map: dict[str, int]
) -> tuple[float | None, str | None]:
    weight_text = _get_column_value(table_row, column_map, "weight")
    if weight_text:
        parsed = _parse_weight_value(weight_text)
        if parsed[0] is not None or parsed[1] is not None:
            return parsed

    for cell in table_row:
        parsed = _parse_weight_value(cell)
        if parsed[0] is not None or parsed[1] is not None:
            return parsed

    return (None, None)


def _parse_weight_value(weight_str: str | None) -> tuple[float | None, str | None]:
    if weight_str is None:
        return (None, None)

    weight_raw = weight_str.strip()
    if not weight_raw:
        return (None, None)

    normalized = (
        weight_raw.lower().replace("lbs.", "lb.").replace("lbs", "lb").replace("pounds", "lb")
    )

    if normalized in {"—", "-", "–"}:
        return (None, weight_raw)

    if "lb" not in normalized:
        # Preserve descriptive weights that contain digits (e.g., "10 crates") but
        # ignore entries without numeric information.
        return (None, weight_raw if any(ch.isdigit() for ch in weight_raw) else None)

    value_part = normalized.split("lb")[0].strip()
    value_part = value_part.replace("½", "1/2").replace("¼", "1/4").replace("¾", "3/4")
    value_part = re.sub(r"[\-\u2013]", " ", value_part)
    value_part = value_part.replace(",", "")

    try:
        value = _parse_fractional_number(value_part)
    except ValueError:
        value = None

    if value is None:
        return (None, weight_raw)

    return (float(value), weight_raw)


def _parse_fractional_number(value_part: str) -> float | None:
    if not value_part:
        return None

    pieces = [piece for piece in value_part.split() if piece]
    if not pieces:
        return None

    total = 0.0
    found = False
    for piece in pieces:
        if "/" in piece:
            total += float(Fraction(piece))
            found = True
        else:
            try:
                total += float(piece)
                found = True
            except ValueError:
                return None

    return total if found else None


def _parse_armor_class(ac_text: str) -> dict[str, Any] | None:
    ac_text = ac_text.strip()
    match = re.search(r"(\d+)", ac_text)
    if not match:
        return None

    base = int(match.group(1))
    armor_class: dict[str, Any] = {"base": base}

    lower = ac_text.lower()
    if "dex" in lower:
        armor_class["dex_bonus"] = True
        max_match = re.search(r"max[^\d]*(\d+)", lower)
        if max_match:
            armor_class["max_bonus"] = int(max_match.group(1))
    else:
        armor_class["dex_bonus"] = False

    return armor_class


def _parse_strength_requirement(text: str | None) -> int | None:
    if not text:
        return None

    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def _parse_stealth(text: str | None) -> bool | None:
    if not text:
        return None

    lower = text.lower().strip()
    if "disadvantage" in lower:
        return True
    if lower in {"—", "-", "–", "none"}:
        return False
    return None


def _parse_damage(damage_text: str | None) -> dict[str, str] | None:
    if not damage_text:
        return None

    damage_text = damage_text.strip()
    match = re.match(r"(\d+d\d+)\s+(\w+)", damage_text)
    if match:
        return {"dice": match.group(1), "type": match.group(2)}

    return None


def _parse_properties(prop_text: str | None) -> list[str] | None:
    if not prop_text:
        return None

    if prop_text.strip() in {"—", "-", ""}:
        return None

    properties: list[str] = []
    for part in prop_text.split(","):
        cleaned = part.strip()
        if cleaned and cleaned not in {"—", "-"}:
            # Strip embedded data in parentheses (e.g., "versatile (1d10)" → "versatile")
            prop_name = re.sub(r"\s*\([^)]+\)", "", cleaned).strip()
            # Fix Unicode dash issues: various dash chars → regular hyphen
            # Includes: soft hyphen (U+00AD), non-breaking hyphen (U+2011),
            # figure dash (U+2012), en dash (U+2013), em dash (U+2014)
            prop_name = re.sub(r"[\u00ad\u2010-\u2014]+", "-", prop_name)
            # Convert to underscore for consistency
            prop_name = prop_name.replace("-", "_")
            # Normalize multiple underscores to single underscore
            prop_name = re.sub(r"_+", "_", prop_name)
            properties.append(prop_name.lower())

    return properties if properties else None


def _parse_versatile_damage_from_raw_text(raw_text: str) -> dict[str, str] | None:
    """Extract versatile damage from raw properties text before cleaning.

    Example: "Versatile (1d10)" → {"dice": "1d10"}
    """
    match = re.search(r"versatile\s*\(([^)]+)\)", raw_text, re.IGNORECASE)
    if not match:
        return None

    dice_match = re.search(r"(\d+d\d+)", match.group(1))
    if dice_match:
        return {"dice": dice_match.group(1)}
    return None


def _parse_range_from_raw_text(raw_text: str) -> dict[str, int] | None:
    """Extract range from raw properties text before cleaning.

    Example: "Thrown (range 20/60)" → {"normal": 20, "long": 60}
    Example: "Ammunition (range 80/320)" → {"normal": 80, "long": 320}
    """
    match = re.search(r"range[^\d]*(\d+)\s*/\s*(\d+)", raw_text, re.IGNORECASE)
    if match:
        return {"normal": int(match.group(1)), "long": int(match.group(2))}
    return None


def _get_column_value(table_row: list[str], column_map: dict[str, int], key: str) -> str | None:
    idx = column_map.get(key)
    if idx is None or idx >= len(table_row):
        return None
    return table_row[idx].strip()


def _stringify_section(section: dict[str, Any]) -> str | None:
    if not isinstance(section, dict):
        return None

    category = section.get("category")
    subcategory = section.get("subcategory")
    if category and subcategory:
        return f"{category}:{subcategory}"
    return category or subcategory


def _generate_id(name: str) -> str:
    identifier = name.lower()
    identifier = re.sub(r"[^\w\s-]", "", identifier)
    identifier = re.sub(r"[\s_]+", "-", identifier)
    identifier = re.sub(r"-+", "-", identifier).strip("-")
    return f"item:{identifier}"


def _generate_simple_name(name: str) -> str:
    simple = re.sub(r"\([^)]*\)", "", name)
    simple = simple.replace(",", "")
    simple = simple.lower().strip()
    return re.sub(r"\s+", " ", simple)


def _determine_weapon_proficiency(item: dict[str, Any], section: dict[str, Any]) -> str | None:
    """Determine weapon proficiency level from section context.

    Args:
        item: The weapon item being parsed
        section: Section context with category and subcategory

    Returns:
        "simple" or "martial" if determinable, None otherwise
    """
    if item.get("category") != "weapon":
        return None

    # Try section-based detection first
    section_text = _stringify_section(section)
    if section_text:
        section_lower = section_text.lower()
        if "simple" in section_lower:
            return "simple"
        elif "martial" in section_lower:
            return "martial"

    # Fallback: check subcategory field directly
    subcategory = section.get("subcategory", "")
    if isinstance(subcategory, str):
        if "simple" in subcategory.lower():
            return "simple"
        elif "martial" in subcategory.lower():
            return "martial"

    # Final fallback: name-based lookup (SRD 5.1 weapon classifications)
    return _infer_weapon_proficiency(item["name"])


def _infer_weapon_proficiency(weapon_name: str) -> str | None:
    """Infer weapon proficiency from item name.

    Fallback for when PDF section context is unreliable.
    Based on SRD 5.1 weapon classifications (pages 65-66).
    """
    name_lower = weapon_name.lower().strip()

    # Simple weapons (SRD 5.1 page 65)
    simple_weapons = {
        "club",
        "dagger",
        "greatclub",
        "handaxe",
        "javelin",
        "light hammer",
        "mace",
        "quarterstaff",
        "sickle",
        "spear",
        "crossbow",
        "light crossbow",
        "dart",
        "shortbow",
        "sling",
    }
    if name_lower in simple_weapons or "crossbow, light" in name_lower:
        return "simple"

    # Martial weapons (SRD 5.1 page 66)
    martial_weapons = {
        "battleaxe",
        "flail",
        "glaive",
        "greataxe",
        "greatsword",
        "halberd",
        "lance",
        "longsword",
        "maul",
        "morningstar",
        "pike",
        "rapier",
        "scimitar",
        "shortsword",
        "trident",
        "war pick",
        "warhammer",
        "whip",
        "blowgun",
        "hand crossbow",
        "heavy crossbow",
        "longbow",
        "net",
    }
    if name_lower in martial_weapons or any(
        weapon in name_lower for weapon in ["crossbow, hand", "crossbow, heavy"]
    ):
        return "martial"

    return None


def _infer_armor_subcategory(armor_name: str) -> str | None:
    """Infer armor subcategory from item name.

    Fallback for when PDF table layout makes section context unreliable.
    Based on SRD 5.1 armor classifications.
    """
    name_lower = armor_name.lower().strip()

    # Light armor
    light_armor = {"padded", "leather", "studded leather", "studded"}
    if name_lower in light_armor:
        return "light"

    # Medium armor
    medium_armor = {
        "hide",
        "chain shirt",
        "scale mail",
        "breastplate",
        "half plate",
        "half-plate",
    }
    if name_lower in medium_armor:
        return "medium"

    # Heavy armor
    heavy_armor = {"ring mail", "chain mail", "splint", "plate"}
    if name_lower in heavy_armor:
        return "heavy"

    # Shield is neither light/medium/heavy
    if "shield" in name_lower:
        return None

    return None
