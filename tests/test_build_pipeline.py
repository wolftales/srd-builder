import json
from pathlib import Path


def _raw_monsters_fixture() -> list[dict[str, object]]:
    return [
        {
            "name": "Aboleth",
            "size": "Large",
            "type": "aberration",
            "alignment": "lawful evil",
            "armor_class": "17 (natural armor)",
            "hit_points": "135 (18d10 + 36)",
            "speed": "10 ft., swim 40 ft.",
            "stats": {
                "str": "21",
                "dex": "9",
                "con": "15",
                "int": "18",
                "wis": "15",
                "cha": "18",
            },
            "saving_throws": "Con +6, Int +8, Wis +6",
            "skills": "History +12, Perception +10",
            "abilities": [
                {"name": "Amphibious", "description": "The aboleth can breathe air and water."}
            ],
            "actions": [
                {
                    "name": "Multiattack",
                    "description": "The aboleth makes three tentacle attacks.",
                },
                {
                    "name": "Tentacle",
                    "description": "Melee Weapon Attack: +9 to hit, reach 10 ft., one target.",
                },
                {
                    "name": "Legendary Actions",
                    "description": "The aboleth can take 3 legendary actions, choosing from the options below.",
                },
                {
                    "name": "Tail Swipe (Costs 2 Actions)",
                    "description": "The aboleth makes one tail attack.",
                },
            ],
            "challenge": "10 (5,900 XP)",
            "senses": "darkvision 120 ft., passive Perception 20",
            "damage_resistances": "cold; bludgeoning, piercing, and slashing from nonmagical attacks",
            "damage_immunities": "",
            "condition_immunities": "",
        },
        {
            "name": "Goblin",
            "size": "Small",
            "type": "humanoid",
            "alignment": "neutral evil",
            "armor_class": "15 (leather armor)",
            "hit_points": "7 (2d6)",
            "speed": "30 ft.",
            "stats": {
                "str": "8",
                "dex": "14",
                "con": "10",
                "int": "10",
                "wis": "8",
                "cha": "8",
            },
            "saving_throws": "Dex +2",
            "skills": "Stealth +6",
            "abilities": [
                {"name": "Nimble Escape", "description": "The goblin can take the Disengage or Hide action as a bonus action."}
            ],
            "actions": [
                {
                    "name": "Scimitar",
                    "description": "Melee Weapon Attack: +4 to hit, reach 5 ft., one target.",
                }
            ],
            "challenge": "1/4 (50 XP)",
            "senses": "darkvision 60 ft., passive Perception 9",
            "damage_resistances": "",
            "damage_immunities": "",
            "condition_immunities": "",
        },
    ]


def test_build_pipeline(tmp_path, monkeypatch):
    from srd_builder.build import build
    import sys
    import types

    class _DummyValidator:
        def __init__(self, _schema):
            pass

        def validate(self, _instance):
            return None

    monkeypatch.setitem(sys.modules, 'jsonschema', types.SimpleNamespace(Draft202012Validator=_DummyValidator))

    import srd_builder.validate as validate_module

    ruleset = "srd_5_1"
    rulesets_root = tmp_path / "rulesets"
    raw_dir = rulesets_root / ruleset / "raw"
    raw_dir.mkdir(parents=True)
    raw_file = raw_dir / "monsters.json"
    raw_file.write_text(json.dumps(_raw_monsters_fixture(), indent=2), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    out_dir = rulesets_root
    report_path = build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert report_path.exists()

    data_dir = out_dir / ruleset / "data"
    monsters_file = data_dir / "monsters.json"
    index_file = data_dir / "index.json"

    assert monsters_file.exists()
    assert index_file.exists()

    first_monsters = monsters_file.read_bytes()
    first_index = index_file.read_bytes()

    build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert first_monsters == monsters_file.read_bytes()
    assert first_index == index_file.read_bytes()

    monkeypatch.setattr(validate_module, "RULESETS_DIR", out_dir)
    count = validate_module.validate_monsters(ruleset)
    assert count == len(_raw_monsters_fixture())
