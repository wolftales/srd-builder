"""Test the 7 tables migrated in v0.9.9 to ensure they extract correctly.

These tables were migrated from legacy text_table_parser.py functions to
modern pattern-based extraction. Tests verify:
1. Correct row counts (matching validation expectations)
2. Category detection working properly
3. Data structure integrity
4. No regressions from legacy parser
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tables_data():
    """Load extracted tables data."""
    tables_path = Path("rulesets/srd_5_1/raw/tables_raw.json")
    if not tables_path.exists():
        pytest.skip("tables_raw.json not found - run 'make tables' first")

    with open(tables_path) as f:
        data = json.load(f)

    # Convert list to dict keyed by table_id
    return {t["table_id"]: t for t in data["tables"]}


# ============================================================================
# TEST: tools (migrated 2025-11-08)
# ============================================================================


def test_tools_table_extraction(tables_data):
    """Test tools table: 38 rows, 3 categories."""
    table = tables_data.get("table:tools")
    assert table is not None, "tools table not found"

    assert len(table["rows"]) == 38, f"Expected 38 rows, got {len(table['rows'])}"
    assert table["headers"] == ["Item", "Cost", "Weight"]

    # Check categories exist (should have empty cost/weight)
    categories = [row for row in table["rows"] if row[1] == "" and row[0] != ""]
    assert len(categories) >= 3, f"Expected at least 3 categories, found {len(categories)}"

    # Sample items (use list comprehension to avoid apostrophe issues)
    item_names = [row[0] for row in table["rows"]]
    assert any("Alchemist" in name for name in item_names), "Missing Alchemist's supplies"
    assert any("Smith" in name for name in item_names), "Missing Smith's tools"
    assert any("Dice set" in name for name in item_names), "Missing Dice set"


# ============================================================================
# TEST: services (migrated 2025-11-08)
# ============================================================================


def test_services_table_extraction(tables_data):
    """Test services table: 9 rows, 2 categories."""
    table = tables_data.get("table:services")
    assert table is not None, "services table not found"

    assert len(table["rows"]) == 9, f"Expected 9 rows, got {len(table['rows'])}"
    assert table["headers"] == ["Service", "Cost"]

    # Check categories
    categories = [row for row in table["rows"] if row[1] == "" and row[0] != ""]
    assert len(categories) >= 2, f"Expected at least 2 categories, found {len(categories)}"

    # Sample items
    items = {row[0]: row for row in table["rows"]}
    assert "Coach cab" in items or "Coach cab:" in items  # Allow colon variation
    assert "Hireling" in items or "Hireling:" in items


# ============================================================================
# TEST: food_drink_lodging (migrated 2025-11-08)
# ============================================================================


def test_food_drink_lodging_table_extraction(tables_data):
    """Test food_drink_lodging table: 21 rows, 4 categories, multi-region."""
    table = tables_data.get("table:food_drink_lodging")
    assert table is not None, "food_drink_lodging table not found"

    assert len(table["rows"]) == 21, f"Expected 21 rows, got {len(table['rows'])}"
    assert table["headers"] == ["Item", "Cost"]

    # Check categories (Inn stay, Meals, Drinks, etc.)
    categories = [row for row in table["rows"] if row[1] == "" and row[0] != ""]
    assert len(categories) >= 4, f"Expected at least 4 categories, found {len(categories)}"

    # Sample items
    item_names = [row[0].lower() for row in table["rows"]]
    assert any("squalid" in name for name in item_names), "Missing 'Squalid'"
    assert any("aristocratic" in name for name in item_names), "Missing 'Aristocratic'"
    assert any("ale" in name for name in item_names), "Missing 'Ale'"
    assert any("wine" in name for name in item_names), "Missing 'Wine'"


# ============================================================================
# TEST: tack_harness_vehicles (migrated 2025-11-08)
# ============================================================================


def test_tack_harness_vehicles_table_extraction(tables_data):
    """Test tack_harness_vehicles table: 14 rows."""
    table = tables_data.get("table:tack_harness_vehicles")
    assert table is not None, "tack_harness_vehicles table not found"

    assert len(table["rows"]) == 14, f"Expected 14 rows, got {len(table['rows'])}"
    assert table["headers"] == ["Item", "Cost", "Weight"]

    # Sample items
    items = {row[0]: row for row in table["rows"]}
    assert "Saddle, Riding" in items or "Saddle" in items
    assert "Wagon" in items or "Carriage" in items


# ============================================================================
# TEST: armor (migrated 2025-11-08)
# ============================================================================


def test_armor_table_extraction(tables_data):
    """Test armor table: 17 rows, 4 categories, multi-region (pages 63-64)."""
    table = tables_data.get("table:armor")
    assert table is not None, "armor table not found"

    assert len(table["rows"]) == 17, f"Expected 17 rows, got {len(table['rows'])}"
    assert table["headers"] == [
        "Armor",
        "Cost",
        "Armor Class (AC)",
        "Strength",
        "Stealth",
        "Weight",
    ]

    # Check categories (Light Armor, Medium Armor, Heavy Armor, Shield)
    categories = [row for row in table["rows"] if row[1] == "" and row[0] != ""]
    assert len(categories) >= 3, f"Expected at least 3 categories, found {len(categories)}"

    # Sample items
    items = {row[0]: row for row in table["rows"]}
    assert "Padded" in items
    assert "Chain mail" in items or "Chain Mail" in items
    assert "Shield" in items


# ============================================================================
# TEST: weapons (migrated 2025-11-08)
# ============================================================================


def test_weapons_table_extraction(tables_data):
    """Test weapons table: 41 rows, 4 categories, multi-region (pages 65-66)."""
    table = tables_data.get("table:weapons")
    assert table is not None, "weapons table not found"

    assert len(table["rows"]) == 41, f"Expected 41 rows, got {len(table['rows'])}"
    assert table["headers"] == ["Name", "Cost", "Damage", "Weight", "Properties"]

    # Check categories (Simple Melee, Simple Ranged, Martial Melee, Martial Ranged)
    categories = [row for row in table["rows"] if row[1] == "" and row[0] != ""]
    assert len(categories) >= 4, f"Expected at least 4 categories, found {len(categories)}"

    # Sample items
    items = {row[0]: row for row in table["rows"]}
    assert "Dagger" in items
    assert "Longbow" in items
    assert "Longsword" in items
    assert "Greatsword" in items


# ============================================================================
# TEST: adventure_gear (migrated 2025-11-08, fixed for two columns)
# ============================================================================


def test_adventure_gear_table_extraction(tables_data):
    """Test adventure_gear table: 103 rows, 4 categories, TWO-COLUMN layout.

    This table has a challenging two-column layout:
    - LEFT column: Abacus through Holy water (A-G)
    - RIGHT column: Hourglass through Whetstone (H-W)
    """
    table = tables_data.get("table:adventure_gear")
    assert table is not None, "adventure_gear table not found"

    assert len(table["rows"]) == 103, f"Expected 103 rows, got {len(table['rows'])}"
    assert table["headers"] == ["Item", "Cost", "Weight"]

    # Check categories
    categories = [row for row in table["rows"] if row[1] == "" and row[0] != ""]
    assert len(categories) >= 4, f"Expected at least 4 categories, found {len(categories)}"

    # Sample items from LEFT column (A-G)
    items = {row[0]: row for row in table["rows"]}
    assert "Abacus" in items, "Missing 'Abacus' from left column"
    assert "Acid (vial)" in items, "Missing 'Acid (vial)' from left column"
    assert "Holy water (flask)" in items, "Missing 'Holy water (flask)' from left column"

    # Sample items from RIGHT column (H-W) - THIS IS THE CRITICAL TEST
    assert "Hourglass" in items, "Missing 'Hourglass' from right column (first item)"
    assert "Hunting trap" in items, "Missing 'Hunting trap' from right column"
    assert "Ink (1 ounce bottle)" in items, "Missing 'Ink' from right column"
    assert "Lamp" in items, "Missing 'Lamp' from right column"
    assert "Torch" in items, "Missing 'Torch' from right column"
    assert "Waterskin" in items, "Missing 'Waterskin' from right column"
    assert "Whetstone" in items, "Missing 'Whetstone' from right column (last item)"

    # Verify expensive items have correct costs (not merged into item name)
    assert items["Hourglass"][1] == "25 gp", f"Hourglass cost wrong: {items['Hourglass'][1]}"
    spyglass = items.get("Spyglass")
    assert spyglass is not None, "Missing 'Spyglass'"
    assert spyglass[1] == "1,000 gp", f"Spyglass cost wrong: {spyglass[1]}"


# ============================================================================
# INTEGRATION TEST: All 7 tables extracted successfully
# ============================================================================


def test_all_migrated_tables_present(tables_data):
    """Verify all 7 newly migrated tables are present and valid."""
    migrated_tables = [
        "table:tools",
        "table:services",
        "table:food_drink_lodging",
        "table:tack_harness_vehicles",
        "table:armor",
        "table:weapons",
        "table:adventure_gear",
    ]

    for table_id in migrated_tables:
        assert table_id in tables_data, f"Missing table: {table_id}"
        table = tables_data[table_id]
        assert len(table["rows"]) > 0, f"Table {table_id} has no rows"
        assert len(table["headers"]) > 0, f"Table {table_id} has no headers"
        assert table["extraction_method"] in [
            "text_parsed",
            "text_region",
        ], f"Table {table_id} using wrong extraction method: {table['extraction_method']}"
