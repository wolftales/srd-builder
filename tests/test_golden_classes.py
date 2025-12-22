from __future__ import annotations

import json
from pathlib import Path

from srd_builder.postprocess import clean_class_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_class_dataset_matches_normalized_fixture() -> None:
    """Test that parse + postprocess produces expected normalized output."""
    raw_path = Path("tests/fixtures/srd_5_1/raw/classes.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/classes.json")

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains class target data
    class_data = raw_data["class_data"]

    # Simulate parse_classes output
    parsed = []
    for rc in class_data:
        parsed.append(
            {
                "name": rc["name"],
                "description": rc["description"],
                "hit_die": rc["hit_die"],
                "primary_ability": rc["primary_ability"],
                "saving_throw_proficiencies": rc["saving_throw_proficiencies"],
                "page": rc["page"],
                "source": "SRD 5.1",
            }
        )

    # Postprocess: normalize IDs and polish text
    processed = [clean_class_record(c) for c in parsed]

    # Wrap with metadata
    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("class")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")

    assert rendered == expected, "Class dataset output doesn't match normalized fixture"
