from __future__ import annotations

import json
from itertools import islice
from pathlib import Path

import pytest

MONSTER_DATA = Path("rulesets/srd_5_1/data/monsters.json")
REQUIRED_FIELDS = ["id", "name", "page", "src"]
SAMPLE_SIZE = 5


@pytest.mark.skipif(not MONSTER_DATA.exists(), reason="No SRD monster data present")
def test_monsters_json_sanity() -> None:
    monsters = json.loads(MONSTER_DATA.read_text(encoding="utf-8"))
    assert isinstance(monsters, list), "monsters.json should contain a list"
    assert monsters, "monsters.json should not be empty"

    for monster in islice(monsters, SAMPLE_SIZE):
        assert isinstance(monster, dict), "monster entries should be objects"
        missing = [field for field in REQUIRED_FIELDS if field not in monster]
        assert not missing, f"missing fields in monster entry: {missing}"
