#!/usr/bin/env python3
"""Investigate which monsters are missing from our 296 extraction.

Compares our extracted monsters against:
1. Blackmoor parser output (if available)
2. Official SRD 5.1 creature list (hardcoded from WotC documents)
"""

import json
from pathlib import Path


def load_our_monsters(output_path: Path) -> set[str]:
    """Load our parsed monster names."""
    if not output_path.exists():
        print(f"⚠️  Output not found: {output_path}")
        print("    Run: python -m srd_builder.build --ruleset srd_5_1 --out dist")
        return set()

    data = json.loads(output_path.read_text(encoding="utf-8"))
    # Handle both list and _meta wrapper format
    items = data.get("items", data) if isinstance(data, dict) else data
    return {m["name"] for m in items}


def load_blackmoor_monsters() -> set[str]:
    """Load Blackmoor parser monster names if available."""
    blackmoor_path = Path("docs/external/blackmoor_monsters.json")
    if not blackmoor_path.exists():
        return set()

    data = json.loads(blackmoor_path.read_text(encoding="utf-8"))
    return {m["name"] for m in data["monsters"]}


def get_official_srd_list() -> set[str]:
    """Official SRD 5.1 creature list from WotC documentation.

    Source: https://dnd.wizards.com/resources/systems-reference-document
    Based on SRD_CC_v5.1.pdf pages 261-394

    Note: This list is compiled from multiple sources and may not be 100% complete.
    """
    # This is a placeholder - we'll need to build this list
    # by manual PDF review or from official WotC sources
    return set()


def compare_sources() -> None:  # noqa: C901
    """Compare our monsters against all available sources."""
    print("=" * 80)
    print("Missing Monster Investigation")
    print("=" * 80)
    print()

    # Load our monsters from parsed output
    our_monsters = load_our_monsters(Path("dist/srd_5_1/data/monsters.json"))
    print(f"Our monsters: {len(our_monsters)}")

    if our_monsters:
        print("\nFirst 10:")
        for name in sorted(our_monsters)[:10]:
            print(f"  • {name}")

    # Load Blackmoor
    blackmoor_monsters = load_blackmoor_monsters()
    if blackmoor_monsters:
        print(f"\nBlackmoor monsters: {len(blackmoor_monsters)}")
        print("\nFirst 10:")
        for name in sorted(blackmoor_monsters)[:10]:
            print(f"  • {name}")

        # Compare
        print("\n" + "=" * 80)
        print("Comparison: Blackmoor vs srd-builder")
        print("=" * 80)

        in_blackmoor_not_ours = blackmoor_monsters - our_monsters
        in_ours_not_blackmoor = our_monsters - blackmoor_monsters

        print(f"\n✅ In Blackmoor, NOT in ours: {len(in_blackmoor_not_ours)}")
        if in_blackmoor_not_ours:
            for name in sorted(in_blackmoor_not_ours)[:20]:
                print(f"  • {name}")
            if len(in_blackmoor_not_ours) > 20:
                print(f"  ... and {len(in_blackmoor_not_ours) - 20} more")

        print(f"\n✅ In ours, NOT in Blackmoor: {len(in_ours_not_blackmoor)}")
        if in_ours_not_blackmoor:
            for name in sorted(in_ours_not_blackmoor)[:20]:
                print(f"  • {name}")
            if len(in_ours_not_blackmoor) > 20:
                print(f"  ... and {len(in_ours_not_blackmoor) - 20} more")
    else:
        print("\n⚠️  Blackmoor data not found")
        print("    Place blackmoor_monsters.json in docs/external/ to enable comparison")

    # Official SRD list
    official_list = get_official_srd_list()
    if official_list and our_monsters:
        print("\n" + "=" * 80)
        print("Comparison: Official SRD vs srd-builder")
        print("=" * 80)

        missing = official_list - our_monsters
        print(f"\n❌ Missing from our extraction: {len(missing)}")
        for name in sorted(missing):
            print(f"  • {name}")

    print("\n" + "=" * 80)
    print("Next Steps")
    print("=" * 80)
    print(
        """
1. **Manual PDF Review**
   - Scan pages 261-394 for monster names in 12pt Calibri-Bold
   - Look for NPCs, variants, unusual formatting
   - Check page headers/footers for clues

2. **Extract Real Data**
   - Place SRD PDF in rulesets/srd_5_1/raw/srd.pdf
   - Run: python -m srd_builder.build --ruleset srd_5_1
   - Re-run this script with actual 296 monsters

3. **Build Official List**
   - Find authoritative SRD 5.1 creature index
   - Cross-reference with our extraction
   - Update get_official_srd_list() function

4. **Pattern Analysis**
   - Check if missing monsters share formatting patterns
   - Expand extraction rules if needed
"""
    )


if __name__ == "__main__":
    compare_sources()
