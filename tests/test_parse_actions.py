"""Tests for action field parsing."""


# TODO(v0.19.0): Update remaining tests to v2.0 schema format
# Two tests updated as examples (test_parse_melee_weapon_attack, test_parse_action_with_saving_throw)
# Others need migration to new field names: attack_bonus (not to_hit), damage array (not dict), dc object, etc.
# See migration examples in docs/migration_v2.0.0/


def test_parse_melee_weapon_attack():
    """Parse typical melee weapon attack (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Greataxe",
        "description": [
            "Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 17 (2d12 + 4) slashing damage."
        ],
    }

    result = parse_action_fields(action)

    assert result["attack_bonus"] == 7
    assert result["range"] == {"reach": 5}
    assert result["damage"] == [
        {
            "dice": "2d12+4",
            "type": "slashing",
            "type_id": "slashing",
        }
    ]
    assert result["description"] == action["description"]  # Preserved


def test_parse_ranged_weapon_attack():
    """Parse ranged weapon attack with range (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Longbow",
        "description": [
            "Ranged Weapon Attack: +4 to hit, range 150/600 ft., one target. Hit: 6 (1d8 + 2) piercing damage."
        ],
    }

    result = parse_action_fields(action)

    assert result["attack_bonus"] == 4
    assert result["range"] == {"normal": 150, "long": 600}
    assert result["damage"] == [
        {
            "dice": "1d8+2",
            "type": "piercing",
            "type_id": "piercing",
        }
    ]
    assert "reach" not in result
    assert result["description"] == action["description"]


def test_parse_action_with_saving_throw():
    """Parse action with DC saving throw (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Breath Weapon",
        "description": [
            "The dragon exhales fire in a 60-foot cone. Each creature in that area must make a DC 21 Dexterity saving throw, taking 63 (18d6) fire damage on a failed save, or half as much damage on a successful one."
        ],
    }

    result = parse_action_fields(action)

    assert result["dc"] == {
        "dc_value": 21,
        "dc_type": "Dexterity",
        "dc_type_id": "dex",
        "success_type": "half",
    }
    assert result["damage"] == [
        {
            "dice": "18d6",
            "type": "fire",
            "type_id": "fire",
        }
    ]


def test_parse_action_multiple_damage_types():
    """Parse action with multiple damage instances (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Claw",
        "description": [
            "Melee Weapon Attack: +14 to hit, reach 10 ft., one target. Hit: 17 (2d6 + 10) slashing damage plus 3 (1d6) fire damage."
        ],
    }

    result = parse_action_fields(action)

    assert result["attack_bonus"] == 14
    assert result["range"] == {"reach": 10}
    assert len(result["damage"]) == 2
    assert result["damage"][0] == {
        "dice": "2d6+10",
        "type": "slashing",
        "type_id": "slashing",
    }
    assert result["damage"][1] == {
        "dice": "1d6",
        "type": "fire",
        "type_id": "fire",
    }


def test_parse_melee_spell_attack():
    """Parse melee spell attack (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Shocking Grasp",
        "description": [
            "Melee Spell Attack: +5 to hit, reach 5 ft., one creature. Hit: 9 (2d8) lightning damage."
        ],
    }

    result = parse_action_fields(action)

    assert result["attack_bonus"] == 5
    assert result["range"] == {"reach": 5}
    assert result["damage"] == [
        {
            "dice": "2d8",
            "type": "lightning",
            "type_id": "lightning",
        }
    ]


def test_parse_ranged_spell_attack():
    """Parse ranged spell attack (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Fire Bolt",
        "description": [
            "Ranged Spell Attack: +7 to hit, range 120/480 ft., one target. Hit: 16 (3d10) fire damage."
        ],
    }

    result = parse_action_fields(action)

    assert result["attack_bonus"] == 7
    assert result["range"] == {"normal": 120, "long": 480}
    assert result["damage"] == [
        {
            "dice": "3d10",
            "type": "fire",
            "type_id": "fire",
        }
    ]


def test_parse_negative_to_hit():
    """Parse action with negative to-hit modifier (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Weak Attack",
        "description": [
            "Melee Weapon Attack: -1 to hit, reach 5 ft., one target. Hit: 1 (1d4 - 1) bludgeoning damage."
        ],
    }

    result = parse_action_fields(action)

    assert result["attack_bonus"] == -1
    assert result["damage"][0]["dice"] == "1d4-1"


def test_parse_action_without_attack():
    """Non-attack actions should not be parsed."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Multiattack",
        "text": "The dragon can use its Frightful Presence. It then makes three attacks: one with its bite and two with its claws.",
    }

    result = parse_action_fields(action)

    assert "attack_type" not in result
    assert "to_hit" not in result
    assert "damage" not in result
    assert result["text"] == action["text"]  # Preserved


