from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_ability_scores import parse_ability_scores
from srd_builder.postprocess import clean_ability_score_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_ability_scores_dataset_golden() -> None:
    """Verify ability_scores dataset matches expected output.

    Unlike other datasets, ability_scores is static data (no raw fixture needed).
    This golden test verifies the 6 core abilities are generated correctly.
    """
    expected_path = Path("tests/fixtures/srd_5_1/normalized/ability_scores.json")

    parsed = parse_ability_scores()
    processed = [clean_ability_score_record(a) for a in parsed]

    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("ability_score")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected


def test_ability_scores_count() -> None:
    """Verify we have exactly 6 core D&D 5e ability scores."""
    parsed = parse_ability_scores()
    assert len(parsed) == 6


def test_ability_scores_canonical_list() -> None:
    """Verify all 6 core ability scores are present."""
    expected_abilities = {
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    }

    parsed = parse_ability_scores()
    actual_abilities = {a["simple_name"] for a in parsed}

    assert actual_abilities == expected_abilities


def test_ability_scores_abbreviations() -> None:
    """Verify all ability scores have correct 3-letter abbreviations."""
    expected_abbrev = {
        "strength": "STR",
        "dexterity": "DEX",
        "constitution": "CON",
        "intelligence": "INT",
        "wisdom": "WIS",
        "charisma": "CHA",
    }

    parsed = parse_ability_scores()

    for ability in parsed:
        assert ability["abbreviation"] == expected_abbrev[ability["simple_name"]]


def test_ability_scores_have_required_fields() -> None:
    """Verify all ability scores have required schema fields."""
    parsed = parse_ability_scores()

    for ability in parsed:
        assert "id" in ability
        assert "simple_name" in ability
        assert "name" in ability
        assert "abbreviation" in ability
        assert "description" in ability
        assert "page" in ability
        assert "source" in ability
        assert "skills" in ability

        # Verify ID format
        assert ability["id"].startswith("ability:")

        # Verify abbreviation is 3 uppercase letters
        assert len(ability["abbreviation"]) == 3
        assert ability["abbreviation"].isupper()

        # Verify page number (from SRD pages 76-78)
        assert 76 <= ability["page"] <= 78

        # Verify source
        assert ability["source"] == "SRD_CC_v5.1"

        # Verify description is non-empty array
        assert isinstance(ability["description"], list)
        assert len(ability["description"]) > 0

        # Verify skills is an array (may be empty for CON)
        assert isinstance(ability["skills"], list)
