"""Tests for poison description parsing module."""

from __future__ import annotations

from srd_builder.parse.parse_poison_descriptions import (
    _parse_single_description,
    parse_poison_description_records,
)


def test_parse_poison_description_records_empty():
    """Test parsing empty poison descriptions list."""
    result = parse_poison_description_records([])
    assert result == []


def test_parse_poison_description_records_multiple():
    """Test parsing multiple poison descriptions."""
    raw_sections = [
        {
            "name": "Assassin's Blood",
            "raw_text": "A creature subjected to this poison must make a DC 10 Constitution saving throw.",
            "page": 204,
        },
        {
            "name": "Burnt Othur Fumes",
            "raw_text": "A creature subjected to this poison must make a DC 13 Constitution saving throw.",
            "page": 204,
        },
    ]

    result = parse_poison_description_records(raw_sections)

    assert len(result) == 2
    assert result[0]["simple_name"] == "assassins_blood"
    assert result[1]["simple_name"] == "burnt_othur_fumes"


def test_parse_single_description_basic():
    """Test parsing a basic poison description."""
    raw = {
        "name": "Assassin's Blood",
        "raw_text": "A creature subjected to this poison must succeed on a DC 10 Constitution saving throw or become poisoned for 24 hours.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert result["simple_name"] == "assassins_blood"
    assert "description" in result
    assert result["page"] == 204


def test_parse_single_description_with_save():
    """Test parsing poison description with save DC."""
    raw = {
        "name": "Burnt Othur Fumes",
        "raw_text": "A creature subjected to this poison must succeed on a DC 13 Constitution saving throw or take 10 (3d6) poison damage.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert "save" in result
    assert result["save"]["dc"] == 13
    assert result["save"]["ability"] == "constitution"


def test_parse_single_description_with_damage():
    """Test parsing poison description with damage."""
    raw = {
        "name": "Serpent Venom",
        "raw_text": "A creature subjected to this poison must succeed on a DC 11 Constitution saving throw or takes 10 (3d6) poison damage.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert "damage" in result
    assert result["damage"]["average"] == 10
    assert result["damage"]["formula"] == "3d6"
    assert result["damage"]["type"] == "poison"


def test_parse_single_description_with_save_and_damage():
    """Test parsing poison with both save and damage."""
    raw = {
        "name": "Wyvern Poison",
        "raw_text": "A creature subjected to this poison must make a DC 15 Constitution saving throw and takes 24 (7d6) poison damage on a failed save.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert "save" in result
    assert result["save"]["dc"] == 15
    assert result["save"]["ability"] == "constitution"
    assert "damage" in result
    assert result["damage"]["average"] == 24
    assert result["damage"]["formula"] == "7d6"
    assert result["damage"]["type"] == "poison"


def test_parse_single_description_missing_name():
    """Test parsing fails gracefully with missing name."""
    raw = {"name": "", "raw_text": "Some text", "page": 204}

    result = _parse_single_description(raw)

    assert result is None


def test_parse_single_description_missing_text():
    """Test parsing fails gracefully with missing text."""
    raw = {"name": "Some Poison", "raw_text": "", "page": 204}

    result = _parse_single_description(raw)

    assert result is None


def test_parse_single_description_no_save():
    """Test parsing poison without save DC."""
    raw = {
        "name": "Basic Poison",
        "raw_text": "This is a simple poison with no save DC mentioned.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert "save" not in result


def test_parse_single_description_no_damage():
    """Test parsing poison without damage."""
    raw = {
        "name": "Oil of Taggit",
        "raw_text": "A creature subjected to this poison must succeed on a DC 13 Constitution saving throw or become poisoned for 24 hours.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert "damage" not in result


def test_parse_poison_description_records_filters_none():
    """Test that None results are filtered from final list."""
    raw_sections = [
        {
            "name": "Valid Poison",
            "raw_text": "A creature must make a DC 10 save.",
            "page": 204,
        },
        {"name": "", "raw_text": "Invalid - no name", "page": 204},
        {
            "name": "Another Valid",
            "raw_text": "Another poison effect.",
            "page": 204,
        },
    ]

    result = parse_poison_description_records(raw_sections)

    # Should only have 2 valid records
    assert len(result) == 2
    assert result[0]["simple_name"] == "valid_poison"
    assert result[1]["simple_name"] == "another_valid"


def test_parse_single_description_different_save_ability():
    """Test parsing with non-Constitution save."""
    raw = {
        "name": "Mind Poison",
        "raw_text": "A creature must succeed on a DC 15 Wisdom saving throw or become confused.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert "save" in result
    assert result["save"]["ability"] == "wisdom"


def test_parse_single_description_different_damage_type():
    """Test parsing with non-poison damage type."""
    raw = {
        "name": "Acid Vial",
        "raw_text": "A creature takes 5 (1d10) acid damage from this substance.",
        "page": 204,
    }

    result = _parse_single_description(raw)

    assert result is not None
    assert "damage" in result
    assert result["damage"]["type"] == "acid"
