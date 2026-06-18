"""Tests for the class extractor (PDF -> raw structured data).

These tests pin the extractor's behavior against the actual SRD 5.1 PDF
by comparing it to a JSON snapshot of the (DISPUTED) hand-curated
``CLASS_DATA`` list (see
``tests/fixtures/srd_5_1/class_targets_snapshot.json``). The snapshot
is the safety net the retirement cutover for
``rulesets/srd_5_1/class_targets.py`` is being built against; do not
introduce new consumers of it.

The extractor is grown incrementally (one field group per commit), so
each test marked ``# step N`` only runs once the extractor reaches that
field. Earlier tests must keep passing as later commits land.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from srd_builder.extract.datasets.extract_classes import extract_classes

PDF_PATH = Path("rulesets/srd_5_1/SRD_CC_v5.1.pdf")
_SNAPSHOT_PATH = Path("tests/fixtures/srd_5_1/class_targets_snapshot.json")
CLASS_DATA: list[dict] = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def extracted_classes() -> list[dict]:
    assert PDF_PATH.exists(), f"Missing SRD PDF at {PDF_PATH}"
    return extract_classes(PDF_PATH)["classes"]


# ---------------------------------------------------------------------------
# Step 1 — class discovery
# ---------------------------------------------------------------------------


def test_extracts_twelve_classes_in_pdf_order(extracted_classes: list[dict]) -> None:
    assert [c["name"] for c in extracted_classes] == [c["name"] for c in CLASS_DATA]


def test_each_class_has_expected_simple_name(extracted_classes: list[dict]) -> None:
    expected = {c["name"]: c["simple_name"] for c in CLASS_DATA}
    actual = {c["name"]: c["simple_name"] for c in extracted_classes}
    assert actual == expected


def test_each_class_has_expected_page(extracted_classes: list[dict]) -> None:
    expected = {c["name"]: c["page"] for c in CLASS_DATA}
    actual = {c["name"]: c["page"] for c in extracted_classes}
    assert actual == expected


def test_source_pages_label() -> None:
    assert extract_classes(PDF_PATH)["source_pages"] == "8-55"


# ---------------------------------------------------------------------------
# Step 2 — hit_die / primary_abilities / saving_throws / proficiencies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("expected", CLASS_DATA, ids=lambda c: c["name"])
def test_hit_die_matches_snapshot(extracted_classes: list[dict], expected: dict) -> None:
    ex = next(c for c in extracted_classes if c["name"] == expected["name"])
    assert ex["hit_die"] == expected["hit_die"]


@pytest.mark.parametrize("expected", CLASS_DATA, ids=lambda c: c["name"])
def test_primary_abilities_matches_snapshot(extracted_classes: list[dict], expected: dict) -> None:
    ex = next(c for c in extracted_classes if c["name"] == expected["name"])
    assert ex["primary_abilities"] == expected["primary_abilities"]


@pytest.mark.parametrize("expected", CLASS_DATA, ids=lambda c: c["name"])
def test_saving_throws_match_snapshot(extracted_classes: list[dict], expected: dict) -> None:
    ex = next(c for c in extracted_classes if c["name"] == expected["name"])
    assert ex["saving_throw_proficiencies"] == expected["saving_throw_proficiencies"]


@pytest.mark.parametrize("expected", CLASS_DATA, ids=lambda c: c["name"])
def test_proficiencies_match_snapshot(extracted_classes: list[dict], expected: dict) -> None:
    ex = next(c for c in extracted_classes if c["name"] == expected["name"])
    assert ex["proficiencies"] == expected["proficiencies"]


# ---------------------------------------------------------------------------
# Step 3 — features + subclasses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("expected", CLASS_DATA, ids=lambda c: c["name"])
def test_features_match_snapshot(extracted_classes: list[dict], expected: dict) -> None:
    ex = next(c for c in extracted_classes if c["name"] == expected["name"])
    assert ex["features"] == expected["features"]


@pytest.mark.parametrize("expected", CLASS_DATA, ids=lambda c: c["name"])
def test_subclasses_match_snapshot(extracted_classes: list[dict], expected: dict) -> None:
    ex = next(c for c in extracted_classes if c["name"] == expected["name"])
    assert ex["subclasses"] == expected["subclasses"]


# ---------------------------------------------------------------------------
# Step 4 — spellcasting block (8 caster classes; absent on the other 4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("expected", CLASS_DATA, ids=lambda c: c["name"])
def test_spellcasting_matches_snapshot(extracted_classes: list[dict], expected: dict) -> None:
    ex = next(c for c in extracted_classes if c["name"] == expected["name"])
    if "spellcasting" in expected:
        assert ex.get("spellcasting") == expected["spellcasting"]
    else:
        assert "spellcasting" not in ex, (
            f"{expected['name']} should NOT have a spellcasting block, got "
            f"{ex.get('spellcasting')!r}"
        )
