import pytest

from srd_builder.postprocess import dedup_defensive_lists, prune_empty_fields


@pytest.fixture
def base_monster() -> dict:
    return {
        "id": "monster:test",
        "name": "Test Monster",
        "page": "MM 1",
        "src": "MM",
        "armor_class": "12",
        "hit_points": "10 (3d8)",
        "ability_scores": {},
    }


def test_prune_empty_fields_skips_required_and_drops_optional(base_monster: dict) -> None:
    monster = {
        **base_monster,
        "traits": [],
        "legendary_actions": [],
        "condition_immunities": [],
        "damage_immunities": [],
        "summary": " ",
        "actions": [],
    }

    pruned = prune_empty_fields(monster)

    assert "traits" not in pruned
    assert "legendary_actions" not in pruned
    assert "condition_immunities" not in pruned
    assert "damage_immunities" not in pruned
    assert "summary" not in pruned
    assert "actions" in pruned
    for field in ("id", "name", "page", "src", "armor_class", "hit_points", "ability_scores"):
        assert field in pruned


def test_dedup_defensive_lists_preserves_first_occurrence(base_monster: dict) -> None:
    monster = {
        **base_monster,
        "damage_resistances": [
            {"type": "Fire", "qualifier": "Nonmagical"},
            {"type": "fire", "qualifier": "nonmagical"},
            {"type": "Cold"},
            {"type": " cold "},
        ],
        "damage_immunities": [
            {"type": "Lightning"},
            {"type": "LIGHTNING"},
        ],
        "condition_immunities": [
            {"type": "Charmed"},
            {"type": "charmed"},
            {"type": "Paralyzed", "qualifier": "While in Sunlight"},
            {"type": "Paralyzed", "qualifier": "while in sunlight"},
        ],
    }

    deduped = dedup_defensive_lists(monster)

    assert deduped["damage_resistances"] == [
        {"type": "fire", "qualifier": "nonmagical"},
        {"type": "cold"},
    ]
    assert deduped["damage_immunities"] == [{"type": "lightning"}]
    assert deduped["condition_immunities"] == [
        {"type": "charmed"},
        {"type": "paralyzed", "qualifier": "while in sunlight"},
    ]
