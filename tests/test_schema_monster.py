from __future__ import annotations

import json
from itertools import islice
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

MONSTER_DATA = Path("rulesets/srd_5_1/data/monsters.json")
SCHEMA_PATH = Path("schemas/monster.schema.json")
SAMPLE_SIZE = 5


@pytest.mark.skipif(not MONSTER_DATA.exists(), reason="No SRD monster data present")
def test_monsters_validate_against_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    monsters = json.loads(MONSTER_DATA.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema)

    for monster in islice(monsters, SAMPLE_SIZE):
        validator.validate(monster)
