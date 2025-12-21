"""Golden fixture test for spell dataset."""

from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_spells import parse_spell_records
from srd_builder.postprocess import clean_spell_record
from srd_builder.utils.metadata import meta_block


def test_spell_dataset_matches_normalized_fixture() -> None:
    """Test that parsing raw spells produces expected normalized output.

    This test ensures the spell parsing and postprocessing pipeline
    produces consistent, deterministic output matching our golden fixtures.
    """
    raw_path = Path("tests/fixtures/srd_5_1/raw/spells.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/spells.json")

    # Skip test if fixtures don't exist yet
    if not raw_path.exists():
        return
    if not expected_path.exists():
        return

    spells_raw = json.loads(raw_path.read_text(encoding="utf-8"))

    # Handle both array and object with "spells" key
    if isinstance(spells_raw, dict) and "spells" in spells_raw:
        spells_raw = spells_raw["spells"]
    elif not isinstance(spells_raw, list):
        spells_raw = [spells_raw]

    parsed = parse_spell_records(spells_raw)
    processed = [clean_spell_record(spell) for spell in parsed]

    document = {"_meta": meta_block("srd_5_1"), "items": processed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
