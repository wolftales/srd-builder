from __future__ import annotations

"""Index construction helpers for SRD entities."""

from collections import defaultdict
from typing import Any, Dict, Iterable

__all__ = ["build_monster_index", "build_indexes"]


def _stable_dict(values: Iterable[tuple[str, list[str]]]) -> Dict[str, list[str]]:
    return {key: ids for key, ids in values}


def build_monster_index(monsters: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical monster lookup tables."""

    by_name: Dict[str, str] = {}
    by_cr: defaultdict[str, list[str]] = defaultdict(list)
    by_type: defaultdict[str, list[str]] = defaultdict(list)
    by_size: defaultdict[str, list[str]] = defaultdict(list)

    for monster in monsters:
        monster_id = monster["id"]
        name = str(monster.get("name", "")).lower()
        cr = monster.get("challenge_rating", 0)
        mtype = str(monster.get("type", "unknown"))
        size = str(monster.get("size", "Medium"))

        by_name[name] = monster_id
        by_cr[str(cr)].append(monster_id)
        by_type[mtype].append(monster_id)
        by_size[size].append(monster_id)

    sorted_by_cr = _stable_dict(
        sorted(
            by_cr.items(),
            key=lambda item: float(item[0]) if _looks_numeric(item[0]) else 0.0,
        )
    )
    sorted_by_type = _stable_dict(sorted(by_type.items()))
    sorted_by_size = _stable_dict(sorted(by_size.items()))

    return {
        "monstersByName": by_name,
        "monstersByCR": sorted_by_cr,
        "monstersByType": sorted_by_type,
        "monstersBySize": sorted_by_size,
    }


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _build_entity_index(monsters: list[dict[str, Any]]) -> Dict[str, dict[str, str]]:
    index: Dict[str, dict[str, str]] = {}
    for monster in monsters:
        monster_id = monster["id"]
        index[monster_id] = {
            "type": "monster",
            "file": "monsters.json",
            "name": monster.get("name", ""),
        }
    return index


def build_indexes(monsters: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate monster and entity indexes for dataset output."""

    monster_indexes = build_monster_index(monsters)
    entity_index = _build_entity_index(monsters)

    return {
        "format_version": "v0.4.0",
        "monsters": monster_indexes,
        "entities": entity_index,
        "stats": {
            "total_monsters": len(monsters),
            "total_entities": len(entity_index),
            "unique_crs": len(monster_indexes["monstersByCR"]),
            "unique_types": len(monster_indexes["monstersByType"]),
            "unique_sizes": len(monster_indexes["monstersBySize"]),
        },
    }

