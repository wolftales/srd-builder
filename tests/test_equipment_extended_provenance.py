"""Tests for the structured `_provenance` block on extended equipment items.

`equipment_extended.py` is a legitimate hand-curated module
(items referenced by SRD packs or monster stat blocks but absent
from SRD equipment tables). Every extended item must carry a
structured `_provenance` block — replacing the prior free-text
`_note` field — so downstream consumers can filter inferred
from PDF-extracted records.
"""

from __future__ import annotations

from srd_builder.assemble.equipment_extended import (
    EXTENDED_EQUIPMENT,
    get_extended_equipment,
)

_REQUIRED_KEYS = {"source", "reason", "referenced_by", "module", "estimates"}
_VALID_REASONS = {"pack_cross_reference", "monster_cross_reference"}
_VALID_ESTIMATES = {"cost", "weight"}


def test_every_extended_item_has_provenance_block() -> None:
    for item in EXTENDED_EQUIPMENT:
        assert "_provenance" in item, f"{item['id']} missing _provenance"
        assert "_note" not in item, f"{item['id']} still has legacy _note field"


def test_provenance_block_shape_is_uniform() -> None:
    for item in EXTENDED_EQUIPMENT:
        prov = item["_provenance"]
        assert set(prov.keys()) == _REQUIRED_KEYS, (
            f"{item['id']} provenance keys {set(prov.keys())} != {_REQUIRED_KEYS}"
        )
        assert prov["source"] == "inferred"
        assert prov["reason"] in _VALID_REASONS
        assert isinstance(prov["referenced_by"], str) and prov["referenced_by"]
        assert prov["module"] == "equipment_extended.py"
        assert isinstance(prov["estimates"], list)
        assert set(prov["estimates"]) <= _VALID_ESTIMATES


def test_pack_referenced_items_estimate_cost_and_weight() -> None:
    pack_items = [
        i for i in EXTENDED_EQUIPMENT if i["_provenance"]["reason"] == "pack_cross_reference"
    ]
    assert len(pack_items) == 8
    for item in pack_items:
        assert item["_provenance"]["estimates"] == ["cost", "weight"]
        assert item["_provenance"]["referenced_by"].endswith("'s Pack")


def test_monster_referenced_natural_armor_estimates_nothing() -> None:
    monster_items = [
        i for i in EXTENDED_EQUIPMENT if i["_provenance"]["reason"] == "monster_cross_reference"
    ]
    assert len(monster_items) == 1
    item = monster_items[0]
    assert item["id"] == "item:natural_armor"
    assert item["_provenance"]["estimates"] == []
    assert item["_provenance"]["referenced_by"] == "monster_stat_blocks"


def test_get_extended_equipment_preserves_provenance() -> None:
    items = get_extended_equipment("SRD_CC_v5.1")
    assert len(items) == len(EXTENDED_EQUIPMENT)
    for item in items:
        assert "_provenance" in item
        assert item["source"] == "SRD_CC_v5.1 (extended)"
