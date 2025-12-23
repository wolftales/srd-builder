from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_damage_types import parse_damage_types
from srd_builder.postprocess import clean_damage_type_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_damage_types_dataset_golden() -> None:
    """Verify damage_types dataset matches expected output.

    Unlike other datasets, damage_types is static data (no raw fixture needed).
    This golden test verifies the 13 canonical types are generated correctly.
    """
    expected_path = Path("tests/fixtures/srd_5_1/normalized/damage_types.json")

    parsed = parse_damage_types()
    processed = [clean_damage_type_record(dt) for dt in parsed]

    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("damage_type")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected


def test_damage_types_count() -> None:
    """Verify we have exactly 13 canonical D&D 5e damage types."""
    parsed = parse_damage_types()
    assert len(parsed) == 13


def test_damage_types_canonical_list() -> None:
    """Verify all 13 canonical damage types are present."""
    expected_types = {
        "acid",
        "bludgeoning",
        "cold",
        "fire",
        "force",
        "lightning",
        "necrotic",
        "piercing",
        "poison",
        "psychic",
        "radiant",
        "slashing",
        "thunder",
    }

    parsed = parse_damage_types()
    actual_types = {dt["simple_name"] for dt in parsed}

    assert actual_types == expected_types


def test_damage_types_have_required_fields() -> None:
    """Verify all damage types have required schema fields."""
    parsed = parse_damage_types()

    for dt in parsed:
        assert "id" in dt
        assert "simple_name" in dt
        assert "name" in dt
        assert "description" in dt
        assert "page" in dt
        assert "source" in dt

        # Verify ID format
        assert dt["id"].startswith("damage_type:")

        # Verify page number (all from SRD page 97)
        assert dt["page"] == 97

        # Verify source
        assert dt["source"] == "SRD_CC_v5.1"

        # Verify description is non-empty array
        assert isinstance(dt["description"], list)
        assert len(dt["description"]) > 0
