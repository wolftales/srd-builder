"""Tests for action field parsing."""


def test_parse_melee_weapon_attack():
    """Parse typical melee weapon attack."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Greataxe",
        "text": "Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 17 (2d12 + 4) slashing damage.",
    }

    result = parse_action_fields(action)

    assert result["attack_type"] == "melee_weapon"
    assert result["to_hit"] == 7
    assert result["reach"] == 5
    assert result["damage"] == {
        "average": 17,
        "dice": "2d12+4",
        "type": "slashing",
    }
    assert result["text"] == action["text"]  # Preserved


def test_parse_ranged_weapon_attack():
    """Parse ranged weapon attack with range."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Longbow",
        "text": "Ranged Weapon Attack: +4 to hit, range 150/600 ft., one target. Hit: 6 (1d8 + 2) piercing damage.",
    }

    result = parse_action_fields(action)

    assert result["attack_type"] == "ranged_weapon"
    assert result["to_hit"] == 4
    assert result["range"] == {"normal": 150, "long": 600}
    assert result["damage"] == {
        "average": 6,
        "dice": "1d8+2",
        "type": "piercing",
    }
    assert "reach" not in result


def test_parse_action_with_saving_throw():
    """Parse action with DC saving throw."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Breath Weapon",
        "text": "The dragon exhales fire in a 60-foot cone. Each creature in that area must make a DC 21 Dexterity saving throw, taking 63 (18d6) fire damage on a failed save, or half as much damage on a successful one.",
    }

    result = parse_action_fields(action)

    assert result["saving_throw"] == {
        "dc": 21,
        "ability": "dexterity",
    }
    assert result["damage"] == {
        "average": 63,
        "dice": "18d6",
        "type": "fire",
    }


def test_parse_action_multiple_damage_types():
    """Parse action with multiple damage instances."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Claw",
        "text": "Melee Weapon Attack: +14 to hit, reach 10 ft., one target. Hit: 17 (2d6 + 10) slashing damage plus 3 (1d6) fire damage.",
    }

    result = parse_action_fields(action)

    assert result["damage"] == {
        "average": 17,
        "dice": "2d6+10",
        "type": "slashing",
    }
    assert "damage_options" in result
    assert len(result["damage_options"]) == 2
    assert result["damage_options"][1] == {
        "average": 3,
        "dice": "1d6",
        "type": "fire",
    }


def test_parse_melee_spell_attack():
    """Parse melee spell attack."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Shocking Grasp",
        "text": "Melee Spell Attack: +5 to hit, reach 5 ft., one creature. Hit: 9 (2d8) lightning damage.",
    }

    result = parse_action_fields(action)

    assert result["attack_type"] == "melee_spell"
    assert result["to_hit"] == 5
    assert result["reach"] == 5


def test_parse_ranged_spell_attack():
    """Parse ranged spell attack."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Fire Bolt",
        "text": "Ranged Spell Attack: +7 to hit, range 120/480 ft., one target. Hit: 16 (3d10) fire damage.",
    }

    result = parse_action_fields(action)

    assert result["attack_type"] == "ranged_spell"
    assert result["to_hit"] == 7
    assert result["range"] == {"normal": 120, "long": 480}


def test_parse_negative_to_hit():
    """Parse action with negative to-hit modifier."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Weak Attack",
        "text": "Melee Weapon Attack: -1 to hit, reach 5 ft., one target. Hit: 1 (1d4 - 1) bludgeoning damage.",
    }

    result = parse_action_fields(action)

    assert result["to_hit"] == -1
    assert result["damage"]["dice"] == "1d4-1"


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
    """Parsing should add fields without removing existing ones."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Bite",
        "simple_name": "bite",
        "text": "Melee Weapon Attack: +10 to hit, reach 10 ft., one target. Hit: 17 (2d10 + 6) piercing damage.",
        "custom_field": "should be preserved",
    }

    result = parse_action_fields(action)

    assert result["name"] == "Bite"
    assert result["simple_name"] == "bite"
    assert result["custom_field"] == "should be preserved"
    assert result["attack_type"] == "melee_weapon"
    assert result["to_hit"] == 10


def test_parse_action_in_pipeline():
    """Test action parsing integrated into clean_monster_record."""
    from srd_builder.postprocess import clean_monster_record

    monster = {
        "id": "monster:test",
        "name": "Test Monster",
        "page": 1,
        "src": "SRD 5.1",
        "armor_class": 15,
        "hit_points": 50,
        "ability_scores": {"strength": 16},
        "actions": [
            {
                "name": "Slam",
                "simple_name": "slam",
                "text": "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 7 (1d8 + 3) bludgeoning damage.",
            }
        ],
    }

    result = clean_monster_record(monster)

    assert len(result["actions"]) == 1
    action = result["actions"][0]
    assert action["attack_type"] == "melee_weapon"
    assert action["to_hit"] == 5
    assert action["reach"] == 5
    assert action["damage"]["dice"] == "1d8+3"
    assert action["damage"]["type"] == "bludgeoning"


def test_parse_legendary_actions():
    """Test action parsing applies to legendary actions."""
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
                "text": "Melee Weapon Attack: +15 to hit, reach 20 ft., one target. Hit: 18 (2d8 + 9) bludgeoning damage.",
            }
        ],
    }

    result = clean_monster_record(monster)

    legendary = result["legendary_actions"][0]
    assert legendary["attack_type"] == "melee_weapon"
    assert legendary["to_hit"] == 15
    assert legendary["reach"] == 20


def test_parse_reactions():
    """Test action parsing applies to reactions."""
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
                "text": "Melee Weapon Attack: +8 to hit, reach 5 ft., one creature. Hit: 10 (2d6 + 3) slashing damage.",
            }
        ],
    }

    result = clean_monster_record(monster)

    reaction = result["reactions"][0]
    assert reaction["attack_type"] == "melee_weapon"
    assert reaction["to_hit"] == 8


def test_parse_constitution_saving_throw():
    """Test full ability name expansion from short form."""
    from srd_builder.parse.parse_actions import parse_action_fields

    action = {
        "name": "Poison",
        "text": "DC 12 Con saving throw or be poisoned.",
    }

    result = parse_action_fields(action)

    assert result["saving_throw"] == {
        "dc": 12,
        "ability": "constitution",
    }


def test_parse_damage_without_spacing():
    """Test damage parsing handles various spacing."""
    from srd_builder.parse.parse_actions import parse_action_fields

    # Compact formatting
    action1 = {"name": "Test", "text": "Hit: 10 (2d6+3) slashing damage."}
    result1 = parse_action_fields(action1)
    assert result1["damage"]["dice"] == "2d6+3"

    # Spaced formatting
    action2 = {"name": "Test", "text": "Hit: 10 (2d6 + 3) slashing damage."}
    result2 = parse_action_fields(action2)
    assert result2["damage"]["dice"] == "2d6+3"

    # Extra spacing
    action3 = {"name": "Test", "text": "Hit: 10 ( 2d6  +  3 ) slashing damage."}
    result3 = parse_action_fields(action3)
    assert result3["damage"]["dice"] == "2d6+3"
