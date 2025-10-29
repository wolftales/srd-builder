from srd_builder.indexer import build_indexes

REQUIRED_FIELDS = {
    "page": "MM 1",
    "src": "MM",
    "armor_class": "12",
    "hit_points": "10 (3d8)",
    "ability_scores": {},
}


def test_build_indexes_records_conflicting_names() -> None:
    monsters = [
        {"id": "monster:alpha", "name": "Shadow", **REQUIRED_FIELDS},
        {"id": "monster:beta", "name": "shadow", **REQUIRED_FIELDS},
    ]

    result = build_indexes(sorted(monsters, key=lambda m: m["id"]))

    assert result["monsters"]["by_name"]["shadow"] == "monster:alpha"
    assert result["conflicts"]["by_name"]["shadow"] == ["monster:beta"]


def test_build_indexes_uses_fallback_identifier() -> None:
    monsters = [
        {"name": "Arcane Wisp", **REQUIRED_FIELDS},
    ]

    result = build_indexes(monsters)

    assert result["monsters"]["by_name"]["arcane wisp"] == "arcane_wisp"
    assert "conflicts" not in result
