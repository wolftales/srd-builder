from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_conditions import parse_condition_records
from srd_builder.postprocess.engine import clean_records
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_condition_dataset_matches_normalized_fixture(assert_golden_matches) -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/conditions.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/conditions.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains condition sections from prose extraction
    sections = raw_data["sections"]

    # Parse: sections → unnormalized dicts
    parsed = parse_condition_records(sections, "srd_5_1")

    # Postprocess: normalize IDs and polish text
    processed = clean_records(parsed, "condition")

    # Wrap with metadata. As of v0.30.0 Phase 2, the top-level array key is
    # "items" for every dataset (was "conditions" here historically).
    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("condition")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    assert_golden_matches(rendered, expected_path)
