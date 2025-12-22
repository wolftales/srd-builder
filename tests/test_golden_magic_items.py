"""Golden fixture test for magic items dataset."""

from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_magic_items import parse_magic_items
from srd_builder.postprocess import clean_magic_item_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_magic_items_dataset_matches_normalized_fixture() -> None:
    """Test that parsing raw magic items produces expected normalized output.

    This test ensures the magic items parsing and postprocessing pipeline
    produces consistent, deterministic output matching our golden fixtures.
    """
    raw_path = Path("tests/fixtures/srd_5_1/raw/magic_items.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/magic_items.json")

    magic_items_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    # parse_magic_items extracts structure, returns dicts without IDs/normalization
    parsed = parse_magic_items({"items": magic_items_raw})
    # clean_magic_item_record applies normalization (IDs, text polish)
    processed = [clean_magic_item_record(item) for item in parsed]

    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("magic_item")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
