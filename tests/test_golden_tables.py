from __future__ import annotations

import json
from pathlib import Path

from srd_builder.postprocess import clean_table_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_table_dataset_matches_normalized_fixture() -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/tables.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/tables.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains table extraction output
    raw_tables = raw_data["raw_tables"]

    # Simulate parse_single_table output
    parsed = []
    for rt in raw_tables:
        parsed.append(
            {
                "name": rt["name"],
                "page": rt["page"],
                "source": "SRD 5.1",
                "headers": rt["headers"],
                "rows": rt["rows"],
            }
        )

    # Postprocess: normalize IDs and polish text
    processed = [clean_table_record(t) for t in parsed]

    # Wrap with metadata
    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("table")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")

    assert rendered == expected, "Table dataset output doesn't match normalized fixture"
