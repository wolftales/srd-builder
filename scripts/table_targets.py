#!/usr/bin/env python3
"""Target reference tables for v0.7.0 extraction.

This documents the specific reference tables we plan to extract from SRD 5.1.
These are reusable gameplay tables (not equipment, monsters, or spells).
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
        "category": "downtime",
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
        "category": "downtime",
        "priority": "LOW",
        "notes": "Daily living costs (wretched to aristocratic)",
    },
    {
        "id": "table:condition_effects",
        "simple_name": "condition_effects",
        "name": "Condition Effects",
        "page": [290, 292],
        "section": "Appendix A: Conditions",
        "category": "reference",
        "priority": "MEDIUM",
        "notes": "May be better suited for conditions.json (v0.9.0)",
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
