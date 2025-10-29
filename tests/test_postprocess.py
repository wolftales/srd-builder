def test_clean_monster_record_basic():
    from srd_builder.postprocess import clean_monster_record

    m = {
        "id": "monster:test",
        "name": "Solar.",
        "traits": [],
        "actions": [
            {
                "name": "Healing Touch.",
                "text": "H it: 10 (2d6 + 3). The creature can take 3 legendary actions...",
            }
        ],
        "damage_resistances": [
            "radiant",
            "bludgeoning, piercing, and slashing from nonmagical attacks",
        ],
    }
    out = clean_monster_record(m)
    assert out["name"] == "Solar"
    assert out["simple_name"] == "solar"
    assert "legendary actions" not in out["actions"][0]["text"].lower()
    assert any(
        x.get("type") == "piercing" and x.get("qualifier") == "nonmagical"
        for x in out["damage_resistances"]
    )
