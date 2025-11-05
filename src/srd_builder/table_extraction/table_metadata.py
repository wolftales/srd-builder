"""Table extraction metadata and configuration.

This module defines extraction patterns and metadata for all SRD tables.
Each table config specifies:
- pattern_type: Extraction/generation pattern (standard_grid, split_column, calculated, etc.)
- source: Data provenance (srd, derived, convenience, reference)
- Extraction parameters (pages, regions, headers, transformations)
- Validation rules (expected row counts)

The patterns.py engine uses this metadata to extract/generate tables without
hardcoded logic. All table-specific configuration lives here.
"""

from typing import Any

# ============================================================================
# SOURCE TYPE DEFINITIONS
# ============================================================================

SOURCE_TYPES = {
    "srd": "Extracted directly from SRD PDF",
    "derived": "Calculated from game rules (appears across multiple tables)",
    "convenience": "Convenience table for quick reference (formula-based)",
    "reference": "Hardcoded reference data (cannot extract from PDF as standalone table)",
    "custom": "Custom/user-defined table (not from official SRD)",
}

# ============================================================================
# PATTERN TYPE DEFINITIONS
# ============================================================================

PATTERN_TYPES = {
    "standard_grid": "PyMuPDF auto-detected grid table",
    "split_column": "Side-by-side sub-tables within same page region",
    "multipage_text_region": "Text-based extraction across multiple page regions",
    "text_region": "Text-based extraction from single page region",
    "calculated": "Generated from formula or lookup table",
    "reference": "Static hardcoded data (fallback when extraction not possible)",
    "legacy_parser": "Uses existing parser function from text_table_parser.py (temporary during migration)",
}

# ============================================================================
# UNIFIED TABLE METADATA
# All tables use same config structure with pattern_type driving behavior
# ============================================================================

