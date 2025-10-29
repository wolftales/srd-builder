import json
from pathlib import Path


def test_monster_fixture_structure() -> None:
    raw = json.loads(Path("tests/fixtures/srd_5_1/raw/monsters.json").read_text())
    assert isinstance(raw, list) and raw
    for monster in raw:
        assert "name" in monster and "cr" in monster and "ac" in monster
