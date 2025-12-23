from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_weapon_properties import parse_weapon_properties
from srd_builder.postprocess import clean_weapon_property_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_weapon_properties_dataset_golden() -> None:
    """Verify weapon_properties dataset matches expected output.

    Unlike other datasets, weapon_properties is static data (no raw fixture needed).
    This golden test verifies the 11 weapon properties are generated correctly.
    """
    expected_path = Path("tests/fixtures/srd_5_1/normalized/weapon_properties.json")

    parsed = parse_weapon_properties()
    processed = [clean_weapon_property_record(wp) for wp in parsed]

    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("weapon_property")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected


def test_weapon_properties_count() -> None:
    """Verify we have exactly 11 D&D 5e weapon properties."""
    parsed = parse_weapon_properties()
    assert len(parsed) == 11


def test_weapon_properties_canonical_list() -> None:
    """Verify all 11 weapon properties are present."""
    expected_properties = {
        "ammunition",
        "finesse",
        "heavy",
        "light",
        "loading",
        "range",
        "reach",
        "special",
        "thrown",
        "two_handed",
        "versatile",
    }

    parsed = parse_weapon_properties()
    actual_properties = {wp["simple_name"] for wp in parsed}

    assert actual_properties == expected_properties


def test_weapon_properties_have_required_fields() -> None:
    """Verify all weapon properties have required schema fields."""
    parsed = parse_weapon_properties()

    for prop in parsed:
        assert "id" in prop
        assert "simple_name" in prop
        assert "name" in prop
        assert "description" in prop
        assert "page" in prop
        assert "source" in prop

        # Verify ID format
        assert prop["id"].startswith("weapon_property:")

        # Verify page number (all from SRD page 147)
        assert prop["page"] == 147

        # Verify source
        assert prop["source"] == "SRD_CC_v5.1"

        # Verify description is non-empty array
        assert isinstance(prop["description"], list)
        assert len(prop["description"]) > 0
