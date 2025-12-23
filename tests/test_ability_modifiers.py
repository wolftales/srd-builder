"""Tests for ability score nested {value, modifier} format in schema v2.0.0."""


def test_parser_generates_nested_ability_scores():
    """Verify parser generates nested {value, modifier} format."""
    from srd_builder.parse.parse_monsters import normalize_monster

    raw_monster = {
        "id": "monster:test",
        "name": "Test Monster",
        "ability_scores": {
            "str": 21,  # +5
            "dex": 10,  # +0
            "con": 18,  # +4
            "int": 8,  # -1
            "wis": 13,  # +1
            "cha": 6,  # -2
        },
    }

    result = normalize_monster(raw_monster)

    # Verify nested format: {value, modifier}
    assert result["ability_scores"]["strength"] == {"value": 21, "modifier": 5}
    assert result["ability_scores"]["dexterity"] == {"value": 10, "modifier": 0}
    assert result["ability_scores"]["constitution"] == {"value": 18, "modifier": 4}
    assert result["ability_scores"]["intelligence"] == {"value": 8, "modifier": -1}
    assert result["ability_scores"]["wisdom"] == {"value": 13, "modifier": 1}
    assert result["ability_scores"]["charisma"] == {"value": 6, "modifier": -2}


def test_parser_handles_missing_ability_scores():
    """Handle monsters with no ability scores."""
    from srd_builder.parse.parse_monsters import normalize_monster

    raw_monster = {
        "id": "monster:test",
        "name": "Test Monster",
        "ability_scores": {},
    }

    result = normalize_monster(raw_monster)
    assert result["ability_scores"] == {}


def test_parser_handles_partial_ability_scores():
    """Handle monsters with only some ability scores."""
    from srd_builder.parse.parse_monsters import normalize_monster

    raw_monster = {
        "id": "monster:partial",
        "name": "Partial",
        "ability_scores": {
            "str": 16,  # +3
            "int": 3,  # -4
        },
    }

    result = normalize_monster(raw_monster)

    assert result["ability_scores"]["strength"] == {"value": 16, "modifier": 3}
    assert result["ability_scores"]["intelligence"] == {"value": 3, "modifier": -4}
    assert "dexterity" not in result["ability_scores"]


def test_ability_score_modifier_formula():
    """Verify D&D 5e modifier formula: (score - 10) // 2 for edge cases."""
    from srd_builder.parse.parse_monsters import normalize_monster

    # Score of 1 (common for constructs' mental stats): -5 modifier
    raw_monster = {"id": "monster:test", "ability_scores": {"int": 1}}
    result = normalize_monster(raw_monster)
    assert result["ability_scores"]["intelligence"] == {"value": 1, "modifier": -5}

    # Score of 30 (legendary creatures): +10 modifier
    raw_monster = {"id": "monster:test", "ability_scores": {"str": 30}}
    result = normalize_monster(raw_monster)
    assert result["ability_scores"]["strength"] == {"value": 30, "modifier": 10}

    # Odd scores round down: 15 -> +2 modifier
    raw_monster = {"id": "monster:test", "ability_scores": {"dex": 15}}
    result = normalize_monster(raw_monster)
    assert result["ability_scores"]["dexterity"] == {"value": 15, "modifier": 2}


def test_postprocess_add_ability_modifiers_is_noop():
    """Verify add_ability_modifiers is now a no-op (parser handles it)."""
    from srd_builder.postprocess import add_ability_modifiers

    # Input already has nested format from parser
    monster = {
        "name": "Test Monster",
        "ability_scores": {
            "strength": {"value": 14, "modifier": 2},
            "dexterity": {"value": 12, "modifier": 1},
        },
    }

    result = add_ability_modifiers(monster)

    # Function should pass through unchanged
    assert result == monster
    assert result["ability_scores"]["strength"] == {"value": 14, "modifier": 2}
