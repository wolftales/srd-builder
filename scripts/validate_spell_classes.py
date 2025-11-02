#!/usr/bin/env python3
"""Validate spell_class_targets.py against actual spell dataset."""

import json
from pathlib import Path

from srd_builder.spell_class_targets import (
    BARD_SPELLS,
    CLERIC_SPELLS,
    DRUID_SPELLS,
    PALADIN_SPELLS,
    RANGER_SPELLS,
    SORCERER_SPELLS,
    WARLOCK_SPELLS,
    WIZARD_SPELLS,
    get_spell_classes,
)


def main():
    # Load actual spells from dataset
    spells_path = Path("dist/srd_5_1/spells.json")
    with open(spells_path) as f:
        data = json.load(f)

    actual_spells = {spell["simple_name"] for spell in data["items"]}

    # Collect all mapped spells
    all_class_lists = {
        "bard": BARD_SPELLS,
        "cleric": CLERIC_SPELLS,
        "druid": DRUID_SPELLS,
        "paladin": PALADIN_SPELLS,
        "ranger": RANGER_SPELLS,
        "sorcerer": SORCERER_SPELLS,
        "warlock": WARLOCK_SPELLS,
        "wizard": WIZARD_SPELLS,
    }

    mapped_spells = set()
    for _class_name, spell_list in all_class_lists.items():
        mapped_spells.update(spell_list)

    # Find mismatches
    unmapped = actual_spells - mapped_spells
    invalid = mapped_spells - actual_spells

    print(f"Total spells in dataset: {len(actual_spells)}")
    print(f"Total spells mapped: {len(mapped_spells)}")
    print()

    if unmapped:
        print(f"⚠️  Spells in dataset but NOT mapped to any class ({len(unmapped)}):")
        for spell in sorted(unmapped):
            print(f"  - {spell}")
        print()

    if invalid:
        print(f"❌ Spells mapped but NOT in dataset ({len(invalid)}):")
        for spell in sorted(invalid):
            print(f"  - {spell}")
        print()

    if not unmapped and not invalid:
        print("✅ Perfect match! All spells mapped correctly.")
        print()

        # Show class distribution
        print("Class distribution:")
        for class_name, spell_list in sorted(all_class_lists.items()):
            print(f"  {class_name:10s}: {len(spell_list):3d} spells")
        print()

        # Test get_spell_classes function
        print("Sample spell class lookups:")
        test_spells = ["fireball", "cure_wounds", "eldritch_blast", "wish"]
        for spell in test_spells:
            classes = get_spell_classes(spell)
            print(f"  {spell:20s} -> {', '.join(classes)}")


if __name__ == "__main__":
    main()
