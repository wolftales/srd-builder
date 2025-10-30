from __future__ import annotations

import json
from pathlib import Path

from srd_builder import __version__
from srd_builder.parse_monsters import parse_monster_records
from srd_builder.postprocess import clean_monster_record


def _meta(ruleset: str) -> dict[str, str]:
    return {
        "ruleset": ruleset,
        "schema_version": "1.1.0",
        "source": "SRD_CC_v5.1",
        "build_report": "../build_report.json",
        "generated_by": f"srd-builder v{__version__}",
    }


def test_monster_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/monsters.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/monsters.json")

    monsters_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_monster_records(monsters_raw)
    processed = [clean_monster_record(monster) for monster in parsed]

    document = {"_meta": _meta("srd_5_1"), "items": processed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
