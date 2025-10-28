import json
from pathlib import Path

from jsonschema import validate


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_monsters(data_dir: Path, schema_dir: Path):
    monsters = load_json(data_dir / "monsters.json")
    schema = load_json(schema_dir / "monster.schema.json")
    for m in monsters:
        validate(instance=m, schema=schema)
