"""Index construction helpers for SRD entities."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from srd_builder.postprocess import normalize_id

__all__ = ["build_monster_index", "build_indexes"]


def _stable_dict(values: Iterable[tuple[str, list[str]]]) -> dict[str, list[str]]:
    return {key: ids for key, ids in values}


def fallback_id(monster: dict[str, Any]) -> str:
    """Best-effort identifier for monsters missing explicit IDs."""

    if monster_id := monster.get("id"):
        return str(monster_id)
    if simple_name := monster.get("simple_name"):
        return str(simple_name)
    name = monster.get("name")
    if not isinstance(name, str):
        raise KeyError("name")
    return normalize_id(name)


def _build_by_name_map(
    monsters: Iterable[dict[str, Any]],
    *,
    display_normalizer: Callable[[str], str] | None = None,
) -> tuple[dict[str, str], dict[str, list[str]]]:
    by_name: dict[str, str] = {}
    conflicts: dict[str, list[str]] = {}
    for monster in monsters:
        name = str(monster.get("name", ""))
        normalized = display_normalizer(name) if display_normalizer else None
        key = (normalized or name).lower()
        monster_id = fallback_id(monster)
        existing = by_name.get(key)
        if existing is not None and existing != monster_id:
            conflicts.setdefault(key, []).append(monster_id)
            continue
        if key in by_name:
            # Same identifier encountered; skip without recording conflict.
            continue
        by_name[key] = monster_id
    sorted_conflicts = {key: sorted(ids) for key, ids in sorted(conflicts.items())}
    return dict(sorted(by_name.items())), sorted_conflicts


def build_monster_index(monsters: list[dict[str, Any]]) -> dict[str, Any]:
    """Build canonical monster lookup tables."""

    by_name, _ = _build_by_name_map(monsters)
    by_cr: defaultdict[str, list[str]] = defaultdict(list)
    by_type: defaultdict[str, list[str]] = defaultdict(list)
    by_size: defaultdict[str, list[str]] = defaultdict(list)

    for monster in monsters:
        monster_id = fallback_id(monster)
        cr = monster.get("challenge_rating", 0)
        mtype = str(monster.get("type", "unknown"))
        size = str(monster.get("size", "Medium"))

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

    for mapping in (sorted_by_cr, sorted_by_type, sorted_by_size):
        for key, ids in mapping.items():
            mapping[key] = sorted(ids)

    return {
        "by_name": by_name,
        "by_cr": sorted_by_cr,
        "by_type": sorted_by_type,
        "by_size": sorted_by_size,
    }


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _build_entity_index(monsters: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for monster in monsters:
        monster_id = fallback_id(monster)
        index[monster_id] = {
            "type": "monster",
            "file": "monsters.json",
            "name": monster.get("name", ""),
        }
    return index


def build_indexes(
    monsters: list[dict[str, Any]],
    *,
    display_normalizer: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Aggregate monster and entity indexes for dataset output."""

    monster_indexes = build_monster_index(monsters)
    by_name, name_conflicts = _build_by_name_map(monsters, display_normalizer=display_normalizer)
    if by_name:
        monster_indexes["by_name"] = by_name
    entity_index = _build_entity_index(monsters)

    payload: dict[str, Any] = {
        "format_version": "v0.4.0",
        "monsters": monster_indexes,
        "entities": entity_index,
        "stats": {
            "total_monsters": len(monsters),
            "total_entities": len(entity_index),
            "unique_crs": len(monster_indexes["by_cr"]),
            "unique_types": len(monster_indexes["by_type"]),
            "unique_sizes": len(monster_indexes["by_size"]),
        },
    }
    if name_conflicts:
        payload["conflicts"] = {"by_name": name_conflicts}
    return payload
