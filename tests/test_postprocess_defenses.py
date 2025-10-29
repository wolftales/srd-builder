def test_structure_defenses_normalizes_strings():
    from srd_builder.postprocess import structure_defenses

    monster = {
        "damage_resistances": ["fire, cold; bludgeoning from nonmagical attacks"],
        "damage_immunities": ["poison"],
        "damage_vulnerabilities": [],
        "condition_immunities": ["Charmed", {"type": "frightened"}],
    }

    structured = structure_defenses(monster)

    assert structured["damage_resistances"] == [
        {"type": "fire"},
        {"type": "cold"},
        {"type": "bludgeoning", "qualifier": "nonmagical"},
    ]
    assert structured["damage_immunities"] == [{"type": "poison"}]
    assert structured["condition_immunities"] == [
        {"type": "charmed"},
        {"type": "frightened"},
    ]