def test_parse_action_preserves_all_fields():
    """Parsing should add fields without removing existing ones (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Bite",
        "simple_name": "bite",
        "description": [
            "Melee Weapon Attack: +10 to hit, reach 10 ft., one target. Hit: 17 (2d10 + 6) piercing damage."
        ],
        "custom_field": "should be preserved",
    }

    result = parse_action_fields(action)

    assert result["name"] == "Bite"
    assert result["simple_name"] == "bite"
    assert result["custom_field"] == "should be preserved"
    assert result["attack_bonus"] == 10
    assert result["range"] == {"reach": 10}
    assert result["damage"][0]["type"] == "piercing"


def test_parse_action_in_pipeline():
    """Test action parsing integrated into clean_monster_record (v2.0 schema)."""
    from srd_builder.postprocess import clean_monster_record

    monster = {
        "id": "monster:test",
        "name": "Test Monster",
        "page": 1,
        "src": "SRD 5.1",
        "armor_class": 15,
        "hit_points": 50,
        "ability_scores": {"strength": {"value": 16, "modifier": 3}},
        "actions": [
            {
                "name": "Slam",
                "simple_name": "slam",
                "description": [
                    "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 7 (1d8 + 3) bludgeoning damage."
                ],
            }
        ],
    }

    result = clean_monster_record(monster)

    assert len(result["actions"]) == 1
    action = result["actions"][0]
    assert action["attack_bonus"] == 5
    assert action["range"] == {"reach": 5}
    assert action["damage"][0]["dice"] == "1d8+3"
    assert action["damage"][0]["type"] == "bludgeoning"


def test_parse_legendary_actions():
    """Test action parsing applies to legendary actions (v2.0 schema)."""
    from srd_builder.postprocess import clean_monster_record

    monster = {
        "id": "monster:test",
        "name": "Test",
        "page": 1,
        "src": "SRD 5.1",
        "armor_class": 15,
        "hit_points": 50,
        "ability_scores": {},
        "actions": [],
        "legendary_actions": [
            {
                "name": "Tail Attack",
                "description": [
                    "Melee Weapon Attack: +15 to hit, reach 20 ft., one target. Hit: 18 (2d8 + 9) bludgeoning damage."
                ],
            }
        ],
    }

    result = clean_monster_record(monster)

    legendary = result["legendary_actions"][0]
    assert legendary["attack_bonus"] == 15
    assert legendary["range"] == {"reach": 20}
    assert legendary["damage"][0]["dice"] == "2d8+9"


def test_parse_reactions():
    """Test action parsing applies to reactions (v2.0 schema)."""
    from srd_builder.postprocess import clean_monster_record

    monster = {
        "id": "monster:test",
        "name": "Test",
        "page": 1,
        "src": "SRD 5.1",
        "armor_class": 15,
        "hit_points": 50,
        "ability_scores": {},
        "actions": [],
        "reactions": [
            {
                "name": "Counterattack",
                "description": [
                    "Melee Weapon Attack: +8 to hit, reach 5 ft., one creature. Hit: 10 (2d6 + 3) slashing damage."
                ],
            }
        ],
    }

    result = clean_monster_record(monster)

    reaction = result["reactions"][0]
    assert reaction["attack_bonus"] == 8
    assert reaction["range"] == {"reach": 5}
    assert reaction["damage"][0]["dice"] == "2d6+3"


def test_parse_constitution_saving_throw():
    """Test DC saving throw parsing with ability expansion (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Poison",
        "description": ["DC 12 Constitution saving throw or be poisoned."],
    }

    result = parse_action_fields(action)

    assert result["dc"] == {
        "dc_value": 12,
        "dc_type": "Constitution",
        "dc_type_id": "con",
        "success_type": "none",
    }


def test_parse_damage_without_spacing():
    """Test damage parsing handles various spacing (v2.0 schema)."""
    from srd_builder.parse.parse_actions import parse_action_fields

    # Compact formatting
    action1 = {"name": "Test", "description": ["Hit: 10 (2d6+3) slashing damage."]}
    result1 = parse_action_fields(action1)
    assert result1["damage"][0]["dice"] == "2d6+3"

    # Spaced formatting
    action2 = {"name": "Test", "description": ["Hit: 10 (2d6 + 3) slashing damage."]}
    result2 = parse_action_fields(action2)
    assert result2["damage"][0]["dice"] == "2d6+3"

    # Extra spacing
    action3 = {"name": "Test", "description": ["Hit: 10 ( 2d6  +  3 ) slashing damage."]}
    result3 = parse_action_fields(action3)
    assert result3["damage"][0]["dice"] == "2d6+3"
