"""Test that all expected datasets are present and populated with expected counts.

This test catches issues like empty monsters.json or missing datasets that would
otherwise go unnoticed until a user reports it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DIST_DIR = Path("dist/srd_5_1")

# Expected minimum counts for each dataset
# These represent the known SRD 5.1 content
EXPECTED_COUNTS = {
    "monsters": 296,  # Full monster list from MM Appendix
    "spells": 319,  # All SRD spells
    "equipment": 200,  # ~200+ equipment items (weapons, armor, gear, packs, etc.)
    "tables": 38,  # Reference tables throughout the document
    "lineages": 9,  # Player character lineages (races)
    "classes": 12,  # Player character classes
    "conditions": 15,  # Standard game conditions
    "diseases": 3,  # Cackle Fever, Sewer Plague, Sight Rot
    "poisons": 14,  # Poison items from table
    "features": 246,  # Class features + lineage traits
}


@pytest.mark.parametrize("dataset_name,expected_min", EXPECTED_COUNTS.items())
def test_dataset_populated(dataset_name: str, expected_min: int) -> None:
    """Test that each dataset exists and has at least the expected number of items."""
    dataset_path = DIST_DIR / f"{dataset_name}.json"

    if not dataset_path.exists():
        pytest.skip(f"{dataset_name}.json not found - build may not have run")

    document = json.loads(dataset_path.read_text(encoding="utf-8"))

    # Determine the key that holds the items
    # Most use "items", but conditions/diseases/features use their own keys
    if dataset_name == "conditions":
        items_key = "conditions"
    elif dataset_name == "diseases":
        items_key = "diseases"
    elif dataset_name == "features":
        items_key = "features"
    else:
        items_key = "items"

    items = document.get(items_key, [])

    assert isinstance(items, list), f"{dataset_name}.json {items_key} should be a list"
    assert len(items) > 0, f"{dataset_name}.json should not be empty"
    assert len(items) >= expected_min, (
        f"{dataset_name}.json has {len(items)} items, " f"expected at least {expected_min}"
    )


def test_all_datasets_have_standard_meta_fields() -> None:
    """Test that all datasets have the standard _meta fields in correct order."""
    standard_fields = [
        "source",
        "ruleset_version",
        "schema_version",
        "generated_by",
        "build_report",
    ]

    for dataset_name in EXPECTED_COUNTS.keys():
        dataset_path = DIST_DIR / f"{dataset_name}.json"

        if not dataset_path.exists():
            continue  # Skip if not built yet

        document = json.loads(dataset_path.read_text(encoding="utf-8"))
        meta = document.get("_meta", {})

        # Check all standard fields are present
        for field in standard_fields:
            assert field in meta, f"{dataset_name}.json missing standard _meta field: {field}"

        # Check field order (Python 3.7+ dicts maintain insertion order)
        meta_keys = list(meta.keys())
        for i, expected_field in enumerate(standard_fields):
            assert meta_keys[i] == expected_field, (
                f"{dataset_name}.json _meta field order incorrect. "
                f"Expected {expected_field} at position {i}, got {meta_keys[i]}"
            )


def test_all_datasets_have_consistent_versions() -> None:
    """Test that all datasets use the same schema version and builder version."""
    versions = {}

    for dataset_name in EXPECTED_COUNTS.keys():
        dataset_path = DIST_DIR / f"{dataset_name}.json"

        if not dataset_path.exists():
            continue

        document = json.loads(dataset_path.read_text(encoding="utf-8"))
        meta = document.get("_meta", {})

        schema_version = meta.get("schema_version")
        generated_by = meta.get("generated_by")

        if not versions:
            versions["schema_version"] = schema_version
            versions["generated_by"] = generated_by
        else:
            assert schema_version == versions["schema_version"], (
                f"{dataset_name}.json has schema_version {schema_version}, "
                f"but other datasets use {versions['schema_version']}"
            )
            assert generated_by == versions["generated_by"], (
                f"{dataset_name}.json has generated_by {generated_by}, "
                f"but other datasets use {versions['generated_by']}"
            )


def test_meta_json_extraction_status() -> None:
    """Test that meta.json marks all datasets as complete."""
    meta_path = DIST_DIR / "meta.json"

    if not meta_path.exists():
        pytest.skip("meta.json not found - build may not have run")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    extraction_status = meta.get("extraction_status", {})

    for dataset_name in EXPECTED_COUNTS.keys():
        status = extraction_status.get(dataset_name)
        assert (
            status == "complete"
        ), f"meta.json shows {dataset_name} status as '{status}', expected 'complete'"
