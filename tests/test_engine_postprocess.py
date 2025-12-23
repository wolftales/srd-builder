"""
Tests for configuration-driven postprocess engine.

Validates that engine + configs produce same output as existing
per-dataset functions for poisons, diseases, conditions.
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
# Dataset Config Tests (Golden Tests)
# ============================================================================


def test_poison_config_matches_existing_output(fixtures_dir: Path):
    """Poison engine output should match existing clean_poison_record."""
    # Load raw fixture
    raw_path = fixtures_dir / "raw" / "poisons.json"
    with open(raw_path) as f:
        raw_data = json.load(f)

    # Load expected normalized fixture
    normalized_path = fixtures_dir / "normalized" / "poisons.json"
    with open(normalized_path) as f:
        expected = json.load(f)

    # Process with engine
    processed = [clean_record(p, DATASET_CONFIGS["poison"]) for p in raw_data]

    # Compare (extract items array from expected)
    assert processed == expected["items"]


def test_disease_config_matches_existing_output(fixtures_dir: Path):
    """Disease engine output should match existing clean_disease_record."""
    raw_path = fixtures_dir / "raw" / "diseases.json"
    with open(raw_path) as f:
        raw_data = json.load(f)

    normalized_path = fixtures_dir / "normalized" / "diseases.json"
    with open(normalized_path) as f:
        expected = json.load(f)

    processed = [clean_record(d, DATASET_CONFIGS["disease"]) for d in raw_data]

    assert processed == expected["items"]


def test_condition_config_matches_existing_output(fixtures_dir: Path):
    """Condition engine output should match existing clean_condition_record."""
    raw_path = fixtures_dir / "raw" / "conditions.json"
    with open(raw_path) as f:
        raw_data = json.load(f)

    normalized_path = fixtures_dir / "normalized" / "conditions.json"
    with open(normalized_path) as f:
        expected = json.load(f)

    processed = [clean_record(c, DATASET_CONFIGS["condition"]) for c in raw_data]

    assert processed == expected["items"]


def test_feature_config_matches_existing_output(fixtures_dir: Path):
    """Feature engine output should match existing clean_feature_record."""
    raw_path = fixtures_dir / "raw" / "features.json"
    with open(raw_path) as f:
        raw_data = json.load(f)

    normalized_path = fixtures_dir / "normalized" / "features.json"
    with open(normalized_path) as f:
        expected = json.load(f)

    processed = [clean_record(f, DATASET_CONFIGS["feature"]) for f in raw_data]

    assert processed == expected["items"]


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
