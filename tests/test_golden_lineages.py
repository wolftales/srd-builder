from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_lineages import _build_lineage_record
from srd_builder.postprocess import clean_lineage_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_lineage_dataset_matches_normalized_fixture() -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/lineages.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/lineages.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains lineage target data
    lineage_data = raw_data["lineage_data"]

    # Parse: target data → unnormalized records
    parsed = [_build_lineage_record(ld) for ld in lineage_data]

    # Postprocess: normalize IDs and polish text
    processed = [clean_lineage_record(lin) for lin in parsed]

    # Wrap with metadata
    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("lineage")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")

    assert rendered == expected, "Lineage dataset output doesn't match normalized fixture"
