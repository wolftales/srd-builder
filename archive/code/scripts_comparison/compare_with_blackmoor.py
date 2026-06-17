#!/usr/bin/env python3
"""Compare srd-builder parser output with Blackmoor parser.

Analyzes differences in monster count, field coverage, and data quality.
"""

import json
from pathlib import Path


def main() -> None:  # noqa: C901
    """Run comparison analysis."""
    ours_path = Path("dist/srd_5_1/data/monsters.json")
    blackmoor_path = Path("docs/external/blackmoor_monsters.json")

    if not ours_path.exists():
        print(f"Error: {ours_path} not found. Run build first.")
        return

    if not blackmoor_path.exists():
        print(f"Error: {blackmoor_path} not found.")
        print("Place Blackmoor's monsters.json at docs/external/blackmoor_monsters.json")
        return

    with open(ours_path) as f:
        ours_data = json.load(f)
    with open(blackmoor_path) as f:
        blackmoor_data = json.load(f)

    ours_monsters = ours_data.get("items", [])
    blackmoor_monsters = blackmoor_data.get("monsters", [])

    print("=" * 80)
    print("SRD Parser Comparison: srd-builder vs Blackmoor")
    print("=" * 80)
    print()

    # 1. Monster Count
    print("1. MONSTER COUNT")
    print("-" * 80)
    print(f"srd-builder:  {len(ours_monsters):3d} monsters")
    print(f"Blackmoor:    {len(blackmoor_monsters):3d} monsters")
    print(f"Difference:   {len(ours_monsters) - len(blackmoor_monsters):+3d} monsters")
    print()

    # 2. Monster Name Comparison
    print("2. MONSTER NAMES")
    print("-" * 80)
    ours_names = {m["name"] for m in ours_monsters}
    blackmoor_names = {m["name"] for m in blackmoor_monsters}

    only_in_ours = ours_names - blackmoor_names
    only_in_blackmoor = blackmoor_names - ours_names
    common = ours_names & blackmoor_names

    print(f"Common monsters:      {len(common):3d}")
    print(f"Only in srd-builder:  {len(only_in_ours):3d}")
    print(f"Only in Blackmoor:    {len(only_in_blackmoor):3d}")

    if only_in_ours:
        print("\nFirst 20 monsters only in srd-builder:")
        for name in sorted(only_in_ours)[:20]:
            print(f"  + {name}")
        if len(only_in_ours) > 20:
            print(f"  ... and {len(only_in_ours) - 20} more")

    if only_in_blackmoor:
        print("\nMonsters only in Blackmoor:")
        for name in sorted(only_in_blackmoor):
            print(f"  - {name}")
    print()

    # 3. Field Coverage
    print("3. FIELD COVERAGE")
    print("-" * 80)

    # Get all fields from both parsers
    ours_fields = set()
    for m in ours_monsters:
        ours_fields.update(m.keys())

    blackmoor_fields = set()
    for m in blackmoor_monsters:
        blackmoor_fields.update(m.keys())

    print("Fields in srd-builder:", len(ours_fields))
    print("Fields in Blackmoor:  ", len(blackmoor_fields))
    print()

    only_ours = ours_fields - blackmoor_fields
    only_blackmoor = blackmoor_fields - ours_fields
    common_fields = ours_fields & blackmoor_fields

    if only_ours:
        print(f"Fields only in srd-builder ({len(only_ours)}):")
        for field in sorted(only_ours):
            count = sum(1 for m in ours_monsters if m.get(field))
            print(f"  + {field:25s} ({count:3d} monsters)")

    if only_blackmoor:
        print(f"\nFields only in Blackmoor ({len(only_blackmoor)}):")
        for field in sorted(only_blackmoor):
            count = sum(1 for m in blackmoor_monsters if m.get(field))
            print(f"  - {field:25s} ({count:3d} monsters)")
    print()

    # 4. Data Quality Comparison (for common monsters)
    print("4. DATA QUALITY COMPARISON (Common Monsters)")
    print("-" * 80)

    # Build lookup dicts
    ours_lookup = {m["name"]: m for m in ours_monsters}
    blackmoor_lookup = {m["name"]: m for m in blackmoor_monsters}

    # Compare common fields for common monsters
    quality_metrics = {}
    for field in sorted(common_fields):
        if field in ("id", "simple_name", "src", "source", "page", "summary"):
            continue  # Skip metadata fields

        ours_count = 0
        blackmoor_count = 0
        both_count = 0

        for name in common:
            ours_has = bool(ours_lookup[name].get(field))
            blackmoor_has = bool(blackmoor_lookup[name].get(field))

            if ours_has:
                ours_count += 1
            if blackmoor_has:
                blackmoor_count += 1
            if ours_has and blackmoor_has:
                both_count += 1

        quality_metrics[field] = {
            "ours": ours_count,
            "blackmoor": blackmoor_count,
            "both": both_count,
            "common": len(common),
        }

    # Print comparison table
    print(f"{'Field':<20s} {'Ours':>6s} {'Them':>6s} {'Both':>6s} {'Winner'}")
    print("-" * 60)

    for field in sorted(quality_metrics.keys()):
        metrics = quality_metrics[field]
        ours_pct = (metrics["ours"] * 100) // metrics["common"]
        blackmoor_pct = (metrics["blackmoor"] * 100) // metrics["common"]

        if ours_pct > blackmoor_pct:
            winner = "✓ Ours"
        elif blackmoor_pct > ours_pct:
            winner = "✗ Them"
        else:
            winner = "= Tie"

        print(f"{field:<20s} {ours_pct:5d}% {blackmoor_pct:5d}% {metrics['both']:5d} {winner}")
    print()

    # 5. Detailed Examples
    print("5. SAMPLE COMPARISON (Aboleth)")
    print("-" * 80)

    if "Aboleth" in common:
        ours_aboleth = ours_lookup["Aboleth"]
        blackmoor_aboleth = blackmoor_lookup["Aboleth"]

        print("srd-builder fields:")
        print(f"  - Armor Class:    {ours_aboleth.get('armor_class')}")
        print(f"  - Hit Points:     {ours_aboleth.get('hit_points')}")
        print(f"  - Languages:      {ours_aboleth.get('languages')}")
        print(f"  - Reactions:      {len(ours_aboleth.get('reactions', []))} reactions")
        print(f"  - Traits:         {len(ours_aboleth.get('traits', []))} traits")
        print(f"  - Actions:        {len(ours_aboleth.get('actions', []))} actions")
        print(f"  - Legendary:      {len(ours_aboleth.get('legendary_actions', []))} legendary")

        print("\nBlackmoor fields:")
        print(f"  - Armor Class:    {blackmoor_aboleth.get('armor_class')}")
        print(f"  - Hit Points:     {blackmoor_aboleth.get('hit_points')}")
        print(f"  - Languages:      {blackmoor_aboleth.get('languages', 'N/A')}")
        print(f"  - Reactions:      {len(blackmoor_aboleth.get('reactions', []))} reactions")
        print(f"  - Traits:         {len(blackmoor_aboleth.get('traits', []))} traits")
        print(f"  - Actions:        {len(blackmoor_aboleth.get('actions', []))} actions")
        print(
            f"  - Legendary:      {len(blackmoor_aboleth.get('legendary_actions', []))} legendary"
        )
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ srd-builder extracts {len(ours_monsters) - len(blackmoor_monsters)} MORE monsters")
    print(f"✓ srd-builder has {len(only_ours)} additional fields:")
    for field in sorted(only_ours)[:5]:
        print(f"    - {field}")

    wins = sum(1 for m in quality_metrics.values() if m["ours"] > m["blackmoor"])
    losses = sum(1 for m in quality_metrics.values() if m["ours"] < m["blackmoor"])
    ties = len(quality_metrics) - wins - losses

    print(f"\nData Quality (for {len(common)} common monsters):")
    print(f"  Wins:   {wins:2d} fields")
    print(f"  Losses: {losses:2d} fields")
    print(f"  Ties:   {ties:2d} fields")
    print()


if __name__ == "__main__":
    main()
