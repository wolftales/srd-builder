"""SRD 5.1 Page Index - Authoritative table of contents.

This module provides the canonical page index for SRD 5.1 PDF content.
All page numbers are actual PDF pages (1-indexed), not TOC references.

Structure is in ascending page order for easy navigation and validation.
"""

from typing import TypedDict


class PageRange(TypedDict):
    """A range of pages with start and end."""

    start: int
    end: int


class Section(TypedDict):
    """A content section with metadata."""

    pages: PageRange
    description: str
    dataset: str | None  # Which dataset extracts this content (if any)


# Complete SRD 5.1 Table of Contents (ascending page order)
PAGE_INDEX: dict[str, Section] = {
    # Front Matter
    "legal": {
        "pages": {"start": 1, "end": 1},
        "description": "Legal information, license (CC-BY-4.0), attribution",
        "dataset": None,  # Extracted via extract_pdf_metadata.py
    },
    # Character Creation
    "lineages": {
        "pages": {"start": 3, "end": 7},
        "description": "Character lineages (races): Dwarf, Elf, Halfling, Human, etc.",
        "dataset": "lineages",
    },
    "classes": {
        "pages": {"start": 8, "end": 55},
        "description": "Character classes: Barbarian through Wizard (12 classes)",
        "dataset": "classes",
    },
    "beyond_1st_level": {
        "pages": {"start": 56, "end": 61},
        "description": "Advancement: XP, leveling, multiclassing",
        "dataset": None,
    },
    # Equipment & Resources
    "equipment": {
        "pages": {"start": 62, "end": 74},
        "description": "Equipment tables: armor, weapons, gear, services, costs",
        "dataset": "equipment",  # Tables extracted, items in equipment.json
    },
    "feats": {
        "pages": {"start": 75, "end": 75},
        "description": "Optional feat: Grappler",
        "dataset": None,
    },
    # Core Rules
    "using_ability_scores": {
        "pages": {"start": 76, "end": 83},
        "description": "Ability checks, saving throws, skills, modifiers",
        "dataset": None,
    },
    "time": {
        "pages": {"start": 84, "end": 84},
        "description": "Time in D&D: rounds, minutes, hours, days",
        "dataset": None,
    },
    "movement": {
        "pages": {"start": 84, "end": 85},
        "description": "Movement rules: speed, difficult terrain, climbing, swimming",
        "dataset": None,
    },
    "environment": {
        "pages": {"start": 86, "end": 87},
        "description": "Environmental hazards: falling, suffocating, vision",
        "dataset": None,
    },
    "between_adventures": {
        "pages": {"start": 88, "end": 89},
        "description": "Downtime activities: resting, lifestyle expenses",
        "dataset": None,
    },
    "combat": {
        "pages": {"start": 90, "end": 99},
        "description": "Combat rules: initiative, actions, attacks, damage, conditions",
        "dataset": None,
    },
    # Magic
    "spellcasting": {
        "pages": {"start": 100, "end": 104},
        "description": "Spellcasting rules: components, concentration, spell slots",
        "dataset": None,
    },
    "spell_lists": {
        "pages": {"start": 105, "end": 113},
        "description": "Spell lists by class (Bard, Cleric, Druid, etc.)",
        "dataset": None,
    },
    "spell_descriptions": {
        "pages": {"start": 114, "end": 194},
        "description": "Spell descriptions: 319 spells from Acid Splash to Wish",
        "dataset": "spells",
    },
    # Hazards & Rules
    "traps": {
        "pages": {"start": 195, "end": 198},
        "description": "Traps: sample traps, detection, effects",
        "dataset": None,
    },
    "diseases": {
        "pages": {"start": 199, "end": 200},
        "description": "Diseases: Cackle Fever, Sewer Plague, Sight Rot",
        "dataset": None,
    },
    "madness": {
        "pages": {"start": 201, "end": 202},
        "description": "Madness: short-term, long-term, indefinite",
        "dataset": None,
    },
    "objects": {
        "pages": {"start": 203, "end": 203},
        "description": "Objects: AC, hit points, breaking objects",
        "dataset": None,
    },
    # Items
    "poisons": {
        "pages": {"start": 204, "end": 205},
        "description": "Poisons: types, application, effects, costs",
        "dataset": None,
    },
    "magic_items": {
        "pages": {"start": 206, "end": 253},
        "description": "Magic items: rarity, tables, A-Z descriptions, sentient items, artifacts",
        "dataset": None,  # Future extraction
    },
    # Monsters
    "monsters": {
        "pages": {"start": 254, "end": 394},
        "description": "Monster stat blocks: 296 creatures from Aboleth to Zombie",
        "dataset": "monsters",
    },
    # Appendices
    "appendix_mm_b_npcs": {
        "pages": {"start": 395, "end": 403},
        "description": "Appendix MM-B: Nonplayer Characters (NPCs)",
        "dataset": None,  # Future extraction
    },
}


def get_section_at_page(page: int) -> str | None:
    """Get the section name for a given PDF page number.

    Args:
        page: PDF page number (1-indexed)

    Returns:
        Section name if found, None otherwise
    """
    for section_name, section in PAGE_INDEX.items():
        if section["pages"]["start"] <= page <= section["pages"]["end"]:
            return section_name
    return None


def get_all_pages_by_dataset(dataset: str) -> list[int]:
    """Get all page numbers associated with a dataset.

    Args:
        dataset: Dataset name (e.g., "monsters", "spells", "equipment")

    Returns:
        Sorted list of page numbers
    """
    pages: list[int] = []
    for section in PAGE_INDEX.values():
        if section.get("dataset") == dataset:
            start = section["pages"]["start"]
            end = section["pages"]["end"]
            pages.extend(range(start, end + 1))
    return sorted(pages)


def validate_page_coverage() -> dict[str, list[int]]:
    """Validate that all pages are covered and find gaps.

    Returns:
        Dictionary with 'covered' and 'gaps' lists
    """
    covered: set[int] = set()
    for section in PAGE_INDEX.values():
        start = section["pages"]["start"]
        end = section["pages"]["end"]
        covered.update(range(start, end + 1))

    # Find gaps (assuming PDF is 1-403 pages based on appendix end)
    all_pages = set(range(1, 404))
    gaps = sorted(all_pages - covered)

    return {"covered": sorted(covered), "gaps": gaps}
