import json
from pathlib import Path


def test_monsters_json_loads():
    p = Path("rulesets/srd_5_1/data/monsters.json")
    assert p.exists(), "monsters.json missing"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, list) and data, "monsters.json should be non-empty list"
    for row in data[:5]:
        assert "id" in row and "name" in row and "page" in row
