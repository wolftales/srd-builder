"""Golden test for magic items dataset.

Validates known magic items have correct structure and content.
"""

import json
from pathlib import Path

import jsonschema
import pytest

# Paths
SCHEMA_PATH = Path("schemas/magic_item.schema.json")
DATASET_PATH = Path("dist/srd_5_1/magic_items.json")
FIXTURES_PATH = Path("tests/fixtures/magic_items/normalized/sample_items.json")


@pytest.fixture
def schema():
    """Load magic item schema."""
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def dataset():
    """Load full magic items dataset."""
    data = json.loads(DATASET_PATH.read_text())
    # Support both 'items' and 'magic_items' keys for backward compatibility
    items_key = "items" if "items" in data else "magic_items"
    # Normalize to 'magic_items' for tests
    if items_key == "items":
        data["magic_items"] = data.pop("items")
    return data


@pytest.fixture
def sample_items():
    """Load sample test fixtures."""
    return json.loads(FIXTURES_PATH.read_text())


def test_dataset_structure(dataset):
    """Test overall dataset structure."""
    assert "magic_items" in dataset
    assert "_meta" in dataset
    assert isinstance(dataset["magic_items"], list)
    assert len(dataset["magic_items"]) > 0


def test_dataset_count(dataset):
    """Test dataset has expected number of items."""
    # SRD 5.1 magic items on pages 206-253 = 240 items
    # (19 monster traits from pages 257-259 excluded)
    # (5 sentient item rule headers from page 251 excluded)
    assert len(dataset["magic_items"]) == 240


def test_all_items_valid_schema(dataset, schema):
    """Test all items validate against schema."""
    errors = []
    for item in dataset["magic_items"]:
        try:
            jsonschema.validate(item, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{item.get('name', 'UNKNOWN')}: {e.message}")

    assert not errors, f"Found {len(errors)} validation errors:\n" + "\n".join(errors[:10])


def test_adamantine_armor(sample_items):
    """Test Adamantine Armor has correct properties."""
    item = next(i for i in sample_items if i["name"] == "Adamantine Armor")

    assert item["id"] == "magic_item:adamantine_armor"
    assert item["simple_name"] == "adamantine_armor"
    assert item["type"] == "Armor"
    assert item["rarity"] == "uncommon"
    assert item["requires_attunement"] is False
    assert item["page"] >= 206
    assert item["source"] == "SRD_CC_v5.1"
    assert len(item["description"]) >= 1
    assert "adamantine" in item["description"][0].lower()


def test_ammunition_variants(sample_items):
    """Test Ammunition with variant notation."""
    item = next(i for i in sample_items if "Ammunition" in i["name"])

    assert item["id"] == "magic_item:ammunition_1_2_or_3"
    assert item["type"] == "Weapon"
    assert item["rarity"] in ["uncommon", "rare", "very rare"]  # Varies by +1/+2/+3
    assert item["requires_attunement"] is False
    assert "page" in item
    assert "source" in item


def test_amulet_of_health_attunement(sample_items):
    """Test Amulet of Health requires attunement."""
    item = next(i for i in sample_items if i["name"] == "Amulet of Health")

    assert item["id"] == "magic_item:amulet_of_health"
    assert item["type"] == "Wondrous item"
    assert item["rarity"] == "rare"
    assert item["requires_attunement"] is True
    assert "attunement_requirements" not in item  # No specific requirements
    assert "page" in item
    assert "source" in item


def test_bag_of_holding(sample_items):
    """Test Bag of Holding classic wondrous item."""
    item = next(i for i in sample_items if i["name"] == "Bag of Holding")

    assert item["id"] == "magic_item:bag_of_holding"
    assert item["simple_name"] == "bag_of_holding"
    assert item["type"] == "Wondrous item"
    assert item["rarity"] == "uncommon"
    assert item["requires_attunement"] is False
    assert len(item["description"]) >= 1


def test_flame_tongue_weapon(sample_items):
    """Test Flame Tongue weapon with attunement."""
    item = next(i for i in sample_items if i["name"] == "Flame Tongue")

    assert item["id"] == "magic_item:flame_tongue"
    assert item["type"] == "Weapon"
    assert item["rarity"] == "rare"
    assert item["requires_attunement"] is True
    assert "page" in item
    assert "source" in item


def test_unique_ids(dataset):
    """Test all item IDs are unique."""
    ids = [item["id"] for item in dataset["magic_items"]]
    assert len(ids) == len(set(ids)), "Duplicate IDs found"


def test_unique_names(dataset):
    """Test all item names are unique."""
    names = [item["name"] for item in dataset["magic_items"]]
    assert len(names) == len(set(names)), "Duplicate names found"


def test_all_items_have_descriptions(dataset):
    """Test every item has non-empty description."""
    for item in dataset["magic_items"]:
        assert len(item["description"]) > 0, f"{item['name']} has no description"
        assert item["description"][0].strip(), f"{item['name']} has empty description"


def test_valid_rarities(dataset):
    """Test all rarities are valid."""
    valid_rarities = {"common", "uncommon", "rare", "very rare", "legendary", "artifact", "varies"}

    for item in dataset["magic_items"]:
        assert item["rarity"] in valid_rarities, (
            f"{item['name']} has invalid rarity: {item['rarity']}"
        )


def test_valid_types(dataset):
    """Test all types are reasonable."""
    # Don't enforce specific list, just check it's not empty
    for item in dataset["magic_items"]:
        assert item["type"], f"{item['name']} has empty type"
        assert len(item["type"]) > 0


def test_simple_names_valid(dataset):
    """Test simple names follow pattern."""
    for item in dataset["magic_items"]:
        # Should be lowercase, underscores only
        assert item["simple_name"].islower(), f"{item['name']} simple_name not lowercase"
        assert item["simple_name"].strip() == item["simple_name"], (
            f"{item['name']} simple_name has extra whitespace"
        )
        # Should only contain a-z, 0-9, and underscores
        import re

        assert re.match(r"^[a-z0-9_]+$", item["simple_name"]), (
            f"{item['name']} simple_name has invalid characters: {item['simple_name']}"
        )


def test_all_items_have_page(dataset):
    """Test all items have page numbers."""
    for item in dataset["magic_items"]:
        assert "page" in item, f"{item['name']} missing page field"
        assert isinstance(item["page"], int), f"{item['name']} page is not an integer"
        assert item["page"] >= 206, (
            f"{item['name']} page {item['page']} is before magic items section"
        )
        assert item["page"] <= 253, (
            f"{item['name']} page {item['page']} is after magic items section"
        )


def test_all_items_have_source(dataset):
    """Test all items have source field."""
    for item in dataset["magic_items"]:
        assert "source" in item, f"{item['name']} missing source field"
        assert item["source"] == "SRD_CC_v5.1", (
            f"{item['name']} has unexpected source: {item['source']}"
        )


def test_ids_have_prefix(dataset):
    """Test all IDs have magic_item: prefix."""
    for item in dataset["magic_items"]:
        assert item["id"].startswith("magic_item:"), (
            f"{item['name']} ID doesn't have magic_item: prefix: {item['id']}"
        )
        # ID should be magic_item:simple_name
        expected_id = f"magic_item:{item['simple_name']}"
        assert item["id"] == expected_id, (
            f"{item['name']} ID mismatch: {item['id']} vs {expected_id}"
        )
