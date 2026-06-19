from __future__ import annotations

import json
from pathlib import Path

from srd_builder.postprocess import clean_feature_record
from srd_builder.postprocess.ids import normalize_id
from srd_builder.utils.metadata import meta_block, read_schema_version

# Each fixture entry is hand-paired with its canonical owner because the
# raw fixture intentionally contains a sparse, hand-picked sample (one
# feature per family) rather than the full PDF stream the
# ``parse_features`` resolver expects.
_FIXTURE_OWNERS: dict[str, tuple[str, str]] = {
    "Rage": ("class", "barbarian"),
    "Evasion": ("class", "rogue"),
    "Languages": ("lineage", "tiefling"),
}


def test_feature_dataset_matches_normalized_fixture(assert_golden_matches) -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/features.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/features.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
    raw_features = raw_data["raw_features"]

    parsed = []
    for rf in raw_features:
        owner_kind, owner_simple = _FIXTURE_OWNERS[rf["name"]]
        simple_name = normalize_id(rf["name"])
        parsed.append(
            {
                "id": f"feature:{owner_simple}:{simple_name}",
                "name": rf["name"],
                "simple_name": simple_name,
                "owner_id": f"{owner_kind}:{owner_simple}",
                "page": rf["page"],
                "source": "SRD_CC_v5.1",
                "summary": rf["summary"],
                "text": rf["text"],
            }
        )

    processed = [clean_feature_record(f) for f in parsed]

    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("features")),
        "features": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    assert_golden_matches(rendered, expected_path)
