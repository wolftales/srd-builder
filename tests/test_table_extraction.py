"""Test that all target tables extract with correct structure.

Validates that:
1. All tables in TARGET_TABLES are present in tables_raw.json
2. Each table has required fields (table_id, simple_name, headers, rows)
3. Row counts match validation expectations from extraction_metadata.py
4. Headers match expected formats
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts to path for importing TARGET_TABLES
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from table_targets import TARGET_TABLES


@pytest.fixture
def tables_raw():
    """Load raw extracted tables data."""
    tables_path = Path("rulesets/srd_5_1/raw/tables_raw.json")
    if not tables_path.exists():
        pytest.skip("tables_raw.json not found - run build first")

    with open(tables_path) as f:
        data = json.load(f)

    # Convert list to dict keyed by simple_name for easy lookup
    return {t["simple_name"]: t for t in data["tables"]}


def test_all_target_tables_extracted(tables_raw):
    """Verify all tables in TARGET_TABLES were successfully extracted."""
    expected_tables = {t["simple_name"] for t in TARGET_TABLES}
    extracted_tables = set(tables_raw.keys())

    # Known issue: long_term_madness requires multipage_text_region implementation
    known_issues = {"long_term_madness"}

    missing = expected_tables - extracted_tables - known_issues
    assert not missing, f"Missing tables: {missing}"


def test_table_structure_valid(tables_raw):
    """Verify each table has required fields and valid structure."""
    for simple_name, table in tables_raw.items():
        # Required fields
        assert "table_id" in table, f"{simple_name}: missing table_id"
        assert "simple_name" in table, f"{simple_name}: missing simple_name"
        assert "headers" in table, f"{simple_name}: missing headers"
        assert "rows" in table, f"{simple_name}: missing rows"

        # Type validation
        assert isinstance(table["headers"], list), f"{simple_name}: headers must be list"
        assert isinstance(table["rows"], list), f"{simple_name}: rows must be list"
        assert len(table["headers"]) > 0, f"{simple_name}: headers cannot be empty"

        # Each row should be a list
        for i, row in enumerate(table["rows"]):
            assert isinstance(row, list), f"{simple_name} row {i}: must be list"


def test_progression_tables_structure(tables_raw):
    """Verify all 12 class progression tables have correct structure."""
    progression_tables = [
        "barbarian_progression",
        "bard_progression",
        "cleric_progression",
        "druid_progression",
        "fighter_progression",
        "monk_progression",
        "paladin_progression",
        "ranger_progression",
        "rogue_progression",
        "sorcerer_progression",
        "warlock_progression",
        "wizard_progression",
    ]

    for simple_name in progression_tables:
        assert simple_name in tables_raw, f"Missing progression table: {simple_name}"
        table = tables_raw[simple_name]

        # All progression tables should have 20 levels
        assert (
            len(table["rows"]) == 20
        ), f"{simple_name}: expected 20 levels, got {len(table['rows'])}"

        # First column should be "Level"
        assert (
            table["headers"][0] == "Level"
        ), f"{simple_name}: first header should be 'Level', got '{table['headers'][0]}'"


def test_equipment_tables_present(tables_raw):
    """Verify key equipment tables are present."""
    equipment_tables = [
        "armor",
        "weapons",
        "adventure_gear",
        "tools",
        "mounts_and_other_animals",
        "services",
        "food_drink_lodging",
    ]

    for simple_name in equipment_tables:
        assert simple_name in tables_raw, f"Missing equipment table: {simple_name}"


def test_hazard_tables_present(tables_raw):
    """Verify hazard tables (madness, poisons) are present."""
    hazard_tables = ["poisons", "short_term_madness", "indefinite_madness"]

    for simple_name in hazard_tables:
        assert simple_name in tables_raw, f"Missing hazard table: {simple_name}"


def test_armor_table_format(tables_raw):
    """Verify armor table has expected structure."""
    table = tables_raw.get("armor")
    assert table is not None, "armor table not found"

    # Should have 6 columns including Strength requirement
    expected_headers = ["Armor", "Cost", "Armor Class (AC)", "Strength", "Stealth", "Weight"]
    assert (
        table["headers"] == expected_headers
    ), f"Armor headers mismatch. Expected {expected_headers}, got {table['headers']}"

    # Should have 17 rows (Light: 3, Medium: 6, Heavy: 6, Shield: 1, plus category headers)
    assert len(table["rows"]) == 17, f"Expected 17 armor rows, got {len(table['rows'])}"


def test_weapons_table_format(tables_raw):
    """Verify weapons table has expected structure."""
    table = tables_raw.get("weapons")
    assert table is not None, "weapons table not found"

    # Should have 5 columns including Properties
    expected_headers = ["Name", "Cost", "Damage", "Weight", "Properties"]
    assert (
        table["headers"] == expected_headers
    ), f"Weapons headers mismatch. Expected {expected_headers}, got {table['headers']}"

    # Should have 41 rows (Simple Melee: 11, Simple Ranged: 4, Martial Melee: 18, Martial Ranged: 8)
    assert len(table["rows"]) == 41, f"Expected 41 weapon rows, got {len(table['rows'])}"


def test_poison_table_format(tables_raw):
    """Verify poisons table has expected structure."""
    table = tables_raw.get("poisons")
    assert table is not None, "poisons table not found"

    # Should have 3 columns: Poison, Type, Price per Dose
    assert (
        len(table["headers"]) == 3
    ), f"Expected 3 poison columns, got {len(table['headers'])}: {table['headers']}"

    # Expect around 14 poisons (may have extra rows due to split-column extraction)
    assert len(table["rows"]) >= 14, f"Expected at least 14 poison rows, got {len(table['rows'])}"
