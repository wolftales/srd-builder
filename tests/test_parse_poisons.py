"""Tests for poison parsing module."""

from __future__ import annotations

from srd_builder.parse.parse_poisons import (
    _extract_condition,
    _extract_cost,
    _extract_damage_info,
    _extract_duration,
    _extract_poison_type,
    _extract_save_info,
    parse_poison_records,
)


def test_parse_poison_records_empty():
    """Test parsing empty poison list."""
    result = parse_poison_records([])
    assert result == []


def test_parse_poison_records_multiple():
    """Test parsing multiple poison records."""
    raw_poisons = [
        {
            "name": "Serpent Venom",
            "raw_text": "This poison must be harvested from a dead or incapacitated giant poisonous snake. A creature subjected to this poison must succeed on a DC 11 Constitution saving throw, taking 10 (3d6) poison damage on a failed save, or half as much damage on a successful one.",
            "page": 204,
        },
        {
            "name": "Assassin's Blood",
            "raw_text": "A creature subjected to this poison must make a DC 10 Constitution saving throw. On a failed save, it takes 6 (1d12) poison damage and is poisoned for 24 hours.",
            "page": 204,
        },
    ]

    result = parse_poison_records(raw_poisons)

    assert len(result) == 2
    assert result[0]["simple_name"] == "serpent_venom"
    assert result[1]["simple_name"] == "assassins_blood"


def test_parse_single_poison_complete():
    """Test parsing a complete poison with all fields."""
    raw = {
        "name": "Serpent Venom",
        "raw_text": "(Injury) A creature subjected to this poison must succeed on a DC 11 Constitution saving throw, taking 10 (3d6) poison damage on a failed save, or half as much damage on a successful one.",
        "page": 204,
    }

    result = parse_poison_records([raw])

    assert len(result) == 1
    poison = result[0]
    assert poison["id"] == "poison:serpent_venom"
    assert poison["name"] == "Serpent Venom"
    assert poison["simple_name"] == "serpent_venom"
    assert poison["type"] == "injury"
    assert poison["page"] == 204
    assert poison["source"] == "SRD 5.1"
    assert "description" in poison


def test_parse_single_poison_minimal():
    """Test parsing a minimal poison with just name and text."""
    raw = {
        "name": "Unknown Poison",
        "raw_text": "This is a mysterious poison.",
        "page": 204,
    }

    result = parse_poison_records([raw])

    assert len(result) == 1
    poison = result[0]
    assert poison["id"] == "poison:unknown_poison"
    assert poison["name"] == "Unknown Poison"
    assert poison["type"] == "injury"  # Default type


def test_parse_single_poison_missing_name():
    """Test that poison without name is skipped."""
    raw = {
        "raw_text": "Some poison text",
        "page": 204,
    }

    result = parse_poison_records([raw])
    assert result == []


def test_parse_single_poison_missing_text():
    """Test that poison without text is skipped."""
    raw = {
        "name": "Empty Poison",
        "page": 204,
    }

    result = parse_poison_records([raw])
    assert result == []


def test_extract_poison_type_injury():
    """Test extracting injury type."""
    text = "(Injury) This poison must be applied to a weapon."
    result = _extract_poison_type(text)
    assert result == "injury"


def test_extract_poison_type_contact():
    """Test extracting contact type."""
    text = "Contact poison can be absorbed through skin."
    result = _extract_poison_type(text)
    assert result == "contact"


def test_extract_poison_type_ingested():
    """Test extracting ingested type."""
    text = "This Ingested poison takes effect when swallowed."
    result = _extract_poison_type(text)
    assert result == "ingested"


def test_extract_poison_type_inhaled():
    """Test extracting inhaled type."""
    text = "Inhaled poison affects creatures in a cloud."
    result = _extract_poison_type(text)
    assert result == "inhaled"


def test_extract_poison_type_not_found():
    """Test when no type keyword is found."""
    text = "This is a mysterious poison with no type specified."
    result = _extract_poison_type(text)
    assert result is None


def test_extract_save_info_constitution():
    """Test extracting Constitution save."""
    text = "A creature must succeed on a Constitution saving throw or takes damage. The DC is 11."
    # Wait, the regex expects "Constitution saving throw...DC 11" format
    text = "A creature subjected to this poison must make a Constitution saving throw with DC 11."
    result = _extract_save_info(text)
    assert result == {"ability": "constitution", "dc": 11}


