#!/usr/bin/env python3
"""Target reference tables for v0.7.0 extraction.

This documents the specific reference tables we plan to extract from SRD 5.1.
These are reusable gameplay tables (not equipment, monsters, or spells).

TABLE CATEGORIES (SRD-Aligned):
  - character_creation: Chapters 1-2 (ability scores, proficiency)
  - class_progression: Chapter 3 (all 12 class level tables)
  - equipment: Chapter 5 (armor, weapons, gear, services, costs)
  - combat: Chapter 9 (CR/XP, actions, conditions in combat)
  - exploration: Chapter 8 (travel, environment, resting)
  - magic: Chapter 10 (spell slots, cantrip scaling, components)
  - conditions: Appendix A (status effects, mechanical impacts)
  - reference: Cross-cutting (creature size, languages, etc.)
"""

from typing import TypedDict


class TableTarget(TypedDict):
    """Metadata for a target table."""

    id: str
    simple_name: str
    name: str
    page: int | list[int]
    section: str
    category: str
    priority: str  # HIGH, MEDIUM, LOW
    notes: str


# Target tables for v0.7.0 extraction
# Priority: HIGH = needed by other datasets, MEDIUM = commonly referenced, LOW = nice-to-have
TARGET_TABLES: list[TableTarget] = [
    # Character Creation
    {
        "id": "table:ability_scores_and_modifiers",
        "simple_name": "ability_scores_and_modifiers",
        "name": "Ability Scores and Modifiers",
        "page": 7,
        "section": "Chapter 1: Characters",
        "category": "character_creation",
        "priority": "HIGH",
        "notes": "Core mechanic: ability score to modifier conversion",
    },
    {
        "id": "table:proficiency_bonus",
        "simple_name": "proficiency_bonus",
        "name": "Proficiency Bonus by Level",
        "page": 15,
        "section": "Chapter 1: Characters",
        "category": "character_creation",
        "priority": "HIGH",
        "notes": "Needed for classes dataset (v0.8.0)",
    },
    # Class Progression Tables (v0.8.2)
    {
        "id": "table:barbarian_progression",
        "simple_name": "barbarian_progression",
        "name": "The Barbarian",
        "page": 8,
        "section": "Chapter 3: Classes - Barbarian",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: rages, rage damage, features",
    },
    {
        "id": "table:bard_progression",
        "simple_name": "bard_progression",
        "name": "The Bard",
        "page": 11,
        "section": "Chapter 3: Classes - Bard",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: cantrips, spells known, spell slots, bardic inspiration",
    },
    {
        "id": "table:cleric_progression",
        "simple_name": "cleric_progression",
        "name": "The Cleric",
        "page": 16,
        "section": "Chapter 3: Classes - Cleric",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: cantrips, spell slots, features",
    },
    {
        "id": "table:druid_progression",
        "simple_name": "druid_progression",
        "name": "The Druid",
        "page": 25,
        "section": "Chapter 3: Classes - Druid",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: cantrips, spell slots, wild shape",
    },
    {
        "id": "table:fighter_progression",
        "simple_name": "fighter_progression",
        "name": "The Fighter",
        "page": 26,
        "section": "Chapter 3: Classes - Fighter",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: features by level",
    },
    {
        "id": "table:monk_progression",
        "simple_name": "monk_progression",
        "name": "The Monk",
        "page": 28,
        "section": "Chapter 3: Classes - Monk",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: martial arts, ki points, unarmored movement",
    },
    {
        "id": "table:paladin_progression",
        "simple_name": "paladin_progression",
        "name": "The Paladin",
        "page": 31,
        "section": "Chapter 3: Classes - Paladin",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: spell slots (half caster)",
    },
    {
        "id": "table:ranger_progression",
        "simple_name": "ranger_progression",
        "name": "The Ranger",
        "page": 37,
        "section": "Chapter 3: Classes - Ranger",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: spell slots (half caster), favored enemies",
    },
    {
        "id": "table:rogue_progression",
        "simple_name": "rogue_progression",
        "name": "The Rogue",
        "page": 39,
        "section": "Chapter 3: Classes - Rogue",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: sneak attack damage",
    },
    {
        "id": "table:sorcerer_progression",
        "simple_name": "sorcerer_progression",
        "name": "The Sorcerer",
        "page": 42,
        "section": "Chapter 3: Classes - Sorcerer",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: cantrips, spells known, spell slots, sorcery points",
    },
    {
        "id": "table:warlock_progression",
        "simple_name": "warlock_progression",
        "name": "The Warlock",
        "page": 44,
        "section": "Chapter 3: Classes - Warlock",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: cantrips, spells known, spell slots (pact magic), invocations",
    },
    {
        "id": "table:wizard_progression",
        "simple_name": "wizard_progression",
        "name": "The Wizard",
        "page": 46,
        "section": "Chapter 3: Classes - Wizard",
        "category": "class_progression",
        "priority": "HIGH",
        "notes": "Level progression: cantrips, spell slots",
    },
    # Combat
    {
        "id": "table:experience_by_cr",
        "simple_name": "experience_by_cr",
        "name": "Experience Points by Challenge Rating",
        "page": 57,
        "section": "Chapter 9: Combat",
        "category": "combat",
        "priority": "HIGH",
        "notes": "XP calculation for encounters",
    },
    # Magic
    {
        "id": "table:spell_slots_by_level",
        "simple_name": "spell_slots_by_level",
        "name": "Spell Slots by Character Level",
        "page": 201,
        "section": "Chapter 10: Spellcasting",
        "category": "magic",
        "priority": "HIGH",
        "notes": "Needed for classes dataset (v0.8.0). May be split by class.",
    },
    {
        "id": "table:cantrip_damage",
        "simple_name": "cantrip_damage",
        "name": "Cantrip Damage by Character Level",
        "page": 201,
        "section": "Chapter 10: Spellcasting",
        "category": "magic",
        "priority": "MEDIUM",
        "notes": "Scaling damage for cantrips",
    },
    # Exploration
    {
        "id": "table:travel_pace",
        "simple_name": "travel_pace",
        "name": "Travel Pace",
        "page": 242,
        "section": "Chapter 8: Adventuring",
        "category": "exploration",
        "priority": "MEDIUM",
        "notes": "Distance per hour/day at different paces",
    },
    {
        "id": "table:food_drink_lodging",
        "simple_name": "food_drink_lodging",
        "name": "Food, Drink, and Lodging",
        "page": 158,
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "MEDIUM",
        "notes": "Service costs for inns/taverns",
    },
    {
        "id": "table:services",
        "simple_name": "services",
        "name": "Services",
        "page": 159,
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "MEDIUM",
        "notes": "Hireling and service costs",
    },
    # Reference
    {
        "id": "table:creature_size",
        "simple_name": "creature_size",
        "name": "Size Categories",
        "page": 191,
        "section": "Chapter 9: Combat",
        "category": "reference",
        "priority": "MEDIUM",
        "notes": "Size to space mapping (Tiny=2.5ft, Small/Medium=5ft, etc.)",
    },
    {
        "id": "table:carrying_capacity",
        "simple_name": "carrying_capacity",
        "name": "Carrying Capacity",
        "page": 176,
        "section": "Chapter 7: Using Ability Scores",
        "category": "reference",
        "priority": "LOW",
        "notes": "Encumbrance rules (Strength × 15)",
    },
    {
        "id": "table:lifestyle_expenses",
        "simple_name": "lifestyle_expenses",
        "name": "Lifestyle Expenses",
        "page": 157,
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "LOW",
        "notes": "Daily living costs (wretched to aristocratic)",
    },
    # Equipment tables extracted via text parsing (v0.9.0 Phase 2)
    {
        "id": "table:exchange_rates",
        "simple_name": "exchange_rates",
        "name": "Standard Exchange Rates",
        "page": [62],
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "HIGH",
        "notes": "Currency conversion rates (CP/SP/EP/GP/PP)",
    },
    {
        "id": "table:adventure_gear",
        "simple_name": "adventure_gear",
        "name": "Adventure Gear",
        "page": [69],
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "HIGH",
        "notes": "General adventuring equipment with costs and weights (99 items)",
    },
    {
        "id": "table:container_capacity",
        "simple_name": "container_capacity",
        "name": "Container Capacity",
        "page": [69, 70],
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "HIGH",
        "notes": "Storage capacity for 13 container types",
    },
    {
        "id": "table:donning_doffing_armor",
        "simple_name": "donning_doffing_armor",
        "name": "Donning and Doffing Armor",
        "page": [64],
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "MEDIUM",
        "notes": "Time requirements for putting on/removing armor",
    },
    {
        "id": "table:armor",
        "simple_name": "armor",
        "name": "Armor",
        "page": [63, 64],
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "HIGH",
        "notes": "Extracted via text_parser from PDF pages 63-64",
    },
    {
        "id": "table:weapons",
        "simple_name": "weapons",
        "name": "Weapons",
        "page": [65, 66],
        "section": "Chapter 5: Equipment",
        "category": "equipment",
        "priority": "HIGH",
        "notes": "Extracted via text_parser from PDF pages 65-66",
    },
    {
        "id": "table:condition_effects",
        "simple_name": "condition_effects",
        "name": "Condition Effects",
        "page": [290, 292],
        "section": "Appendix A: Conditions",
        "category": "conditions",
        "priority": "LOW",
        "notes": "Condition status effects and mechanical impacts (not yet implemented)",
    },
]


def print_summary():
    """Print summary of target tables."""
    print("=" * 80)
    print("v0.7.0 Target Reference Tables")
    print("=" * 80)
    print()

    by_priority = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for table in TARGET_TABLES:
        by_priority[table["priority"]].append(table)

    for priority in ["HIGH", "MEDIUM", "LOW"]:
        tables = by_priority[priority]
        print(f"\n{priority} Priority ({len(tables)} tables)")
        print("-" * 40)
        for t in tables:
            page_str = (
                f"p.{t['page']}"
                if isinstance(t["page"], int)
                else f"p.{t['page'][0]}-{t['page'][-1]}"
            )
            print(f"  • {t['name']}")
            print(f"    ID: {t['id']}")
            print(f"    Location: {page_str} ({t['section']})")
            print(f"    Notes: {t['notes']}")
            print()

    print("=" * 80)
    print(f"Total: {len(TARGET_TABLES)} reference tables")
    print("=" * 80)


if __name__ == "__main__":
    print_summary()
