from __future__ import annotations

from srd_builder.postprocess import (
    normalize_id,
    polish_text,
    split_legendary,
    standardize_challenge,
    structure_defenses,
)


def test_normalize_id_idempotent() -> None:
    assert normalize_id("adult_black_dragon") == "adult_black_dragon"
    assert normalize_id("Adult Black Dragon") == "adult_black_dragon"


def test_split_legendary_moves_cost_markers() -> None:
    monster = {
        "actions": [
            {
                "name": "Multiattack",
                "text": "The dragon makes three attacks.",
            },
            {
                "name": "Legendary Overview",
                "text": "The dragon can take 3 legendary actions, choosing from the options below.",
            },
            {
                "name": "Wing Attack (Costs 2 Actions)",
                "text": "The dragon beats its wings.",
            },
            {
                "name": "Tail Attack",
                "text": "Tail Attack (Costs 2 Actions).",
            },
        ]
    }

    split = split_legendary(monster)

    assert [action["name"] for action in split["actions"]] == [
        "Multiattack",
        "Legendary Overview",
    ]
    assert [action["name"] for action in split["legendary_actions"]] == [
        "Wing Attack (Costs 2 Actions)",
        "Tail Attack",
    ]


def test_structure_defenses_preserves_order_and_qualifiers() -> None:
    monster = {
        "damage_resistances": [
            "cold; fire from nonmagical attacks",
            "lightning",
        ],
        "damage_immunities": [
            "poison",
        ],
    }

    structured = structure_defenses(monster)

    assert structured["damage_resistances"] == [
        {"type": "cold"},
        {"type": "fire", "qualifier": "nonmagical"},
        {"type": "lightning"},
    ]
    assert structured["damage_immunities"] == [{"type": "poison"}]


def test_standardize_challenge_handles_fraction_and_numeric() -> None:
    monster = {"challenge_rating": "1/2"}
    assert standardize_challenge(monster)["challenge_rating"] == 0.5

    monster = {"challenge_rating": "5"}
    assert standardize_challenge(monster)["challenge_rating"] == 5

    monster = {"challenge_rating": 7.0}
    assert standardize_challenge(monster)["challenge_rating"] == 7


def test_polish_text_cleans_spacing_and_dice() -> None:
    text = "H  it:  10 (2d6 +  3)--and   keepsgoing."
    assert polish_text(text) == "Hit: 10 (2d6 + 3)—and keeps going."
