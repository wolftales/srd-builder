from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_poisons_table import parse_poisons_table
from srd_builder.postprocess import clean_poison_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_poison_dataset_matches_normalized_fixture() -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/poisons.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/poisons.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains poisons table and descriptions
    poisons_table = raw_data["poisons_table"]
    poison_descriptions = raw_data["poison_descriptions"]

    # Parse: table + descriptions → unnormalized dicts
    parsed = parse_poisons_table(poisons_table, descriptions=poison_descriptions)

    # Postprocess: normalize IDs and polish text
    processed = [clean_poison_record(p) for p in parsed]

    # Wrap with metadata
    document = {"_meta": meta_block("srd_5_1", read_schema_version("poison")), "items": processed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")

    assert rendered == expected, "Poison dataset output doesn't match normalized fixture"
