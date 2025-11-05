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
