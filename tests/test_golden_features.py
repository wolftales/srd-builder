from __future__ import annotations

import json
from pathlib import Path

from srd_builder.postprocess import clean_feature_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_feature_dataset_matches_normalized_fixture() -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/features.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/features.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains feature extraction output
    raw_features = raw_data["raw_features"]

    # Simulate parse_features output
    parsed = []
    for rf in raw_features:
        parsed.append(
            {
                "name": rf["name"],
                "page": rf["page"],
                "source": "SRD 5.1",
                "summary": rf["summary"],
                "text": rf["text"],
            }
        )

    # Postprocess: normalize IDs and polish text
    processed = [clean_feature_record(f) for f in parsed]

    # Wrap with metadata
    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("features")),
        "features": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")

    assert rendered == expected, "Feature dataset output doesn't match normalized fixture"
