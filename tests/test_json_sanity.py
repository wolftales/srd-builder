import json
from pathlib import Path


def test_monsters_json_loads():
    p = Path("schemas/monster.schema.json")
    assert p.exists(), "monster.schema.json missing"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "monster.schema.json should be a valid JSON object"
    assert "type" in data and data["type"] == "object", "monster.schema.json should define an object schema"
    assert "properties" in data, "monster.schema.json should define properties"
    for prop in ["id", "name", "page", "src", "armor_class", "hit_points", "ability_scores"]:
        assert prop in data["properties"], f"monster.schema.json is missing property: {prop}"
