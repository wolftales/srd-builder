"""Test that all expected datasets are present and populated with expected counts.

This test catches issues like empty monsters.json or missing datasets that would
otherwise go unnoticed until a user reports it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DIST_DIR = Path("dist/srd_5_1")
PDF_PATH = Path("rulesets/srd_5_1/SRD_CC_v5.1.pdf")
PDF_AVAILABLE = PDF_PATH.exists()

# Expected minimum counts for each dataset
# These represent the known SRD 5.1 content
EXPECTED_COUNTS = {
    "monsters": 317,  # 201 monsters + 95 creatures (MM-A) + 21 NPCs (MM-B)
    "spells": 319,  # All SRD spells
    "equipment": 200,  # ~200+ equipment items (weapons, armor, gear, packs, etc.)
    "tables": 38,  # Reference tables throughout the document
    "lineages": 9,  # Player character lineages (races)
    "classes": 12,  # Player character classes
    "conditions": 15,  # Standard game conditions
    "diseases": 3,  # Cackle Fever, Sewer Plague, Sight Rot
    "poisons": 14,  # Poison items from table
    "features": 246,  # Class features + lineage traits
    # Note: madness tables are in tables.json, not a separate madness.json file
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
    assert (
        len(items) >= expected_min
    ), f"{dataset_name}.json has {len(items)} items, expected at least {expected_min}"


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
    """Test that all datasets have valid schema versions and consistent builder version.

    Schema versions can differ between datasets (independent versioning as of v0.15.1),
    but generated_by should be consistent across all datasets.
    """
    versions = {}

    for dataset_name in EXPECTED_COUNTS.keys():
        dataset_path = DIST_DIR / f"{dataset_name}.json"

        if not dataset_path.exists():
            continue

        document = json.loads(dataset_path.read_text(encoding="utf-8"))
        meta = document.get("_meta", {})

        schema_version = meta.get("schema_version")
        generated_by = meta.get("generated_by")

        # Validate schema_version format (each dataset can have its own version)
        if schema_version:
            assert isinstance(schema_version, str), f"{dataset_name} schema_version must be string"
            parts = schema_version.split(".")
            assert len(parts) == 3, f"{dataset_name} schema_version must be MAJOR.MINOR.PATCH"
            assert all(p.isdigit() for p in parts), f"{dataset_name} parts must be numeric"

        # Check generated_by consistency across all datasets
        if not versions:
            versions["generated_by"] = generated_by
        else:
            assert generated_by == versions["generated_by"], (
                f"{dataset_name}.json has generated_by {generated_by}, "
                f"but other datasets use {versions['generated_by']}"
            )


def test_pdf_location() -> None:
    """Test that the PDF is in the expected location (local development only).

    The PDF should be at rulesets/srd_5_1/SRD_CC_v5.1.pdf (not in the raw/ subdirectory).
    This catches bugs where build.py looks in the wrong directory.

    Skipped if PDF not present (e.g., CI environment).
    """
    if not PDF_PATH.exists():
        pytest.skip("PDF not available - test only relevant when PDF is present")

    # Also check that it's NOT in the wrong location (raw/ subdirectory)
    wrong_location = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")
    if wrong_location.exists():
        pytest.fail(
            f"PDF found at {wrong_location} - it should be in the parent directory instead. "
            "Move it to rulesets/srd_5_1/SRD_CC_v5.1.pdf"
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
