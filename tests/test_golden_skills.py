from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_skills import parse_skills
from srd_builder.postprocess import clean_skill_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_skills_dataset_golden() -> None:
    """Verify skills dataset matches expected output.

    Unlike other datasets, skills is static data (no raw fixture needed).
    This golden test verifies the 18 skills are generated correctly.
    """
    expected_path = Path("tests/fixtures/srd_5_1/normalized/skills.json")

    parsed = parse_skills()
    processed = [clean_skill_record(s) for s in parsed]

    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("skill")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected


def test_skills_count() -> None:
    """Verify we have exactly 18 D&D 5e skills."""
    parsed = parse_skills()
    assert len(parsed) == 18


def test_skills_canonical_list() -> None:
    """Verify all 18 skills are present."""
    expected_skills = {
        "acrobatics",
        "animal_handling",
        "arcana",
        "athletics",
        "deception",
        "history",
        "insight",
        "intimidation",
        "investigation",
        "medicine",
        "nature",
        "perception",
        "performance",
        "persuasion",
        "religion",
        "sleight_of_hand",
        "stealth",
        "survival",
    }

    parsed = parse_skills()
    actual_skills = {s["simple_name"] for s in parsed}

    assert actual_skills == expected_skills


def test_skills_ability_associations() -> None:
    """Verify skills are associated with correct abilities."""
    expected_by_ability = {
        "strength": ["athletics"],
        "dexterity": ["acrobatics", "sleight_of_hand", "stealth"],
        "intelligence": ["arcana", "history", "investigation", "nature", "religion"],
        "wisdom": [
            "animal_handling",
            "insight",
            "medicine",
            "perception",
            "survival",
        ],
        "charisma": ["deception", "intimidation", "performance", "persuasion"],
    }

    parsed = parse_skills()

    for ability, expected_skills in expected_by_ability.items():
        actual_skills = sorted(s["simple_name"] for s in parsed if s["ability"] == ability)
        assert actual_skills == sorted(expected_skills)


def test_skills_have_required_fields() -> None:
    """Verify all skills have required schema fields."""
    parsed = parse_skills()

    for skill in parsed:
        assert "id" in skill
        assert "simple_name" in skill
        assert "name" in skill
        assert "ability" in skill
        assert "ability_id" in skill
        assert "description" in skill
        assert "page" in skill
        assert "source" in skill

        # Verify ID format
        assert skill["id"].startswith("skill:")

        # Verify ability_id format
        assert skill["ability_id"].startswith("ability:")
        assert skill["ability_id"] == f"ability:{skill['ability']}"

        # Verify ability is valid
        assert skill["ability"] in [
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        ]

        # Verify page number (from SRD pages 76-79)
        assert 76 <= skill["page"] <= 79

        # Verify source
        assert skill["source"] == "SRD_CC_v5.1"

        # Verify description is non-empty array
        assert isinstance(skill["description"], list)
        assert len(skill["description"]) > 0
