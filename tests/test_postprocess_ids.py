def test_unify_simple_name_updates_monster_and_children():
    from srd_builder.postprocess import unify_simple_name

    monster = {
        "id": "monster:temp",
        "name": "Solar.",
        "simple_name": "Solar.",
        "abilities": [{"name": "Angelic Weapons.", "description": "Sheds bright light."}],
        "actions": [{"name": "Healing Touch.", "description": "Magical healing."}],
    }

    patched = unify_simple_name(monster)

    assert patched["name"] == "Solar"
    assert patched["simple_name"] == "solar"
    assert patched["id"] == "monster:solar"
    assert patched["abilities"][0]["simple_name"] == "angelic_weapons"
    assert patched["actions"][0]["simple_name"] == "healing_touch"
