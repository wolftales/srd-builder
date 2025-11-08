"""Table extraction metadata and configuration.

This module defines extraction patterns and metadata for all SRD tables.
Each table config specifies:
- pattern_type: Extraction/generation pattern (standard_grid, split_column, calculated, etc.)
- source: Data provenance (srd, derived, convenience, reference)
- Extraction parameters (pages, regions, headers, transformations)
- Validation rules (expected row counts)
- data_driven: Boolean indicating table uses modern pattern-based extraction engine (NOT legacy function parsers)
- confirmed: Boolean indicating extraction has been tested and validated

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
        "pages": [68, 69],  # Table spans pages 68-69
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
    # PDF EXTRACTED TABLES - Text region extraction (data-driven)
    # Using modern pattern-based extraction (NOT legacy_parser)
    # ═══════════════════════════════════════════════════════════
    "travel_pace": {
        "pattern_type": "text_region",  # Modern data-driven extraction
        "source": "srd",
        "pages": [84],
        "headers": [
            "Pace",
            "Distance per Minute",
            "Distance per Hour",
            "Distance per Day",
            "Effect",
        ],
        "region": {"x_min": 320, "x_max": 560, "y_min": 570, "y_max": 655},
        "column_boundaries": [
            370,
            405,
            437,
            470,
        ],  # Pace(~328) | Min(373-404) | Hour(406-436) | Day(439-469) | Effect(470+)
        "chapter": "Movement",
        "data_driven": True,  # Uses modern pattern-based extraction engine (NOT legacy function parser)
        "confirmed": False,  # Will be confirmed after testing
        "validation": {"expected_rows": 3},
        "notes": "Travel pace rates (Fast/Normal/Slow) with 5 columns including effects - modern pattern-based extraction from page 84",
    },
    "size_categories": {
        "pattern_type": "text_region",  # Modern data-driven extraction
        "source": "srd",
        "pages": [92],
        "headers": ["Size", "Space"],
        "region": {"x_min": 320, "x_max": 465, "y_min": 200, "y_max": 275},
        "column_split_x": 380,  # Split between size names (x~329) and space values (x~383)
        "chapter": "Combat",
        "data_driven": True,  # Uses modern pattern-based extraction engine (NOT legacy function parser)
        "confirmed": False,  # Will be confirmed after testing
        "validation": {"expected_rows": 6},
        "notes": "Size Categories table (Tiny through Gargantuan) - modern pattern-based extraction from page 92",
    },
    # ═══════════════════════════════════════════════════════════
    # CLASS PROGRESSION TABLES - Extracting in v0.9.8
    # Level 1-20 progression for all 12 classes
    # ═══════════════════════════════════════════════════════════
    "barbarian": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [8],
        "headers": ["Level", "Proficiency Bonus", "Features", "Rages", "Rage Damage"],
        "regions": [
            {
                "x_min": 0,
                "x_max": 280,
                "y_min": 463,
                "y_max": 703,
                # Words at: Level(62) | Prof(105) | Features(141) | Rages(221) | Damage(263)
                # Boundaries split between: 83, 123, 180, 242
                "column_boundaries": [83, 123, 200, 242],
            },
            {
                "x_min": 280,
                "x_max": 560,
                "y_min": 73,
                "y_max": 268,
                # Words at (offsets): Level(50) | Prof(95) | Features(132) | Rages(212) | Damage(254)
                # Boundaries split between: 72, 113, 172, 233
                "column_boundaries": [72, 113, 190, 233],
            },
        ],
        "merge_continuation_rows": True,  # Features column spans multiple lines
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Two-column layout with multi-line Features column",
    },
    "bard": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [11],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Features",
            "Cantrips Known",
            "Spells Known",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "5th",
            "6th",
            "7th",
            "8th",
            "9th",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 310,
                "y_max": 610,
                "column_boundaries": [
                    86,
                    129,
                    250,
                    310,
                    349,
                    371,
                    396,
                    419,
                    443,
                    466,
                    489,
                    513,
                    536,
                ],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout with 14 columns (Cantrips Known + Spells Known + spell slots 1st-9th)",
    },
    "cleric": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [15],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Features",
            "Cantrips Known",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "5th",
            "6th",
            "7th",
            "8th",
            "9th",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 320,
                "y_max": 610,
                "column_boundaries": [86, 129, 290, 347, 371, 396, 419, 443, 466, 489, 513, 536],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout with 13 columns (Cantrips + spell slots 1st-9th)",
    },
    "druid": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [19],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Features",
            "Cantrips Known",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "5th",
            "6th",
            "7th",
            "8th",
            "9th",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 320,
                "y_max": 590,
                "column_boundaries": [86, 129, 290, 347, 371, 396, 419, 443, 466, 489, 513, 536],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout with 13 columns (Cantrips + spell slots 1st-9th)",
    },
    "fighter": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [24],
        "headers": ["Level", "Proficiency Bonus", "Features"],
        "regions": [
            {
                "x_min": 0,
                "x_max": 280,
                "y_min": 532,
                "y_max": 687,
                "column_boundaries": [90, 145],  # Level(57-90) | Prof(104-145) | Features(155+)
            },
            {
                "x_min": 280,
                "x_max": 560,
                "y_min": 71,
                "y_max": 128,
                "column_boundaries": [90, 145],  # Same structure in right column
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Two-column layout (1st-15th left, 16th-20th right) with multi-line Features column",
    },
    "monk": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [26],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Martial Arts",
            "Ki Points",
            "Unarmored Movement",
            "Features",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 311,
                "y_max": 521,
                "column_boundaries": [
                    85,
                    160,
                    215,
                    260,
                    360,
                ],  # Level | Prof | Arts | Ki | Movement | Features
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout with 6 columns including Martial Arts, Ki Points, and Unarmored Movement. Known limitation: Row 6 Features contains soft hyphen (U+00AD) in 'Ki-Empowered' from source PDF.",
    },
    "paladin": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [30],
        "headers": ["Level", "Proficiency Bonus", "Features", "1st", "2nd", "3rd", "4th", "5th"],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 310,
                "y_max": 560,
                "column_boundaries": [86, 129, 235, 315, 341, 365, 390],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Half-caster, 8 columns (spell slots 1st-5th only)",
    },
    "ranger": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [35],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Features",
            "Spells Known",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "5th",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 320,
                "y_max": 570,
                "column_boundaries": [86, 129, 256, 362, 395, 418, 444, 469, 494],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout, half-caster with 9 columns (Spells Known + spell slots 1st-5th)",
    },
    "rogue": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [39],
        "headers": ["Level", "Proficiency Bonus", "Sneak Attack", "Features"],
        "regions": [
            {
                "x_min": 0,
                "x_max": 280,
                "y_min": 544,
                "y_max": 689,
                "column_boundaries": [
                    95,
                    153,
                    190,
                ],  # Level(57-95) | Prof(102-153) | Sneak(156-190) | Features(195+)
            },
            {
                "x_min": 280,
                "x_max": 560,
                "y_min": 72,
                "y_max": 237,
                "column_boundaries": [
                    75,
                    125,
                    170,
                ],  # Level(rel:50) | Prof(rel:100) | Sneak(rel:150) | Features(rel:187)
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Two-column layout (1st-10th left, 11th-20th right), right column starts at y=72 to capture continuation text from 10th row. Known limitation: Row 10 Features shows 'Ability Score' without 'Improvement' due to complex page break (word on page 40).",
    },
    "sorcerer": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [42],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Sorcery Points",
            "Features",
            "Cantrips Known",
            "Spells Known",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "5th",
            "6th",
            "7th",
            "8th",
            "9th",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 310,
                "y_max": 650,
                "column_boundaries": [
                    86,
                    131,
                    172,
                    244,
                    310,
                    349,
                    371,
                    396,
                    419,
                    443,
                    466,
                    489,
                    513,
                    536,
                ],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout with 15 columns. Multi-line Features text will be truncated (known limitation).",
    },
    "warlock": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [46],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Features",
            "Cantrips Known",
            "Invocations Known",
            "Spell Slots",
            "Slot Level",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 324,
                "y_max": 560,
                "column_boundaries": [92, 145, 242, 335, 393, 438, 489],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout with 7 columns (unique Pact Magic progression: fixed Spell Slots + Slot Level)",
    },
    "wizard": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [52],
        "headers": [
            "Level",
            "Proficiency Bonus",
            "Features",
            "Cantrips Known",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "5th",
            "6th",
            "7th",
            "8th",
            "9th",
        ],
        "regions": [
            {
                "x_min": 0,
                "x_max": 560,
                "y_min": 310,
                "y_max": 560,
                "column_boundaries": [86, 129, 240, 294, 317, 342, 366, 389, 413, 436, 459, 483],
            },
        ],
        "merge_continuation_rows": True,
        "chapter": "Classes",
        "data_driven": True,
        "confirmed": False,
        "validation": {"expected_rows": 20},
        "notes": "Single-column layout with 13 columns (Cantrips + spell slots 1st-9th)",
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
