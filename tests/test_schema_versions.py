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


def test_dataset_schema_versions_match():
    """Dataset _meta.schema_version should match current schema version."""
    dist_dir = Path(__file__).parent.parent / "dist" / "srd_5_1" / "data"
    schema_dir = Path(__file__).parent.parent / "schemas"

    # Map dataset files to their schema files
    dataset_schema_map = {
        "monsters.json": "monster.schema.json",
        "equipment.json": "equipment.schema.json",
    }

    for dataset_file, schema_file in dataset_schema_map.items():
        dataset_path = dist_dir / dataset_file
        schema_path = schema_dir / schema_file

        if not dataset_path.exists():
            pytest.skip(f"Dataset {dataset_file} not built yet")

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


def test_meta_json_schema_version():
    """meta.json should declare the schema version."""
    meta_path = Path(__file__).parent.parent / "dist" / "srd_5_1" / "meta.json"

    if not meta_path.exists():
        pytest.skip("meta.json not built yet")

    with open(meta_path) as f:
        meta = json.load(f)

    assert "$schema_version" in meta, "meta.json missing $schema_version field"
    assert isinstance(meta["$schema_version"], str), "$schema_version must be string"

    # Should be semantic versioning format
    version = meta["$schema_version"]
    parts = version.split(".")
    assert len(parts) == 3, "$schema_version must be MAJOR.MINOR.PATCH format"
    assert all(p.isdigit() for p in parts), "$schema_version parts must be numeric"


def test_schema_version_consistency():
    """All schemas with the same major version should have the same version number."""
    schema_dir = Path(__file__).parent.parent / "schemas"
    schema_files = list(schema_dir.glob("*.schema.json"))

    versions = {}
    for schema_file in schema_files:
        with open(schema_file) as f:
            schema = json.load(f)

        if "version" in schema:
            version = schema["version"]
            versions[schema_file.name] = version

    # All schemas should be on version 1.2.0 currently
    # (This test will need updating when we have different versions)
    current_version = "1.2.0"
    for schema_file, version in versions.items():
        assert (
            version == current_version
        ), f"{schema_file} has version {version}, expected {current_version}"
