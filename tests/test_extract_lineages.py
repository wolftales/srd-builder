"""Tests for the lineage extractor (PDF -> raw structured data).

These tests pin the extractor's behavior against the actual SRD 5.1 PDF.
They are the safety net for the cutover that retires
`rulesets/srd_5_1/lineage_targets.py` in v0.27.0.

Why we compare against LINEAGE_DATA rather than literal fixture values:
LINEAGE_DATA is the legacy hand-curated shape that all downstream code
already consumes. By proving the extractor reproduces that shape (with
one documented PDF-fidelity correction), we know the cutover is safe.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srd_builder.extract.datasets.extract_lineages import extract_lineages
from srd_builder.rulesets.srd_5_1.lineage_targets import LINEAGE_DATA

PDF_PATH = Path("rulesets/srd_5_1/SRD_CC_v5.1.pdf")

# One deliberate divergence from the legacy hand-curated data: the PDF
# heading literally reads "Lightfoot" (only the parent race is named
# "Halfling"). The legacy author embellished it to "Lightfoot Halfling".
# The extractor is PDF-faithful; the cutover updates the consumer fixture.
_SUBRACE_NAME_OVERRIDES = {
    "Lightfoot Halfling": "Lightfoot",
}


@pytest.fixture(scope="module")
def extracted_lineages() -> list[dict]:
    assert PDF_PATH.exists(), f"Missing SRD PDF at {PDF_PATH}"
    return extract_lineages(PDF_PATH)["lineages"]


def test_extracts_nine_lineages_in_pdf_order(extracted_lineages: list[dict]) -> None:
    assert [r["name"] for r in extracted_lineages] == [r["name"] for r in LINEAGE_DATA]


def test_each_lineage_has_expected_page(extracted_lineages: list[dict]) -> None:
    expected = {r["name"]: r["page"] for r in LINEAGE_DATA}
    actual = {r["name"]: r["page"] for r in extracted_lineages}
    assert actual == expected


@pytest.mark.parametrize("expected", LINEAGE_DATA, ids=lambda r: r["name"])
def test_ability_modifiers_match(extracted_lineages: list[dict], expected: dict) -> None:
    ex = next(r for r in extracted_lineages if r["name"] == expected["name"])
    assert ex["ability_modifiers"] == expected["ability_modifiers"]


@pytest.mark.parametrize("expected", LINEAGE_DATA, ids=lambda r: r["name"])
def test_size_speed_match(extracted_lineages: list[dict], expected: dict) -> None:
    ex = next(r for r in extracted_lineages if r["name"] == expected["name"])
    assert ex["size"] == expected["size"], f"{expected['name']} size"
    assert ex["speed"] == expected["speed"], f"{expected['name']} speed"


@pytest.mark.parametrize("expected", LINEAGE_DATA, ids=lambda r: r["name"])
def test_languages_match(extracted_lineages: list[dict], expected: dict) -> None:
    ex = next(r for r in extracted_lineages if r["name"] == expected["name"])
    assert ex["languages"] == expected["languages"]


@pytest.mark.parametrize("expected", LINEAGE_DATA, ids=lambda r: r["name"])
def test_trait_names_match(extracted_lineages: list[dict], expected: dict) -> None:
    """Trait NAMES (not text) must match the hand-curated set exactly."""
    ex = next(r for r in extracted_lineages if r["name"] == expected["name"])
    expected_names = [t["name"] for t in expected["traits"]]
    actual_names = [t["name"] for t in ex["traits"]]
    assert actual_names == expected_names


@pytest.mark.parametrize("expected", LINEAGE_DATA, ids=lambda r: r["name"])
def test_subraces_match(extracted_lineages: list[dict], expected: dict) -> None:
    ex = next(r for r in extracted_lineages if r["name"] == expected["name"])
    expected_subraces = expected.get("subraces", [])
    actual_subraces = ex.get("subraces", [])
    assert len(actual_subraces) == len(expected_subraces), f"{expected['name']}: subrace count"
    for exp_sr, act_sr in zip(expected_subraces, actual_subraces, strict=True):
        canonical_name = _SUBRACE_NAME_OVERRIDES.get(exp_sr["name"], exp_sr["name"])
        assert act_sr["name"] == canonical_name
        assert act_sr["ability_modifiers"] == exp_sr["ability_modifiers"]
        exp_trait_names = [t["name"] for t in exp_sr["traits"]]
        act_trait_names = [t["name"] for t in act_sr["traits"]]
        assert act_trait_names == exp_trait_names


def test_no_structural_traits_in_traits_list(extracted_lineages: list[dict]) -> None:
    """ASI/Age/Alignment/Size/Speed/Languages must be lifted to top-level fields."""
    structural = {"Ability Score Increase", "Age", "Alignment", "Size", "Speed", "Languages"}
    for race in extracted_lineages:
        trait_names = {t["name"] for t in race["traits"]}
        assert structural.isdisjoint(trait_names), (
            f"{race['name']} has structural trait in traits list: {structural & trait_names}"
        )


def test_age_alignment_size_description_populated(extracted_lineages: list[dict]) -> None:
    """All 9 lineages should have non-empty age/alignment/size_description prose."""
    for race in extracted_lineages:
        assert race.get("age"), f"{race['name']}: missing age"
        assert race.get("alignment"), f"{race['name']}: missing alignment"
        assert race.get("size_description"), f"{race['name']}: missing size_description"
