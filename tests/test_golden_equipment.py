from __future__ import annotations

import json
from pathlib import Path

from srd_builder.parse.parse_equipment import parse_equipment_records
from srd_builder.postprocess import clean_equipment_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_equipment_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/equipment.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/equipment.json")

    equipment_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_equipment_records(equipment_raw)
    processed = [clean_equipment_record(item) for item in parsed]

    document = {
        "_meta": meta_block("srd_5_1", read_schema_version("equipment")),
        "items": processed,
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
