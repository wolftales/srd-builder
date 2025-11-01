"""Parse raw equipment table data into structured records."""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any


def parse_equipment_records(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw equipment items into structured records."""

    parsed: list[dict[str, Any]] = []
    for raw_item in raw_items:
        try:
            parsed_item = _parse_single_item(raw_item)
        except Exception as exc:  # pragma: no cover - defensive fallback
            name = raw_item.get("table_row", ["unknown"])[0]
            print(f"Warning: Failed to parse {name}: {exc}")
            continue

        if parsed_item:
            parsed.append(parsed_item)

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

    damage_text = _get_column_value(table_row, column_map, "damage")
    if damage_text:
        damage = _parse_damage(damage_text)
        if damage:
            item["damage"] = damage

    properties_text = _get_column_value(table_row, column_map, "properties")
    properties = _parse_properties(properties_text)
    if properties:
        item["properties"] = properties

        versatile = _parse_versatile_damage_from_properties(properties)
        if versatile:
            item["versatile_damage"] = versatile

        range_info = _parse_range(properties)
        if range_info:
            item["range"] = range_info

        ranged_prop = any(
            prop.startswith("thrown") or prop.startswith("ammunition") or prop.startswith("range")
            for prop in properties
        )

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


def _detect_column_map(  # noqa: C901
    headers: list[str] | None, table_row: list[str], category: str
) -> dict[str, int]:
    column_map: dict[str, int] = {}

    if headers:
        for index, header in enumerate(headers):
            key = _match_header(header)
            if key:
                column_map.setdefault(key, index)

    if category == "armor" and "armor_class" not in column_map:
        for idx, cell in enumerate(table_row):
            lower = cell.lower()
            if "ac" in lower or "dex" in lower:
                column_map["armor_class"] = idx
                break

    if "cost" not in column_map:
        for idx, cell in enumerate(table_row):
            if _parse_cost_value(cell):
                column_map["cost"] = idx
                break

    if "weight" not in column_map:
        # Skip columns already mapped to avoid misdetection
        used_columns = set(column_map.values())
        for idx, cell in enumerate(table_row):
            if idx in used_columns:
                continue
            # Only accept cells that contain "lb" for heuristic weight detection
            # to avoid false positives like "15 gp" being treated as weight
            if "lb" in cell.lower():
                weight_candidate = _parse_weight_value(cell)
                if weight_candidate[0] is not None or weight_candidate[1] is not None:
                    column_map["weight"] = idx
                    break

    if category == "armor":
        if "strength" not in column_map:
            for idx, cell in enumerate(table_row):
                if "str" in cell.lower():
                    column_map["strength"] = idx
                    break
        if "stealth" not in column_map:
            for idx, cell in enumerate(table_row):
                if "stealth" in cell.lower():
                    column_map["stealth"] = idx
                    break

    if category == "weapon":
        if "damage" not in column_map:
            for idx, cell in enumerate(table_row):
                if _parse_damage(cell):
                    column_map["damage"] = idx
                    break
        if "properties" not in column_map and table_row:
            column_map["properties"] = len(table_row) - 1
    else:
        if "properties" not in column_map and table_row:
            column_map["properties"] = len(table_row) - 1

    return column_map


def _match_header(header: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", " ", header.lower()).strip()
    header_map = {
        "armor_class": ["armor class", "ac"],
        "cost": ["cost"],
        "weight": ["weight"],
        "strength": ["strength"],
        "stealth": ["stealth"],
        "damage": ["damage"],
        "properties": ["properties", "property"],
    }

    for key, tokens in header_map.items():
        for token in tokens:
            if token in normalized:
                return key
    return None


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
            properties.append(cleaned.lower())

    return properties if properties else None


def _parse_versatile_damage_from_properties(
    properties: list[str],
) -> dict[str, str] | None:
    for prop in properties:
        versatile = _parse_versatile_damage(prop)
        if versatile:
            return versatile
    return None


def _parse_versatile_damage(versatile_prop: str) -> dict[str, str] | None:
    match = re.search(r"versatile\s*\(([^)]+)\)", versatile_prop, re.IGNORECASE)
    if not match:
        return None

    dice_match = re.search(r"(\d+d\d+)", match.group(1))
    if dice_match:
        return {"dice": dice_match.group(1)}
    return None


def _parse_range(properties: list[str]) -> dict[str, int] | None:
    for prop in properties:
        match = re.search(r"range[^\d]*(\d+)\s*/\s*(\d+)", prop, re.IGNORECASE)
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
