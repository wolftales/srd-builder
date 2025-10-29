#!/usr/bin/env python3
"""
Polish monsters.json and index.json based on review feedback #2.

Fixes:
1. Index name→ID glitches (duplicates, double hyphens, commas/parens)
2. Strip legendary boilerplate from action text
3. Fix damage resistance qualifiers (energy types shouldn't have 'nonmagical')
4. Text normalization cleanup
5. Update meta.json status
6. Add monstersByCR and monstersByType to index

Usage:
    python scripts/polish_data.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path


def normalize_display_name(name: str) -> str:
    """
    Normalize display name for index keys.

    Examples:
        "blue dragon ancient blue dragon" → "ancient blue dragon"
        "half--red dragon veteran" → "half-red dragon veteran"
        "elf, drow" → "drow elf"
        "gnome, deep (svirfneblin)" → "deep gnome (svirfneblin)"
    """
    # Fix double hyphens
    name = re.sub(r"--+", "-", name)

    # Handle duplicates like "blue dragon ancient blue dragon"
    words = name.split()
    if len(words) > len(set(words)):
        # Check if there's a repeated phrase
        mid = len(words) // 2
        first_half = " ".join(words[:mid])
        second_half = " ".join(words[mid:])
        if first_half in second_half or second_half in first_half:
            # Take the longer/more specific one
            name = second_half if len(second_half) > len(first_half) else first_half

    # Handle comma formats "type, subtype" → "subtype type"
    if "," in name and "(" not in name:
        parts = [p.strip() for p in name.split(",")]
        if len(parts) == 2:
            name = f"{parts[1]} {parts[0]}"

    return name.strip()


def strip_legendary_boilerplate(text: str) -> str:
    """
    Strip legendary actions boilerplate from action text.

    Removes text like "The aboleth can take 3 legendary actions..."
    """
    if not text:
        return text

    # Pattern for legendary actions boilerplate
    patterns = [
        r"The \w+ can take \d+ legendary actions.*?at the start of its turn\.",
        r"The \w+ can take three legendary actions.*?at the start of its turn\.",
        r"Only one legendary action.*?at the start of its turn\.",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # Clean up extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def fix_resistance_qualifiers(resistances: list[dict]) -> list[dict]:
    """
    Fix resistance qualifiers - only B/P/S should have 'nonmagical'.

    Energy types (fire, cold, lightning, acid, thunder, poison, necrotic, radiant,
    psychic, force) should NOT have 'nonmagical' qualifier.
    """
    energy_types = {
        "fire",
        "cold",
        "lightning",
        "acid",
        "thunder",
        "poison",
        "necrotic",
        "radiant",
        "psychic",
        "force",
    }

    physical_types = {"bludgeoning", "piercing", "slashing"}

    fixed = []
    for resist in resistances:
        resist_type = resist.get("type", "").lower()

        # Remove 'nonmagical' qualifier from energy types
        if resist_type in energy_types and resist.get("qualifier") == "nonmagical":
            fixed.append({"type": resist["type"]})
        # Keep qualifier for physical damage types
        elif resist_type in physical_types:
            fixed.append(resist)
        # Everything else keeps as-is
        else:
            fixed.append(resist)

    return fixed


def normalize_text(text: str) -> str:
    """
    Normalize text content - fix spacing, punctuation artifacts.

    Fixes:
    - "Hit:15" → "Hit: 15"
    - "restorationspell" → "restoration spell"
    - Multiple spaces → single space
    - Standardize dice notation
    """
    if not text:
        return text

    # Fix "Hit:" spacing
    text = re.sub(r"Hit:\s*(\d)", r"Hit: \1", text)

    # Fix missing spaces before "spell"
    text = re.sub(r"(\w)(spell)", r"\1 \2", text)

    # Fix missing spaces after periods (but not in abbreviations)
    text = re.sub(r"\.([A-Z])", r". \1", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Standardize dice notation (already done in earlier script, but ensure consistency)
    text = re.sub(r"(\d+d\d+)\s*\+\s*(\d+)", r"\1+\2", text)
    text = re.sub(r"(\d+d\d+)\s*-\s*(\d+)", r"\1-\2", text)

    return text.strip()


def strip_trailing_periods_from_names(monster: dict) -> dict:
    """
    Optionally strip trailing periods from name fields.
    User can decide if they want this or not.
    """
    # For now, keep periods as they appear in SRD
    # This is a style choice - can be enabled later if desired
    return monster


def polish_monster(monster: dict) -> dict:
    """Apply all polish operations to a single monster."""
    polished = monster.copy()

    # Strip legendary boilerplate from actions
    for action in polished.get("actions", []):
        if "text" in action:
            action["text"] = strip_legendary_boilerplate(action["text"])
            action["text"] = normalize_text(action["text"])

    # Normalize text in traits
    for trait in polished.get("traits", []):
        if "text" in trait:
            trait["text"] = normalize_text(trait["text"])

    # Normalize text in legendary_actions
    for action in polished.get("legendary_actions", []):
        if "text" in action:
            action["text"] = normalize_text(action["text"])

    # Fix resistance qualifiers
    if "damage_resistances" in polished:
        polished["damage_resistances"] = fix_resistance_qualifiers(polished["damage_resistances"])

    if "damage_immunities" in polished:
        polished["damage_immunities"] = fix_resistance_qualifiers(polished["damage_immunities"])

    return polished


def rebuild_index(monsters: list[dict]) -> dict:
    """Rebuild index with fixed names and additional indexes."""
    by_name = {}
    by_cr = defaultdict(list)
    by_type = defaultdict(list)
    by_size = defaultdict(list)

    for monster in monsters:
        monster_id = monster["id"]

        # Normalize display name for index key
        display_name = normalize_display_name(monster["name"].lower())

        # Add to by_name index
        by_name[display_name] = monster_id

        # Add to by_cr index
        cr = str(monster.get("challenge_rating", 0))
        by_cr[cr].append(monster_id)

        # Add to by_type index
        mtype = monster.get("type", "unknown")
        by_type[mtype].append(monster_id)

        # Add to by_size index
        size = monster.get("size", "Medium")
        by_size[size].append(monster_id)

    # Sort CR index by numeric value
    def cr_sort_key(cr_str):
        try:
            return float(cr_str)
        except (ValueError, TypeError):
            return 0

    by_cr_sorted = {k: sorted(v) for k, v in sorted(by_cr.items(), key=lambda x: cr_sort_key(x[0]))}
    by_type_sorted = {k: sorted(v) for k, v in sorted(by_type.items())}
    by_size_sorted = {k: sorted(v) for k, v in sorted(by_size.items())}

    return {
        "by_name": by_name,
        "by_cr": by_cr_sorted,
        "by_type": by_type_sorted,
        "by_size": by_size_sorted,
    }


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"

    monsters_file = data_dir / "monsters.json"
    index_file = data_dir / "index.json"
    meta_file = data_dir / "meta.json"

    # Load monsters
    print(f"Loading monsters from {monsters_file}...")
    with open(monsters_file, encoding="utf-8") as f:
        monsters_data = json.load(f)

    if isinstance(monsters_data, dict) and "monsters" in monsters_data:
        monsters = monsters_data["monsters"]
        wrapper = monsters_data
    else:
        monsters = monsters_data
        wrapper = None

    # Polish monsters
    print(f"Polishing {len(monsters)} monsters...")
    polished_monsters = []
    for i, monster in enumerate(monsters):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(monsters)}...")
        polished = polish_monster(monster)
        polished_monsters.append(polished)

    # Save polished monsters
    if wrapper:
        wrapper["monsters"] = polished_monsters
        output_data = wrapper
    else:
        output_data = polished_monsters

    print(f"Writing polished monsters to {monsters_file}...")
    with open(monsters_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Rebuild index
    print("Rebuilding index...")
    monster_indexes = rebuild_index(polished_monsters)

    # Load existing index
    with open(index_file, encoding="utf-8") as f:
        index_data = json.load(f)

    # Update with new indexes
    index_data["monsters"] = monster_indexes

    # Update stats
    index_data["stats"] = {
        "total_monsters": len(polished_monsters),
        "total_entities": len(index_data.get("entities", {})),
        "unique_crs": len(monster_indexes["by_cr"]),
        "unique_types": len(monster_indexes["by_type"]),
        "unique_sizes": len(monster_indexes["by_size"]),
    }

    print(f"Writing updated index to {index_file}...")
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    # Update meta.json
    print(f"Updating {meta_file}...")
    with open(meta_file, encoding="utf-8") as f:
        meta = json.load(f)

    # Add schema version if missing
    if "$schema_version" not in meta:
        meta["$schema_version"] = "1.0"

    # Update extraction status
    if "extraction_status" in meta:
        meta["extraction_status"]["index"] = "complete"

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("\n✅ Polish complete!")
    print("\nSummary:")
    print(f"  - Monsters polished: {len(polished_monsters)}")
    print(f"  - Index entries: {len(monster_indexes['by_name'])}")
    print(f"  - Unique CRs: {len(monster_indexes['by_cr'])}")
    print(f"  - Unique types: {len(monster_indexes['by_type'])}")
    print(f"  - Unique sizes: {len(monster_indexes['by_size'])}")
    print(f"  - Meta schema version: {meta.get('$schema_version')}")


if __name__ == "__main__":
    main()
