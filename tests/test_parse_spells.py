"""Unit tests for spell parsing functions."""

from __future__ import annotations

from srd_builder.parse.parse_spells import (
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
    assert result == {"type": "ranged", "distance": {"value": 150, "unit": "feet"}}


def test_parse_range_special_self() -> None:
    result = _parse_range("Self")
    assert result == {"type": "self"}


def test_parse_range_special_touch() -> None:
    result = _parse_range("Touch")
    assert result == {"type": "touch"}


def test_parse_range_with_area() -> None:
    result = _parse_range("Self (15-foot cone)")
    assert result == {
        "type": "self",
        "area": {"shape": "cone", "size": {"value": 15, "unit": "feet"}},
    }


def test_parse_duration_instantaneous() -> None:
    result = _parse_duration("Instantaneous")
    assert result == {"requires_concentration": False, "length": "instantaneous"}


def test_parse_duration_with_concentration() -> None:
    result = _parse_duration("Concentration, up to 1 minute")
    assert result == {"requires_concentration": True, "length": "up to 1 minute"}


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


# Healing pattern tests
def test_extract_effects_healing_dice() -> None:
    """Test dice-based healing like Cure Wounds."""
    description = "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier."
    result = _extract_effects(description)
    assert "healing" in result
    assert result["healing"]["dice"] == "1d8"


def test_extract_effects_healing_fixed_amount() -> None:
    """Test fixed-amount healing like Heal."""
    description = "Choose a creature that you can see within range. A surge of positive energy washes through the creature, causing it to regain 70 hit points."
    result = _extract_effects(description)
    assert "healing" in result
    assert result["healing"]["amount"] == 70


def test_extract_effects_healing_with_modifier() -> None:
    """Test dice-based healing with modifier like Regenerate."""
    description = "The target regains 4d8 + 15 hit points."
    result = _extract_effects(description)
    assert "healing" in result
    assert result["healing"]["dice"] == "4d8+15"


def test_extract_effects_healing_conditional() -> None:
    """Test conditional healing like Vampiric Touch."""
    description = "On a hit, the target takes 3d6 necrotic damage, and you regain hit points equal to half the amount of necrotic damage dealt."
    result = _extract_effects(description)
    assert "healing" in result
    assert result["healing"]["condition"] == "half the amount of necrotic damage dealt"


def test_extract_effects_healing_full_restore() -> None:
    """Test full healing like Wish."""
    description = "You grant up to ten creatures that you can see immunity to a single spell or other magical effect for 8 hours. For instance, you could make yourself and all your companions immune to a lich's life drain attack. You allow up to twenty creatures that you can see to regain all hit points, and you end all effects on them described in the greater restoration spell."
    result = _extract_effects(description)
    assert "healing" in result
    assert result["healing"]["condition"] == "all hit points"


def test_extract_effects_healing_mass_heal() -> None:
    """Test large fixed amount healing like Mass Heal."""
    description = "A flood of healing energy flows from you into injured creatures around you. You restore up to 700 hit points, divided as you choose among any number of creatures that you can see within range."
    result = _extract_effects(description)
    assert "healing" in result
    assert result["healing"]["amount"] == 700


# AOE pattern tests
def test_extract_effects_area_cylinder_with_height() -> None:
    """Test cylinder with height pattern like Flame Strike."""
    description = "A vertical column of divine fire roars down from the heavens in a location you specify. Each creature in a 10-foot-radius, 40-foot-high cylinder centered on a point within range must make a Dexterity saving throw."
    result = _extract_effects(description)
    assert "area" in result
    assert result["area"]["shape"] == "cylinder"
    assert result["area"]["size"] == 10
    assert result["area"]["unit"] == "feet"


def test_extract_effects_area_diameter() -> None:
    """Test diameter pattern like Flaming Sphere."""
    description = "A 5-foot-diameter sphere of fire appears in an unoccupied space of your choice within range and lasts for the duration."
    result = _extract_effects(description)
    assert "area" in result
    assert result["area"]["shape"] == "sphere"
    assert result["area"]["size"] == 5
    assert result["area"]["unit"] == "feet"


def test_extract_effects_area_radius_only() -> None:
    """Test radius-only pattern (defaults to sphere) like Antilife Shell."""
    description = "A shimmering barrier extends out from you in a 10-foot radius and moves with you, remaining centered on you and hedging out creatures other than undead and constructs."
    result = _extract_effects(description)
    assert "area" in result
    assert result["area"]["shape"] == "sphere"
    assert result["area"]["size"] == 10
    assert result["area"]["unit"] == "feet"


def test_extract_effects_area_reversed_cylinder() -> None:
    """Test reversed cylinder pattern like Call Lightning."""
    description = "A storm cloud appears in the shape of a cylinder that is 10 feet tall with a 60-foot radius, centered on a point you can see 100 feet directly above you."
    result = _extract_effects(description)
    assert "area" in result
    assert result["area"]["shape"] == "cylinder"
    assert result["area"]["size"] == 60
    assert result["area"]["unit"] == "feet"


def test_extract_effects_area_standard_cube() -> None:
    """Test standard cube pattern."""
    description = "Choose an area no larger than a 20-foot cube within range."
    result = _extract_effects(description)
    assert "area" in result
    assert result["area"]["shape"] == "cube"
    assert result["area"]["size"] == 20
    assert result["area"]["unit"] == "feet"
