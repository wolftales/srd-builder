import json
from pathlib import Path


def test_monster_fixture_structure() -> None:
    raw = json.loads(Path("tests/fixtures/srd_5_1/raw/monsters.json").read_text())
    assert isinstance(raw, list) and raw
    for monster in raw:
        # Raw extraction has blocks, name, pages, markers
        assert "name" in monster and "blocks" in monster
