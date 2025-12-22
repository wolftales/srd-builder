def test_split_legendary_moves_actions():
    from srd_builder.postprocess import (
        polish_text_fields,
        rename_abilities_to_traits,
        split_legendary,
    )

    monster = {
        "name": "Aboleth",
        "actions": [
            {
                "name": "Enslave",
                "description": [
                    "The aboleth can take 3 legendary actions, choosing from the options below."
                ],
            },
            {
                "name": "Tail Swipe (Costs 2 Actions)",
                "description": ["Tail attack dealing bludgeoning damage."],
            },
        ],
    }

    renamed = rename_abilities_to_traits(monster)
    split = split_legendary(renamed)
    polished = polish_text_fields(split)

    assert len(polished["actions"]) == 1
    assert len(polished["legendary_actions"]) == 1
    # Check description array (new format)
    assert "legendary actions" not in " ".join(polished["actions"][0]["description"]).lower()
