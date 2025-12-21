def test_build_monster_index():
    from srd_builder.assemble.indexer import build_monster_index

    mons = [
        {"id": "monster:a", "name": "A", "challenge_rating": 1, "type": "fiend", "size": "Medium"},
        {"id": "monster:b", "name": "B", "challenge_rating": 1, "type": "fiend", "size": "Large"},
    ]
    idx = build_monster_index(mons)
    assert idx["by_name"]["a"] == "monster:a"
    assert set(idx["by_cr"]["1"]) == {"monster:a", "monster:b"}
