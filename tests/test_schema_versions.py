"""Test schema version consistency across schema files and datasets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_schema_files_have_version():
    """All schema files should declare a version field."""
    schema_dir = Path(__file__).parent.parent / "schemas"
    schema_files = list(schema_dir.glob("*.schema.json"))

    assert len(schema_files) > 0, "No schema files found"

    for schema_file in schema_files:
        with open(schema_file) as f:
            schema = json.load(f)

        assert "version" in schema, f"{schema_file.name} missing 'version' field"
        assert isinstance(schema["version"], str), f"{schema_file.name} version must be string"
        assert schema["version"], f"{schema_file.name} version cannot be empty"

        # Version should be semantic versioning format (e.g., "1.1.0")
        parts = schema["version"].split(".")
        assert len(parts) == 3, f"{schema_file.name} version must be MAJOR.MINOR.PATCH format"
        assert all(p.isdigit() for p in parts), f"{schema_file.name} version parts must be numeric"


@pytest.mark.package
def test_dataset_schema_versions_match():
    """Dataset _meta.schema_version should match current schema version.

    Requires: Built package (run 'make output' first)
    """
    dist_dir = Path(__file__).parent.parent / "dist" / "srd_5_1"
    schema_dir = Path(__file__).parent.parent / "schemas"

    # Map dataset files to their schema files
    dataset_schema_map = {
        "monsters.json": "monster.schema.json",
        "equipment.json": "equipment.schema.json",
        "spells.json": "spell.schema.json",
    }

    for dataset_file, schema_file in dataset_schema_map.items():
        dataset_path = dist_dir / dataset_file
        schema_path = schema_dir / schema_file

        if not dataset_path.exists():
            pytest.skip(f"Dataset {dataset_file} not built - run 'make output' first")

        # Load dataset
        with open(dataset_path) as f:
            dataset = json.load(f)

        # Load schema
        with open(schema_path) as f:
            schema = json.load(f)

        # Check dataset has _meta.schema_version
        assert "_meta" in dataset, f"{dataset_file} missing _meta section"
        assert "schema_version" in dataset["_meta"], f"{dataset_file} _meta missing schema_version"

        # Check versions match
        dataset_version = dataset["_meta"]["schema_version"]
        schema_version = schema["version"]

        assert (
            dataset_version == schema_version
        ), f"{dataset_file} schema_version ({dataset_version}) doesn't match {schema_file} version ({schema_version})"


@pytest.mark.package
def test_meta_json_schema_version():
    """meta.json should declare schema versions for all datasets.

    The schemas section provides a manifest of schema versions for each dataset type,
    allowing independent evolution (e.g., monster schema can be 2.0.0 while spells stay 1.4.0).

    Requires: Built package (run 'make output' first)
    """
    # meta.json at package root (flat structure)
    meta_path = Path(__file__).parent.parent / "dist" / "srd_5_1" / "meta.json"

    if not meta_path.exists():
        pytest.skip("meta.json not built - run 'make output' first")

    with open(meta_path) as f:
        meta = json.load(f)

    # meta.json should have schemas section
    assert "schemas" in meta, "meta.json missing schemas section"
    schemas = meta["schemas"]

    # All dataset types should be listed
    expected_datasets = {
        "monster",
        "spell",
        "equipment",
        "class",
        "lineage",
        "table",
        "condition",
        "disease",
        "poison",
        "features",
        "madness",
        "magic_item",
    }
    assert (
        set(schemas.keys()) == expected_datasets
    ), f"schemas section missing datasets: {expected_datasets - set(schemas.keys())}"

    # Each schema version should be valid semver
    for dataset, version in schemas.items():
        assert isinstance(version, str), f"{dataset} schema version must be string"
        parts = version.split(".")
        assert len(parts) == 3, f"{dataset} schema version must be MAJOR.MINOR.PATCH format"
        assert all(p.isdigit() for p in parts), f"{dataset} schema version parts must be numeric"


def test_meta_json_schemas_match_datasets() -> None:
    """Cross-validate that meta.json schemas section matches individual dataset _meta.schema_version fields."""
    dist_path = Path(__file__).parent.parent / "dist" / "srd_5_1"

    # Skip if build hasn't been run yet
    if not dist_path.exists():
        pytest.skip("dist/srd_5_1 not found - run build first")

    meta_path = dist_path / "meta.json"
    with open(meta_path) as f:
        meta = json.load(f)

    schemas_section = meta.get("schemas", {})

    # Check each dataset file
    for dataset_name, expected_version in schemas_section.items():
        dataset_path = dist_path / f"{dataset_name}.json"

        # Skip if dataset file doesn't exist (e.g., madness might not be in SRD)
        if not dataset_path.exists():
            continue

        with open(dataset_path) as f:
            dataset = json.load(f)

        # Check _meta.schema_version matches meta.json schemas entry
        dataset_meta = dataset.get("_meta", {})
        actual_version = dataset_meta.get("schema_version")

        assert actual_version == expected_version, (
            f"{dataset_name}.json _meta.schema_version ({actual_version}) "
            f"doesn't match meta.json schemas.{dataset_name} ({expected_version})"
        )
