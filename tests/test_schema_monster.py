from __future__ import annotations

import json
from itertools import islice
from pathlib import Path

import pytest

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Draft202012Validator = None

MONSTER_DATA = Path("dist/srd_5_1/monsters.json")
SCHEMA_PATH = Path("schemas/monster.schema.json")
SAMPLE_SIZE = 5


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not installed")
@pytest.mark.skipif(not MONSTER_DATA.exists(), reason="No SRD monster data present")
def test_monsters_validate_against_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = json.loads(MONSTER_DATA.read_text(encoding="utf-8"))
    monsters = document.get("items", []) if isinstance(document, dict) else []

    validator = Draft202012Validator(schema)

    for monster in islice(monsters, SAMPLE_SIZE):
        validator.validate(monster)
