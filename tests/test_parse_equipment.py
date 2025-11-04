from __future__ import annotations

from srd_builder.parse_equipment import parse_equipment_records


def test_parse_equipment_armor_uses_headers() -> None:
    raw_item = {
        "table_row": [
            "Chain Shirt",
            "50 gp",
            "AC 13 + Dex modifier (max 2)",
            "Str 13",
            "Disadvantage",
            "40 lb.",
        ],
        "table_headers": [
            "Armor",
            "Cost",
            "Armor Class (AC)",
            "Strength",
            "Stealth",
            "Weight",
        ],
        "section": {"category": "armor", "subcategory": "medium"},
        "page": 64,
        "row_index": 1,
    }

    item = parse_equipment_records([raw_item])[0]

    assert item["sub_category"] == "medium"
    assert item["armor_class"] == {
        "base": 13,
        "dex_bonus": True,
        "max_bonus": 2,
    }
    assert item["strength_req"] == 13
    assert item["stealth_disadvantage"] is True
    assert item["weight_lb"] == 40.0
    assert item["weight_raw"] == "40 lb."
    assert item["cost"] == {"amount": 50, "currency": "gp"}
    assert item["source"] == "SRD 5.1"
    assert item["table_header"] == raw_item["table_headers"]
    assert item["row_index"] == 1


def test_parse_equipment_weapon_range_and_versatile() -> None:
    raw_item = {
        "table_row": [
            "Dagger",
            "2 gp",
            "1d4 piercing",
            "1 lb.",
            "Finesse, light, thrown (range 20/60)",
        ],
        "table_headers": [
            "Weapon",
            "Cost",
            "Damage",
            "Weight",
            "Properties",
        ],
        "section": {"category": "weapon", "subcategory": "simple_melee"},
        "page": 66,
    }

    item = parse_equipment_records([raw_item])[0]

    assert item["damage"] == {"dice": "1d4", "type": "piercing"}
    # Properties should be clean (no embedded data)
    assert item["properties"] == [
        "finesse",
        "light",
        "thrown",
    ]
    assert "versatile_damage" not in item
    # Range extracted from embedded data in properties
    assert item["range"] == {"normal": 20, "long": 60}
    assert item["weapon_type"] == "ranged"
    assert item["proficiency"] == "simple"
    assert item["weight_lb"] == 1.0
    assert item["weight_raw"] == "1 lb."


def test_parse_equipment_weapon_versatile_damage() -> None:
    raw_item = {
        "table_row": [
            "Longsword",
            "15 gp",
            "1d8 slashing",
            "3 lb.",
            "Versatile (1d10)",
        ],
        "table_headers": [
            "Weapon",
            "Cost",
            "Damage",
            "Weight",
            "Properties",
        ],
        "section": {"category": "weapon", "subcategory": "martial_melee"},
        "page": 66,
    }

    item = parse_equipment_records([raw_item])[0]

    assert item["damage"] == {"dice": "1d8", "type": "slashing"}
    # Versatile damage extracted from embedded data in properties
    assert item["versatile_damage"] == {"dice": "1d10"}
    # Properties should be clean (no embedded data)
    assert item["properties"] == ["versatile"]
    assert item["weapon_type"] == "melee"
    assert item["proficiency"] == "martial"
    assert item["sub_category"] == "martial_melee"
    assert item["weight_lb"] == 3.0
    assert item["weight_raw"] == "3 lb."


def test_parse_equipment_fractional_weight() -> None:
    raw_item = {
        "table_row": ["Acid (vial)", "25 gp", "—", "1/2 lb."],
        "table_headers": ["Item", "Cost", "Notes", "Weight"],
        "section": {"category": "gear", "subcategory": "adventuring_gear"},
        "page": 153,
    }

    item = parse_equipment_records([raw_item])[0]

    assert item["weight_lb"] == 0.5
    assert item["weight_raw"] == "1/2 lb."
    assert item["cost"] == {"amount": 25, "currency": "gp"}
