from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_diseases import parse_disease_records
from srd_builder.postprocess import clean_disease_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_disease_dataset_matches_normalized_fixture() -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/diseases.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/diseases.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains disease sections from prose extraction
    sections = raw_data["sections"]

    # Parse: sections → unnormalized dicts
    parsed = parse_disease_records(sections)

    # Postprocess: normalize IDs and polish text
    processed = [clean_disease_record(d) for d in parsed]

    # Wrap with metadata
    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("disease")),
        "diseases": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")

    assert rendered == expected, "Disease dataset output doesn't match normalized fixture"
