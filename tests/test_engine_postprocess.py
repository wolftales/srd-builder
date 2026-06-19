"""
Tests for configuration-driven postprocess engine.

Validates that engine + configs produce the same output as the previous
per-dataset functions for the 12 simple datasets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from srd_builder.postprocess.configs import DATASET_CONFIGS, RecordConfig
from srd_builder.postprocess.engine import clean_record, clean_records


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures" / "srd_5_1"


# ============================================================================
# Engine Core Tests
# ============================================================================


def test_clean_record_generates_simple_name():
    """Engine should generate simple_name from name field."""
    record = {"name": "Giant Rat"}
    config = RecordConfig(id_prefix="monster")

    result = clean_record(record, config)

    assert result["simple_name"] == "giant_rat"


def test_clean_record_generates_id():
    """Engine should generate id using prefix and simple_name."""
    record = {"name": "Giant Rat"}
    config = RecordConfig(id_prefix="monster")

    result = clean_record(record, config)

    assert result["id"] == "monster:giant_rat"


def test_clean_record_polishes_text_fields():
    """Engine should polish configured text fields."""
    record = {
        "name": "Test",
        "description": "  Multiple   spaces  ",
        "other_field": "  Not polished  ",
    }
    config = RecordConfig(
        id_prefix="test",
        text_fields=["description"],
    )

    result = clean_record(record, config)

    assert result["description"] == "Multiple spaces"
    assert result["other_field"] == "  Not polished  "  # Unchanged


def test_clean_record_polishes_text_arrays():
    """Engine should polish string arrays."""
    record = {
        "name": "Test",
        "effects": ["  Effect  one  ", "  Effect  two  "],
    }
    config = RecordConfig(
        id_prefix="test",
        text_arrays=["effects"],
    )

    result = clean_record(record, config)

    assert result["effects"] == ["Effect one", "Effect two"]


def test_clean_record_polishes_nested_structures():
    """Engine should polish nested dicts."""
    record = {
        "name": "Test",
        "traits": [
            {"name": "  Trait  One  ", "description": "  Desc  one  "},
            {"name": "  Trait  Two  ", "description": "  Desc  two  "},
        ],
    }
    config = RecordConfig(
        id_prefix="test",
        nested_structures={"traits": ["name", "description"]},
    )

    result = clean_record(record, config)

    assert result["traits"][0]["name"] == "Trait One"
    assert result["traits"][0]["description"] == "Desc one"


def test_clean_record_applies_custom_transform():
    """Engine should apply custom transformation if provided."""

    def custom(record: dict) -> dict:
        record["custom_field"] = "added"
        return record

    record = {"name": "Test"}
    config = RecordConfig(id_prefix="test", custom_transform=custom)

    result = clean_record(record, config)

    assert result["custom_field"] == "added"


# ============================================================================
# Dataset Idempotency Tests
#
# Running the engine over already-normalized fixtures should be a no-op.
# This proves the engine doesn't mangle clean data. End-to-end equivalence
# with the previous per-dataset cleaners is covered by tests/test_golden_*.
# ============================================================================


def _assert_engine_idempotent(fixtures_dir: Path, dataset_file: str, dataset_key: str) -> None:
    """Running the engine over already-normalized records must be a no-op."""
    normalized_path = fixtures_dir / "normalized" / dataset_file
    with open(normalized_path) as f:
        expected = json.load(f)

    # Most fixtures use "items"; a few use the dataset name as the key.
    items = next(v for k, v in expected.items() if k != "_meta")
    # Deep copy via JSON round-trip so the engine can't mutate the expected baseline.
    processed = [
        clean_record(json.loads(json.dumps(item)), DATASET_CONFIGS[dataset_key]) for item in items
    ]

    assert processed == items


def test_poison_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized poisons should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "poisons.json", "poison")


def test_disease_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized diseases should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "diseases.json", "disease")


def test_condition_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized conditions should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "conditions.json", "condition")


def test_feature_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized features should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "features.json", "feature")


def test_lineage_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized lineages should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "lineages.json", "lineage")


def test_table_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized tables should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "tables.json", "table")


def test_class_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized classes should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "classes.json", "class")


def test_ability_score_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized ability scores should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "ability_scores.json", "ability_score")


def test_damage_type_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized damage types should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "damage_types.json", "damage_type")


def test_skill_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized skills should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "skills.json", "skill")


def test_weapon_property_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized weapon properties should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "weapon_properties.json", "weapon_property")


def test_magic_item_engine_idempotent(fixtures_dir: Path):
    """Engine over normalized magic items should produce identical output."""
    _assert_engine_idempotent(fixtures_dir, "magic_items.json", "magic_item")


# ============================================================================
# Batch Processing Tests
# ============================================================================


def test_clean_records_batch_processing():
    """clean_records should process multiple records."""
    records = [
        {"name": "Poison One"},
        {"name": "Poison Two"},
    ]

    processed = clean_records(records, "poison")

    assert len(processed) == 2
    assert processed[0]["id"] == "poison:poison_one"
    assert processed[1]["id"] == "poison:poison_two"


def test_clean_records_unknown_dataset_raises():
    """clean_records should raise for unknown dataset."""
    with pytest.raises(ValueError, match="Unknown dataset: unknown"):
        clean_records([], "unknown")


# ============================================================================
# Config Validation Tests
# ============================================================================


@pytest.mark.parametrize(
    "dataset_name",
    [
        "poison",
        "disease",
        "condition",
        "feature",
        "lineage",
        "table",
        "class",
        "ability_score",
        "damage_type",
        "skill",
        "weapon_property",
        "magic_item",
    ],
)
def test_all_configs_have_required_fields(dataset_name: str):
    """All dataset configs should have valid structure."""
    config = DATASET_CONFIGS[dataset_name]

    assert isinstance(config.id_prefix, str)
    assert len(config.id_prefix) > 0
    assert isinstance(config.name_field, str)
    assert isinstance(config.text_fields, list)
    assert isinstance(config.text_arrays, list)
    assert isinstance(config.nested_structures, dict)
