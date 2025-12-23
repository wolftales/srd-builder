"""Tests for equipment pack validation."""

import json
from pathlib import Path

import pytest

from src.srd_builder.assemble.equipment_packs import EQUIPMENT_PACKS, validate_pack_contents


def test_validate_pack_contents_all_found():
    """All pack items should be found in equipment lookup."""
    pack = {
        "name": "Test Pack",
        "contents": [
            {"item_id": "item:rope-50-feet", "item_name": "Rope (50 feet)", "quantity": 1},
            {"item_id": "item:torch", "item_name": "Torch", "quantity": 10},
        ],
        "missing_items": [],
    }

    equipment_lookup = {
        "item:rope-50-feet": {"id": "item:rope-50-feet", "name": "Rope (50 feet)"},
        "item:torch": {"id": "item:torch", "name": "Torch"},
    }

    result = validate_pack_contents(pack, equipment_lookup)

    assert result["found_count"] == 2
    assert result["missing_count"] == 0
    assert result["missing_items"] == []


def test_validate_pack_contents_some_missing():
    """Missing pack items should be detected."""
    pack = {
        "name": "Test Pack",
        "contents": [
            {"item_id": "item:rope-50-feet", "item_name": "Rope (50 feet)", "quantity": 1},
            {"item_id": "item:invalid", "item_name": "Invalid Item", "quantity": 1},
        ],
        "missing_items": [],
    }

    equipment_lookup = {
        "item:rope-50-feet": {"id": "item:rope-50-feet", "name": "Rope (50 feet)"},
    }

    result = validate_pack_contents(pack, equipment_lookup)

    assert result["found_count"] == 1
    assert result["missing_count"] == 1
    assert "Invalid Item" in result["missing_items"]


def test_validate_pack_contents_with_pre_identified_missing():
    """Pre-identified missing items should be included in results."""
    pack = {
        "name": "Test Pack",
        "contents": [
            {"item_id": "item:rope-50-feet", "item_name": "Rope (50 feet)", "quantity": 1},
        ],
        "missing_items": ["Special Item Not In SRD"],
    }

    equipment_lookup = {
        "item:rope-50-feet": {"id": "item:rope-50-feet", "name": "Rope (50 feet)"},
    }

    result = validate_pack_contents(pack, equipment_lookup)

    assert result["found_count"] == 1
    assert result["missing_count"] == 1
    assert "Special Item Not In SRD" in result["missing_items"]


def test_validate_pack_contents_empty_pack():
    """Empty pack should have zero counts."""
    pack = {
        "name": "Empty Pack",
        "contents": [],
        "missing_items": [],
    }

    equipment_lookup = {}

    result = validate_pack_contents(pack, equipment_lookup)

    assert result["found_count"] == 0
    assert result["missing_count"] == 0
    assert result["missing_items"] == []


@pytest.mark.skipif(
    not (Path("dist/srd_5_1/equipment.json").exists()),
    reason="equipment.json not built yet",
)
def test_all_real_packs_have_valid_contents():
    """Integration test: all equipment packs should have valid contents."""
    # Load built equipment data
    equipment_path = Path("dist/srd_5_1/equipment.json")
    with open(equipment_path) as f:
        equipment = json.load(f)

    items_by_id = {item["id"]: item for item in equipment["items"]}

    # Validate each pack
    for pack in EQUIPMENT_PACKS:
        validation = validate_pack_contents(pack, items_by_id)

        # All items should be found (no missing items)
        assert validation["missing_count"] == 0, (
            f"{pack['name']} has {validation['missing_count']} missing items: "
            f"{validation['missing_items']}"
        )

        # Pack should have some contents
        assert validation["found_count"] > 0, f"{pack['name']} has no contents"