TABLES: dict[str, dict[str, Any]] = {
    # ═══════════════════════════════════════════════════════════
    # PDF EXTRACTED TABLES - Text-based parsing
    # ═══════════════════════════════════════════════════════════
    "ability_scores_and_modifiers": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [76],  # Actual PDF page number
        "parser": "parse_ability_scores_and_modifiers_table",
        "chapter": "Chapter 1: Characters",
        "confirmed": True,  # Extraction verified working
        "validation": {"expected_rows": 16},
    },
    "adventure_gear": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [68],  # Table starts on page 68 and continues to 69
        "parser": "parse_adventure_gear_table",
        "validation": {"expected_rows": 49},
    },
    "armor": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [63, 64],
        "parser": "parse_armor_table",
        "validation": {"expected_rows": 14},
    },
    "container_capacity": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [69, 70],
        "parser": "parse_container_capacity_table",
        "validation": {"expected_rows": 7},
    },
    "donning_doffing_armor": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [64],
        "parser": "parse_donning_doffing_armor_table",
        "validation": {"expected_rows": 3},
    },
    "exchange_rates": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [62],
        "parser": "parse_exchange_rates_table",
        "validation": {"expected_rows": 4},
    },
    "food_drink_lodging": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [73, 74],
        "parser": "parse_food_drink_lodging_table",
        "validation": {"expected_rows": 20},
    },
    "lifestyle_expenses": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [72, 73],
        "parser": "parse_lifestyle_expenses_table",
        "validation": {"expected_rows": 6},
    },
    "mounts_and_other_animals": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [71, 72],
        "parser": "parse_mounts_and_other_animals_table",
        "validation": {"expected_rows": 13},
    },
    "services": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [74],
        "parser": "parse_services_table",
        "validation": {"expected_rows": 5},
    },
    "tack_harness_vehicles": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [72],
        "parser": "parse_tack_harness_vehicles_table",
        "validation": {"expected_rows": 14},
    },
    "tools": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [70],
        "parser": "parse_tools_table",
        "validation": {"expected_rows": 18},
    },
    "trade_goods": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [72],
        "parser": "parse_trade_goods_table",
        "validation": {"expected_rows": 15},
    },
    "waterborne_vehicles": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [72],
        "parser": "parse_waterborne_vehicles_table",
        "validation": {"expected_rows": 3},
    },
    "weapons": {
        "pattern_type": "legacy_parser",
        "source": "srd",
        "pages": [65, 66],
        "parser": "parse_weapons_table",
        "validation": {"expected_rows": 37},
    },
    "experience_by_cr": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [258],  # Actual PDF page number
        "headers": ["Challenge Rating", "XP"],
        "regions": [
            {"x_min": 0, "x_max": 130, "y_min": 445, "y_max": 665},
            {"x_min": 130, "x_max": 250, "y_min": 445, "y_max": 665},
        ],
        "transformations": {"XP": {"remove_commas": True, "cast": "int"}},
        "special_cases": [{"column": 0, "pattern": r"^0$", "context": "or", "action": "use_first"}],
        "chapter": "Chapter 9: Combat",
        "confirmed": True,  # Extraction verified working (34 rows extracted correctly)
        "validation": {"expected_rows": 34},
    },
    # ═══════════════════════════════════════════════════════════
    # CALCULATED TABLES - Generated from rules
    # ═══════════════════════════════════════════════════════════
    "proficiency_bonus": {
        "pattern_type": "calculated",
        "source": "derived",
        "calculation": {
            "method": "lookup",
            "data": {
                range(1, 5): "+2",
                range(5, 9): "+3",
                range(9, 13): "+4",
                range(13, 17): "+5",
                range(17, 21): "+6",
            },
        },
        "headers": ["Level", "Proficiency Bonus"],
        "notes": "Proficiency bonus by character level (appears in all class tables but not as standalone table)",
        "validation": {"expected_rows": 20},
    },
    "carrying_capacity": {
        "pattern_type": "calculated",
        "source": "convenience",
        "calculation": {
            "method": "formula",
            "formula": lambda strength: strength * 15,
            "range": range(1, 31),
        },
        "headers": ["Strength Score", "Carrying Capacity (lbs)"],
        "notes": "Carrying capacity formula (Strength × 15) expressed as reference table",
        "validation": {"expected_rows": 30},
    },
    # ═══════════════════════════════════════════════════════════
    # REFERENCE TABLES - Hardcoded (cannot extract as standalone)
    # ═══════════════════════════════════════════════════════════
    "spell_slots_by_level": {
        "pattern_type": "reference",
        "source": "reference",
        "headers": [
            "Level",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "5th",
            "6th",
            "7th",
            "8th",
            "9th",
            "Cantrips Known",
        ],
        "rows": [
            [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [4, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [5, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0],
            [6, 4, 3, 3, 0, 0, 0, 0, 0, 0, 0],
            [7, 4, 3, 3, 1, 0, 0, 0, 0, 0, 0],
            [8, 4, 3, 3, 2, 0, 0, 0, 0, 0, 0],
            [9, 4, 3, 3, 3, 1, 0, 0, 0, 0, 0],
            [10, 4, 3, 3, 3, 2, 0, 0, 0, 0, 0],
            [11, 4, 3, 3, 3, 2, 1, 0, 0, 0, 0],
            [12, 4, 3, 3, 3, 2, 1, 0, 0, 0, 0],
            [13, 4, 3, 3, 3, 2, 1, 1, 0, 0, 0],
            [14, 4, 3, 3, 3, 2, 1, 1, 0, 0, 0],
            [15, 4, 3, 3, 3, 2, 1, 1, 1, 0, 0],
            [16, 4, 3, 3, 3, 2, 1, 1, 1, 0, 0],
            [17, 4, 3, 3, 3, 2, 1, 1, 1, 1, 0],
            [18, 4, 3, 3, 3, 3, 1, 1, 1, 1, 0],
            [19, 4, 3, 3, 3, 3, 2, 1, 1, 1, 0],
            [20, 4, 3, 3, 3, 3, 2, 2, 1, 1, 0],
        ],
        "notes": "Full caster spell slot progression - not found as standalone table in PDF (embedded in class tables)",
        "validation": {"expected_rows": 20},
    },
    "cantrip_damage": {
        "pattern_type": "reference",
        "source": "reference",
        "headers": ["Character Level", "Damage Dice"],
        "rows": [
            ["1st-4th", "1 die"],
            ["5th-10th", "2 dice"],
            ["11th-16th", "3 dice"],
            ["17th-20th", "4 dice"],
        ],
        "notes": "Cantrip damage scaling by character level - TODO: search PDF for actual table",
        "validation": {"expected_rows": 4},
    },
    "travel_pace": {
        "pattern_type": "reference",
        "source": "reference",
        "headers": ["Pace", "Distance per Minute", "Distance per Hour", "Distance per Day"],
        "rows": [
            ["Fast", "400 feet", "4 miles", "30 miles"],
            ["Normal", "300 feet", "3 miles", "24 miles"],
            ["Slow", "200 feet", "2 miles", "18 miles"],
        ],
        "notes": "Travel pace rates - TODO: search PDF for actual table (likely in exploration section)",
        "validation": {"expected_rows": 3},
    },
    "creature_size": {
        "pattern_type": "reference",
        "source": "reference",
        "headers": ["Size", "Space"],
        "rows": [
            ["Tiny", "2½ by 2½ ft."],
            ["Small", "5 by 5 ft."],
            ["Medium", "5 by 5 ft."],
            ["Large", "10 by 10 ft."],
            ["Huge", "15 by 15 ft."],
            ["Gargantuan", "20 by 20 ft. or larger"],
        ],
        "notes": "Creature size categories - TODO: search PDF for actual table",
        "validation": {"expected_rows": 6},
    },
    # ═══════════════════════════════════════════════════════════
    # CLASS PROGRESSION TABLES - Hardcoded (will extract in v0.9.6)
    # Level 1-20 progression for all 12 classes
    # ═══════════════════════════════════════════════════════════
    "barbarian": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",  # Temp: points to reference_data.py
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "bard": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "cleric": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "druid": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "fighter": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "monk": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "paladin": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "ranger": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "rogue": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "sorcerer": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "warlock": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
    "wizard": {
        "pattern_type": "reference",
        "source": "srd",
        "use_legacy_data": "CLASS_PROGRESSIONS",
        "notes": "TODO v0.9.6: Extract from PDF",
        "validation": {"expected_rows": 20},
    },
}


def get_table_metadata(simple_name: str) -> dict[str, Any] | None:
    """Get metadata for a table by simple_name.

    Handles both direct lookups and _progression suffix for class tables.

    Args:
        simple_name: Table simple_name (e.g., "experience_by_cr" or "barbarian_progression")

    Returns:
        Table configuration dict or None if not found
    """
    # Direct lookup first
    if simple_name in TABLES:
        return TABLES[simple_name]

    # Check class progressions (strip _progression suffix)
    if simple_name.endswith("_progression"):
        class_name = simple_name.replace("_progression", "")
        if class_name in TABLES:
            return TABLES[class_name]

    return None
