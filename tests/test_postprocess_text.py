def test_polish_text_fields_cleans_boilerplate_and_spacing():
    from srd_builder.postprocess import polish_text_fields

    monster = {
        "summary": "H it:10.Only one legendary action option can be used at a time.",
        "actions": [
            {
                "name": "Tail",
                "text": "Hit:10 (2d6 + 5) bludgeoning. The dragon can take three legendary actions at the end of another creature's turn.",
            }
        ],
        "legendary_actions": [{"name": "Wing Attack.", "text": "H it:10 (2d6 + 5) damage."}],
    }

    polished = polish_text_fields(monster)

    assert polished["summary"].startswith("Hit: 10")
    assert "legendary actions" not in polished["actions"][0]["text"].lower()
    assert polished["legendary_actions"][0]["name"] == "Wing Attack"
    assert "2d6+5" in polished["legendary_actions"][0]["text"]
