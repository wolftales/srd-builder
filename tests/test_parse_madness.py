"""Tests for madness parsing module."""

from __future__ import annotations

from srd_builder.parse.parse_madness import (
    _extract_madness_effects,
    _parse_single_madness,
    parse_madness_records,
)


def test_parse_madness_records_empty():
    """Test parsing empty madness list."""
    result = parse_madness_records([])
    assert result == []


def test_parse_madness_records_multiple():
    """Test parsing multiple madness categories."""
    raw_categories = [
        {
            "name": "Short-Term Madness",
            "raw_text": "1-10 The character retreats into his or her mind.\n11-20 The character becomes incapacitated.",
            "page": 201,
        },
        {
            "name": "Long-Term Madness",
            "raw_text": "1-10 The character feels compelled to repeat a specific activity.\n11-20 The character experiences vivid hallucinations.",
            "page": 201,
        },
    ]

    result = parse_madness_records(raw_categories)

    assert len(result) == 2
    assert result[0]["simple_name"] == "short_term_madness"
    assert result[1]["simple_name"] == "long_term_madness"


def test_parse_single_madness_complete():
    """Test parsing a complete madness record."""
    raw = {
        "name": "Short-Term Madness",
        "raw_text": "1-20 The character retreats into his or her mind and becomes paralyzed.\n21-30 The character becomes incapacitated and spends the duration screaming.",
        "page": 201,
    }

    result = _parse_single_madness(raw)

    assert result is not None
    assert result["id"] == "madness:short_term_madness"
    assert result["name"] == "Short-Term Madness"
    assert result["simple_name"] == "short_term_madness"
    assert result["duration"] == "1d10 minutes"
    assert result["page"] == 201
    assert result["source"] == "SRD 5.1"
    assert "summary" in result
    assert len(result["effects"]) == 2


def test_parse_single_madness_long_term():
    """Test long-term madness has correct duration."""
    raw = {
        "name": "Long-Term Madness",
        "raw_text": "1-10 Some effect here.",
        "page": 201,
    }

    result = _parse_single_madness(raw)

    assert result is not None
    assert result["duration"] == "1d10 × 10 hours"


def test_parse_single_madness_indefinite():
    """Test indefinite madness has correct duration."""
    raw = {
        "name": "Indefinite Madness",
        "raw_text": "1-10 Some effect here.",
        "page": 201,
    }

    result = _parse_single_madness(raw)

    assert result is not None
    assert result["duration"] == "until cured"


def test_parse_single_madness_missing_name():
    """Test parsing fails gracefully with missing name."""
    raw = {"name": "", "raw_text": "Some text", "page": 201}

    result = _parse_single_madness(raw)

    assert result is None


def test_parse_single_madness_missing_text():
    """Test parsing fails gracefully with missing text."""
    raw = {"name": "Some Madness", "raw_text": "", "page": 201}

    result = _parse_single_madness(raw)

    assert result is None


def test_extract_madness_effects_basic():
    """Test extracting basic d100 table effects."""
    text = """
    1-10 The character retreats into his or her mind and becomes paralyzed.
    11-20 The character becomes incapacitated and spends the duration screaming.
    21-30 The character becomes frightened and must use his or her action.
    """

    effects = _extract_madness_effects(text)

    assert len(effects) == 3
    assert effects[0]["roll"] == "1-10"
    assert "retreats into" in effects[0]["effect"]
    assert effects[1]["roll"] == "11-20"
    assert "incapacitated" in effects[1]["effect"]
    assert effects[2]["roll"] == "21-30"
    assert "frightened" in effects[2]["effect"]


def test_extract_madness_effects_single_number():
    """Test extracting effects with single numbers (e.g., 100)."""
    text = """
    91-99 The character experiences vivid hallucinations.
    100 The character falls unconscious.
    """

    effects = _extract_madness_effects(text)

    assert len(effects) == 2
    assert effects[0]["roll"] == "91-99"
    assert effects[1]["roll"] == "100"
    assert "unconscious" in effects[1]["effect"]


def test_extract_madness_effects_empty():
    """Test extracting effects from empty text."""
    effects = _extract_madness_effects("")
    assert effects == []


def test_extract_madness_effects_filters_headers():
    """Test that obvious headers are filtered out."""
    text = """
    d100 Effect
    1-10 The character retreats into his or her mind.
    """

    effects = _extract_madness_effects(text)

    # Should skip "Effect" header
    assert len(effects) == 1
    assert effects[0]["roll"] == "1-10"


def test_parse_madness_records_filters_none():
    """Test that None results are filtered from final list."""
    raw_categories = [
        {"name": "Valid Madness", "raw_text": "1-10 Some effect.", "page": 201},
        {"name": "", "raw_text": "Invalid - no name", "page": 201},
        {"name": "Another Valid", "raw_text": "1-10 Another effect.", "page": 201},
    ]

    result = parse_madness_records(raw_categories)

    # Should only have 2 valid records
    assert len(result) == 2
    assert result[0]["name"] == "Valid Madness"
    assert result[1]["name"] == "Another Valid"
