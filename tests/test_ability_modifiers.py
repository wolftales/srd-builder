"""Tests for ability score modifier calculation."""


def test_add_ability_modifiers_calculates_correctly():
    """Verify D&D 5e modifier formula: (score - 10) // 2."""
    from srd_builder.postprocess import add_ability_modifiers

    monster = {
        "name": "Test Monster",
        "ability_scores": {
            "strength": 21,  # +5
            "dexterity": 10,  # +0
            "constitution": 18,  # +4
            "intelligence": 8,  # -1
            "wisdom": 13,  # +1
            "charisma": 6,  # -2
        },
    }

    result = add_ability_modifiers(monster)

    assert result["ability_scores"]["strength"] == 21
    assert result["ability_scores"]["strength_modifier"] == 5

    assert result["ability_scores"]["dexterity"] == 10
    assert result["ability_scores"]["dexterity_modifier"] == 0

    assert result["ability_scores"]["constitution"] == 18
    assert result["ability_scores"]["constitution_modifier"] == 4

    assert result["ability_scores"]["intelligence"] == 8
    assert result["ability_scores"]["intelligence_modifier"] == -1

    assert result["ability_scores"]["wisdom"] == 13
    assert result["ability_scores"]["wisdom_modifier"] == 1

    assert result["ability_scores"]["charisma"] == 6
    assert result["ability_scores"]["charisma_modifier"] == -2


def test_add_ability_modifiers_handles_missing_scores():
    """Handle monsters with no ability scores."""
    from srd_builder.postprocess import add_ability_modifiers

    monster = {"name": "Test", "ability_scores": {}}
    result = add_ability_modifiers(monster)
    assert result["ability_scores"] == {}

    monster_no_scores = {"name": "Test"}
    result = add_ability_modifiers(monster_no_scores)
    assert "ability_scores" not in result or result.get("ability_scores") == {}


def test_add_ability_modifiers_handles_partial_scores():
    """Handle monsters with only some ability scores."""
    from srd_builder.postprocess import add_ability_modifiers

    monster = {
        "name": "Partial",
        "ability_scores": {
            "strength": 16,  # +3
            "intelligence": 3,  # -4
        },
    }

    result = add_ability_modifiers(monster)

    assert result["ability_scores"]["strength"] == 16
    assert result["ability_scores"]["strength_modifier"] == 3
    assert result["ability_scores"]["intelligence"] == 3
    assert result["ability_scores"]["intelligence_modifier"] == -4
    assert "dexterity_modifier" not in result["ability_scores"]


def test_add_ability_modifiers_in_pipeline():
    """Verify modifiers are added during clean_monster_record."""
    from srd_builder.postprocess import clean_monster_record

    monster = {
        "id": "monster:test",
        "name": "Test Monster",
        "page": 1,
        "src": "SRD 5.1",
        "armor_class": 15,
        "hit_points": 50,
        "ability_scores": {
            "strength": 14,  # +2
            "dexterity": 12,  # +1
            "constitution": 16,  # +3
            "intelligence": 10,  # +0
            "wisdom": 8,  # -1
            "charisma": 7,  # -2
        },
    }

    result = clean_monster_record(monster)

    # Verify original scores preserved
    assert result["ability_scores"]["strength"] == 14
    assert result["ability_scores"]["wisdom"] == 8

    # Verify modifiers calculated
    assert result["ability_scores"]["strength_modifier"] == 2
    assert result["ability_scores"]["dexterity_modifier"] == 1
    assert result["ability_scores"]["constitution_modifier"] == 3
    assert result["ability_scores"]["intelligence_modifier"] == 0
    assert result["ability_scores"]["wisdom_modifier"] == -1
    assert result["ability_scores"]["charisma_modifier"] == -2


def test_ability_modifiers_edge_cases():
    """Test edge cases for ability scores."""
    from srd_builder.postprocess import add_ability_modifiers

    # Score of 1 (common for constructs' mental stats)
    monster = {"ability_scores": {"intelligence": 1}}  # -5
    result = add_ability_modifiers(monster)
    assert result["ability_scores"]["intelligence_modifier"] == -5

    # Score of 30 (legendary creatures)
    monster = {"ability_scores": {"strength": 30}}  # +10
    result = add_ability_modifiers(monster)
    assert result["ability_scores"]["strength_modifier"] == 10

    # Odd scores
    monster = {"ability_scores": {"dexterity": 15}}  # +2
    result = add_ability_modifiers(monster)
    assert result["ability_scores"]["dexterity_modifier"] == 2