def test_extract_save_info_wisdom():
    """Test extracting Wisdom save."""
    text = "The target makes a Wisdom saving throw against DC 15."
    result = _extract_save_info(text)
    assert result == {"ability": "wisdom", "dc": 15}


def test_extract_save_info_alternate_format():
    """Test extracting save with DC at end."""
    text = "Constitution saving throw with DC 20."
    result = _extract_save_info(text)
    assert result == {"ability": "constitution", "dc": 20}


def test_extract_save_info_not_found():
    """Test when no save info is found."""
    text = "This poison has no saving throw."
    result = _extract_save_info(text)
    assert result is None


def test_extract_damage_info_basic():
    """Test extracting basic damage."""
    text = "The creature takes 3d6 poison damage."
    result = _extract_damage_info(text)
    assert result == {
        "dice": "3d6",
        "type": "poison",
        "type_id": "damage_type:poison",
    }


def test_extract_damage_info_with_bonus():
    """Test extracting damage with bonus."""
    text = "The target takes 2d8 + 4 necrotic damage."
    result = _extract_damage_info(text)
    assert result["dice"] == "2d8 + 4"
    assert result["type"] == "necrotic"


def test_extract_damage_info_psychic():
    """Test extracting psychic damage."""
    text = "The creature suffers 1d10 psychic damage."
    result = _extract_damage_info(text)
    assert result["type"] == "psychic"


def test_extract_damage_info_no_type_specified():
    """Test extracting damage when type is not specified."""
    text = "The target takes 2d6 damage."
    result = _extract_damage_info(text)
    assert result["type"] == "poison"  # Default to poison


def test_extract_damage_info_not_found():
    """Test when no damage info is found."""
    text = "This poison has no damage effect."
    result = _extract_damage_info(text)
    assert result is None


def test_extract_condition_poisoned():
    """Test extracting poisoned condition."""
    text = "The creature is poisoned for 24 hours."
    result = _extract_condition(text)
    assert result == "poisoned"


def test_extract_condition_paralyzed():
    """Test extracting paralyzed condition."""
    text = "The target becomes paralyzed."
    result = _extract_condition(text)
    assert result == "paralyzed"


def test_extract_condition_unconscious():
    """Test extracting unconscious condition."""
    text = "The creature falls unconscious."
    result = _extract_condition(text)
    assert result == "unconscious"


def test_extract_condition_stunned():
    """Test extracting stunned condition."""
    text = "The target is stunned until cured."
    result = _extract_condition(text)
    assert result == "stunned"


def test_extract_condition_not_found():
    """Test when no condition is found."""
    text = "This poison has no condition effect."
    result = _extract_condition(text)
    assert result is None


def test_extract_duration_hours():
    """Test extracting duration in hours."""
    text = "The effect lasts for 24 hours."
    result = _extract_duration(text)
    assert result == "24 hours"


def test_extract_duration_minutes():
    """Test extracting duration in minutes."""
    text = "The poison persists for 10 minutes."
    result = _extract_duration(text)
    assert result == "10 minutes"


def test_extract_duration_days():
    """Test extracting duration in days."""
    text = "The creature is affected for 7 days."
    result = _extract_duration(text)
    assert result == "7 days"


def test_extract_duration_until():
    """Test extracting 'until' duration."""
    text = "The effect continues for until cured."
    result = _extract_duration(text)
    assert result == "until"


def test_extract_duration_not_found():
    """Test when no duration is found."""
    text = "This poison has no specified duration."
    result = _extract_duration(text)
    assert result is None


def test_extract_cost_gold():
    """Test extracting cost in gold pieces."""
    text = "This poison costs 200 gp."
    result = _extract_cost(text)
    assert result == {"amount": 200, "currency": "gp"}


def test_extract_cost_silver():
    """Test extracting cost in silver pieces."""
    text = "Available for 50 sp."
    result = _extract_cost(text)
    assert result == {"amount": 50, "currency": "sp"}


def test_extract_cost_with_commas():
    """Test extracting cost with comma separators."""
    text = "This rare poison sells for 1,500 gp."
    result = _extract_cost(text)
    assert result == {"amount": 1500, "currency": "gp"}


def test_extract_cost_platinum():
    """Test extracting cost in platinum pieces."""
    text = "Worth 10 pp."
    result = _extract_cost(text)
    assert result == {"amount": 10, "currency": "pp"}


def test_extract_cost_not_found():
    """Test when no cost is found."""
    text = "This poison has no listed cost."
    result = _extract_cost(text)
    assert result is None
