from __future__ import annotations

import json
from pathlib import Path

from srd_builder import __version__
from srd_builder.constants import SCHEMA_VERSION
from srd_builder.parse_equipment import parse_equipment_records
from srd_builder.postprocess import clean_equipment_record


def _meta(ruleset: str) -> dict[str, str]:
    return {
        "ruleset": ruleset,
        "schema_version": SCHEMA_VERSION,
        "source": "SRD_CC_v5.1",
        "build_report": "./build_report.json",
        "generated_by": f"srd-builder v{__version__}",
    }


def test_equipment_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/equipment.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/equipment.json")

    equipment_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_equipment_records(equipment_raw)
    processed = [clean_equipment_record(item) for item in parsed]

    document = {"_meta": _meta("srd_5_1"), "items": processed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
