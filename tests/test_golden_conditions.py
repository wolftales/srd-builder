from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_conditions import parse_condition_records
from srd_builder.postprocess import clean_condition_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_condition_dataset_matches_normalized_fixture() -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/conditions.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/conditions.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains condition sections from prose extraction
    sections = raw_data["sections"]

    # Parse: sections → unnormalized dicts
    parsed = parse_condition_records(sections)

    # Postprocess: normalize IDs and polish text
    processed = [clean_condition_record(c) for c in parsed]

    # Wrap with metadata
    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("condition")),
        "conditions": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")

    assert rendered == expected, "Condition dataset output doesn't match normalized fixture"
