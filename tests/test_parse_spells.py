"""Unit tests for spell parsing functions."""

from __future__ import annotations

from srd_builder.parse_spells import (
    _extract_effects,
    _extract_scaling,
    _parse_casting_time,
    _parse_components,
    _parse_duration,
    _parse_level_and_school,
    _parse_range,
)


def test_parse_level_and_school_cantrip() -> None:
    result = _parse_level_and_school("Evocation cantrip")
    assert result == (0, "evocation")


def test_parse_level_and_school_leveled_spell() -> None:
    result = _parse_level_and_school("3rd-level evocation")
    assert result == (3, "evocation")


def test_parse_level_and_school_first_level() -> None:
    result = _parse_level_and_school("1st-level abjuration")
    assert result == (1, "abjuration")


def test_parse_casting_time_action() -> None:
    result = _parse_casting_time("1 action")
    assert result == "1 action"


def test_parse_casting_time_bonus_action() -> None:
    result = _parse_casting_time("1 bonus action")
    assert result == "1 bonus action"


def test_parse_casting_time_minutes() -> None:
    result = _parse_casting_time("10 minutes")
    assert result == "10 minutes"


def test_parse_range_numeric() -> None:
    result = _parse_range("150 feet")
    assert result == {"kind": "ranged", "value": 150, "unit": "feet"}


def test_parse_range_special_self() -> None:
    result = _parse_range("Self")
    assert result == "self"


def test_parse_range_special_touch() -> None:
    result = _parse_range("Touch")
    assert result == "touch"


def test_parse_duration_instantaneous() -> None:
    duration, concentration = _parse_duration("Instantaneous")
    assert duration == "instantaneous"
    assert concentration is False


def test_parse_duration_with_concentration() -> None:
    duration, concentration = _parse_duration("Concentration, up to 1 minute")
    assert duration == "up to 1 minute"
    assert concentration is True


def test_parse_components_vsm() -> None:
    result = _parse_components("V, S, M (a tiny ball of bat guano and sulfur)")
    assert result == {
        "verbal": True,
        "somatic": True,
        "material": True,
        "material_description": "a tiny ball of bat guano and sulfur",
    }


def test_parse_components_vs_only() -> None:
    result = _parse_components("V, S")
    assert result == {"verbal": True, "somatic": True, "material": False}


def test_extract_effects_damage() -> None:
    description = "The target takes 8d6 fire damage on a failed save"
    result = _extract_effects(description)
    assert "damage" in result
    assert result["damage"]["dice"] == "8d6"
    assert result["damage"]["type"] == "fire"


def test_extract_effects_save() -> None:
    description = "Each creature must make a Dexterity saving throw"
    result = _extract_effects(description)
    assert "save" in result
    assert result["save"]["ability"] == "dexterity"


def test_extract_scaling_slot_level() -> None:
    description = "At Higher Levels. When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd."
    result = _extract_scaling(description, level=3)
    assert result is not None
    assert result["type"] == "slot"
    assert result["base_level"] == 3
    assert "1d6" in result["formula"]


def test_extract_scaling_character_level() -> None:
    description = "This spell's damage increases by 1d10 when you reach 5th level (2d10), 11th level (3d10), and 17th level (4d10)."
    result = _extract_scaling(description, level=0)
    assert result is not None
    assert result["type"] == "character_level"
    assert "1d10" in result["formula"]


def test_extract_scaling_none() -> None:
    description = "The creature is healed for 1d8 hit points."
    result = _extract_scaling(description, level=1)
    assert result is None
