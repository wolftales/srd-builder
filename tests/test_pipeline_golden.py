from __future__ import annotations

import json
from pathlib import Path

from srd_builder.indexer import build_indexes
from srd_builder.parse_monsters import parse_monster_records
from srd_builder.postprocess import clean_monster_record


def test_monster_pipeline_matches_golden_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/monsters.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/monsters.json")

    monsters_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_monster_records(monsters_raw)
    processed = [clean_monster_record(monster) for monster in parsed]

    index_blob = build_indexes(processed)
    assert index_blob["stats"]["total_monsters"] == len(processed)

    rendered = json.dumps(processed, indent=2, sort_keys=True) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
