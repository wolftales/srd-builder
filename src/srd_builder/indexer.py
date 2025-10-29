#!/usr/bin/env python3
"""
Build index.json for fast lookups.

Creates indexes for:
- Monsters by name (lowercase)
- Monsters by CR
- Monsters by type
- Monsters by size
- All entities by ID

Usage:
    python scripts/build_index.py
"""

import json
from collections import defaultdict
from pathlib import Path


def build_monster_indexes(monsters: list[dict]) -> dict:
    """
    Build various indexes for monsters.

    Returns:
        Dict with indexes:
        - by_name: {name: id}
        - by_cr: {cr: [id, id, ...]}
        - by_type: {type: [id, id, ...]}
        - by_size: {size: [id, id, ...]}
    """
    by_name = {}
    by_cr = defaultdict(list)
    by_type = defaultdict(list)
    by_size = defaultdict(list)

    for monster in monsters:
        monster_id = monster["id"]
        name = monster["name"].lower()
        cr = str(monster.get("challenge_rating", 0))
        mtype = monster.get("type", "unknown")
        size = monster.get("size", "Medium")

        # Index by name (lowercase for case-insensitive lookup)
        by_name[name] = monster_id

        # Index by CR
        by_cr[cr].append(monster_id)

        # Index by type
        by_type[mtype].append(monster_id)

        # Index by size
        by_size[size].append(monster_id)

    # Convert defaultdicts to regular dicts and sort
    by_cr_sorted = {
        k: sorted(v)
        for k, v in sorted(
            by_cr.items(), key=lambda x: float(x[0]) if x[0].replace(".", "").isdigit() else 0
        )
    }
    by_type_sorted = {k: sorted(v) for k, v in sorted(by_type.items())}
    by_size_sorted = {k: sorted(v) for k, v in sorted(by_size.items())}

    return {
        "by_name": by_name,
        "by_cr": by_cr_sorted,
        "by_type": by_type_sorted,
        "by_size": by_size_sorted,
    }


def build_all_entities_index(monsters: list[dict]) -> dict:
    """
    Build index of all entities by ID.

    Returns:
        Dict mapping ID to entity type and location:
        {
            "monster:aboleth": {"type": "monster", "file": "monsters.json"},
            ...
        }
    """
    index = {}

    for monster in monsters:
        monster_id = monster["id"]
        index[monster_id] = {"type": "monster", "file": "monsters.json", "name": monster["name"]}

    return index


def main():
    """Main entry point."""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"

    monsters_file = data_dir / "monsters.json"
    output_file = data_dir / "index.json"

    # Load monsters
    print(f"Loading monsters from {monsters_file}...")
    with open(monsters_file, encoding="utf-8") as f:
        data = json.load(f)

    # Get monster list
    if isinstance(data, dict) and "monsters" in data:
        monsters = data["monsters"]
        source = data.get("source", "SRD_CC_v5.1")
        version = data.get("version", "5.1")
    else:
        monsters = data
        source = "SRD_CC_v5.1"
        version = "5.1"

    print(f"Building indexes for {len(monsters)} monsters...")

    # Build indexes
    monster_indexes = build_monster_indexes(monsters)
    all_entities = build_all_entities_index(monsters)

    # Create index structure
    index = {
        "format_version": "v0.4.0",
        "source": source,
        "version": version,
        "monsters": monster_indexes,
        "entities": all_entities,
        "stats": {
            "total_monsters": len(monsters),
            "total_entities": len(all_entities),
            "unique_crs": len(monster_indexes["by_cr"]),
            "unique_types": len(monster_indexes["by_type"]),
            "unique_sizes": len(monster_indexes["by_size"]),
        },
    }

    # Save index
    print(f"Writing index to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print("✅ Index built successfully!")
    print("\nStats:")
    print(f"  - Total entities: {index['stats']['total_entities']}")
    print(f"  - Monsters: {index['stats']['total_monsters']}")
    print(f"  - Unique CRs: {index['stats']['unique_crs']}")
    print(f"  - Unique types: {index['stats']['unique_types']}")
    print(f"  - Unique sizes: {index['stats']['unique_sizes']}")


if __name__ == "__main__":
    main()
