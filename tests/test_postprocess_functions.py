from __future__ import annotations

from typing import Any

from srd_builder.postprocess import (
    normalize_id,
    polish_text,
    split_legendary,
    standardize_challenge,
    structure_defenses,
)
from srd_builder.postprocess.text import clean_text


def test_normalize_id_idempotent() -> None:
    assert normalize_id("adult_black_dragon") == "adult_black_dragon"
    assert normalize_id("Adult Black Dragon") == "adult_black_dragon"


def test_split_legendary_moves_cost_markers() -> None:
    monster = {
        "actions": [
            {
                "name": "Multiattack",
                "description": ["The dragon makes three attacks."],
            },
            {
                "name": "Legendary Overview",
                "description": [
                    "The dragon can take 3 legendary actions, choosing from the options below."
                ],
            },
            {
                "name": "Wing Attack (Costs 2 Actions)",
                "description": ["The dragon beats its wings."],
            },
            {
                "name": "Tail Attack",
                "description": ["Tail Attack (Costs 2 Actions)."],
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
    monster: dict[str, Any] = {"challenge_rating": "1/2"}
    assert standardize_challenge(monster)["challenge_rating"] == 0.5

    monster = {"challenge_rating": "5"}
    assert standardize_challenge(monster)["challenge_rating"] == 5

    monster = {"challenge_rating": 7.0}
    assert standardize_challenge(monster)["challenge_rating"] == 7


def test_polish_text_cleans_spacing_and_dice() -> None:
    text = "H  it:  10 (2d6 +  3)--and   keepsgoing."
    assert polish_text(text) == "Hit: 10 (2d6 + 3)—and keeps going."


def test_polish_text_stitches_pdf_line_break_hyphens() -> None:
    # Compound words broken across PDF lines come through whitespace
    # normalization as ``word- word`` and must be re-joined.
    assert polish_text("a two- handed weapon") == "a two-handed weapon"
    assert polish_text("for well- being") == "for well-being"
    assert polish_text("Strength- based attack") == "Strength-based attack"


def test_polish_text_preserves_suspended_hyphen() -> None:
    # ``long- and short-range`` is intentional grammar, not a line break.
    assert polish_text("long- and short-range") == "long- and short-range"


def test_clean_text_stitches_pdf_line_break_hyphens() -> None:
    # Same fix applies at the clean_text layer (spells flow through here).
    assert clean_text("a foot-\nradius sphere") == "a foot-radius sphere"
    assert clean_text("a one- word command") == "a one-word command"


def test_clean_text_preserves_suspended_hyphen() -> None:
    assert clean_text("pre- or post-combat") == "pre- or post-combat"


def test_polish_text_stitches_digit_letter_compounds() -> None:
    # Dimensional / temporal compounds: ``10- foot``, ``6- second``,
    # ``24- hour``. PDF line wrap splits these the same way as letter-
    # letter compounds.
    assert polish_text("a 10- foot radius") == "a 10-foot radius"
    assert polish_text("a 6- second span of time") == "a 6-second span of time"
    assert polish_text("over a 24- hour period") == "over a 24-hour period"


def test_polish_text_stitches_dimensional_chains() -> None:
    # ``foot- by- 5- foot`` is the worst-case multi-token PDF dimensional
    # expression. After stitching both letter-letter and letter-digit /
    # digit-letter, it collapses to ``foot-by-5-foot``.
    assert polish_text("a 3- foot- by- 5- foot window") == "a 3-foot-by-5-foot window"


def test_polish_text_stitches_title_case_compounds() -> None:
    # Monster trait names: ``Two-Headed``, ``Sure-Footed``.
    assert polish_text("Two- Headed") == "Two-Headed"
    assert polish_text("Sure- Footed") == "Sure-Footed"


def test_polish_text_stitches_single_letter_appendix_refs() -> None:
    # ``PH-A`` is the appendix reference in the SRD rules dataset.
    assert polish_text("see appendix PH- A") == "see appendix PH-A"


def test_polish_text_preserves_suspended_hyphen_with_digit_leader() -> None:
    # ``5- and 10-foot`` is the digit-leader form of the suspended hyphen.
    assert polish_text("a 5- and 10-foot cone") == "a 5- and 10-foot cone"
