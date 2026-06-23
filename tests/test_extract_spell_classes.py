"""Tests for the spell-class extractor (PDF -> {class: [spell simple_names]}).

These tests pin the extractor's behavior against the actual SRD 5.1 PDF
by comparing it to a JSON snapshot of the retired
``rulesets/srd_5_1/spell_class_targets.py`` lists (see
``tests/fixtures/srd_5_1/spell_class_targets_snapshot.json``). The
snapshot is the safety net the v0.27.0 cutover retiring that module was
built against; do not introduce new consumers of it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from srd_builder.extract.datasets.extract_spell_classes import (
    build_spell_to_classes_map,
    extract_spell_classes,
)

PDF_PATH = Path("rulesets/srd_5_1/SRD_CC_v5.1.pdf")
_SNAPSHOT_PATH = Path("tests/fixtures/srd_5_1/spell_class_targets_snapshot.json")
SNAPSHOT: dict = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def extracted_class_spells(srd_5_1_pdf: Path) -> dict[str, list[str]]:
    return extract_spell_classes(srd_5_1_pdf)["class_spells"]


def test_extracts_eight_classes(extracted_class_spells: dict[str, list[str]]) -> None:
    assert sorted(extracted_class_spells.keys()) == [
        "bard",
        "cleric",
        "druid",
        "paladin",
        "ranger",
        "sorcerer",
        "warlock",
        "wizard",
    ]


@pytest.mark.parametrize(
    "cls",
    ["bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock", "wizard"],
)
def test_class_spell_list_matches_snapshot(
    extracted_class_spells: dict[str, list[str]], cls: str
) -> None:
    """Each class's extracted spell list must equal the snapshot exactly.

    Lists are compared as sets (order is PDF-walk order; both source and
    snapshot were extracted from the same walk, so order is in fact equal
    too, but membership is the contract).
    """
    expected = set(SNAPSHOT["class_spells"][cls])
    actual = set(extracted_class_spells[cls])
    assert actual == expected, (
        f"{cls}: extracted-only={sorted(actual - expected)}, "
        f"snapshot-only={sorted(expected - actual)}"
    )


def test_total_spell_count(extracted_class_spells: dict[str, list[str]]) -> None:
    total = sum(len(v) for v in extracted_class_spells.values())
    expected = sum(len(v) for v in SNAPSHOT["class_spells"].values())
    assert total == expected


def test_spell_to_classes_map_round_trips(
    extracted_class_spells: dict[str, list[str]],
) -> None:
    """``build_spell_to_classes_map`` inverts the class→spells dict."""
    spell_map = build_spell_to_classes_map(extracted_class_spells)
    # Spot-check well-known multi-class spells
    assert "cure_wounds" in spell_map
    assert set(spell_map["cure_wounds"]) >= {"bard", "cleric", "druid", "paladin", "ranger"}
    assert "fireball" in spell_map
    assert set(spell_map["fireball"]) == {"sorcerer", "wizard"}
    # Spot-check class-unique spells
    assert spell_map.get("eldritch_blast") == ["warlock"]
    assert spell_map.get("vicious_mockery") == ["bard"]
    # Each value must be sorted alphabetically
    for classes in spell_map.values():
        assert classes == sorted(classes)


def test_extractor_matches_snapshot_total(
    extracted_class_spells: dict[str, list[str]],
) -> None:
    """Inverted map size matches the snapshot's spell_classes dict."""
    extracted_map = build_spell_to_classes_map(extracted_class_spells)
    assert len(extracted_map) == len(SNAPSHOT["spell_classes"])
