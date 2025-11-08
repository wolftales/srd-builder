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

For migration status and remaining work, see docs/ROADMAP.md v0.9.9 section.
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
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [76],  # Actual PDF page number
        "headers": ["Score", "Modifier"],
        "regions": [
            # Left column: scores 1-11 (bottom of page)
            {"x_min": 0, "x_max": 300, "y_min": 615, "y_max": 690},
            # Right column: scores 12-30 (top of page)
            {"x_min": 300, "x_max": 560, "y_min": 70, "y_max": 180},
        ],
        "transformations": {
            "Score": {"strip": True},
            "Modifier": {"strip": True},
        },
        "chapter": "Using Ability Scores",
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
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [63, 64],
        "headers": ["Armor", "Cost", "Armor Class (AC)", "Stealth", "Weight"],
        "regions": [
            {
                "page": 63,
                "x_min": 52,
                "x_max": 300,
                "y_min": 678,
                "y_max": 695,  # Light Armor category + Padded (page 63)
                "column_boundaries": [78, 123, 193, 238],
            },
            {
                "page": 64,
                "x_min": 52,
                "x_max": 300,
                "y_min": 71,
                "y_max": 235,  # Leather through Shield (page 64)
                "column_boundaries": [78, 123, 193, 238],
            },
        ],
        "detect_categories": True,
        "validation": {"expected_rows": 17},  # 4 categories + 13 armor types
        "confirmed": True,
    },
    "container_capacity": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [69, 70],
        "headers": ["Container", "Capacity"],
        "regions": [
            {
                "page": 69,
                "x_min": 323,
                "x_max": 518,
                "y_min": 615,
                "y_max": 690,
                "column_boundaries": [69],
            },  # Page 69 bottom right
            {
                "page": 70,
                "x_min": 52,
                "x_max": 279,
                "y_min": 66,
                "y_max": 143,
                "column_boundaries": [69],
            },  # Page 70 top left
        ],
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,
        "validation": {"expected_rows": 13},
        "notes": "Container Capacity - multi-page extraction (page 69 bottom right + page 70 top left)",
    },
    "donning_doffing_armor": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [64],
        "headers": ["Category", "Don", "Doff"],
        "regions": [
            {"x_min": 52, "x_max": 220, "y_min": 385, "y_max": 425},
        ],
        "column_boundaries": [70, 122],  # Before Don(~122abs), Before Doff(~174abs)
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,
        "validation": {"expected_rows": 4},
        "notes": "Donning and Doffing Armor - time requirements for putting on and removing armor",
    },
    "exchange_rates": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [62],
        "headers": ["Coin", "CP", "SP", "EP", "GP", "PP"],
        "regions": [
            {"x_min": 52, "x_max": 271, "y_min": 531, "y_max": 595},
        ],
        "column_boundaries": [
            63,
            96,
            124,
            152,
            185,
        ],  # Boundaries placed BEFORE each column start: CP(~115), SP(~148), EP(~176), GP(~204), PP(~237)
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,  # Validated: exact match to legacy output
        "validation": {"expected_rows": 5},
        "notes": "Standard Exchange Rates - currency conversion table showing CP/SP/EP/GP/PP equivalencies",
    },
    "food_drink_lodging": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [74, 73],  # Multi-page extraction
        "headers": ["Item", "Cost"],
        "regions": [
            {
                "page": 74,
                "x_min": 52,
                "x_max": 300,
                "y_min": 100,
                "y_max": 295,  # Inn stay through Wine
                "column_boundaries": [94],  # Split at x=146 (52+94); Cost starts at x=146.4
            },
            {
                "page": 73,
                "x_min": 323,
                "x_max": 560,
                "y_min": 655,
                "y_max": 685,  # Ale section
                "column_boundaries": [94],  # Split at x=417 (323+94); Cost starts at x=417.4
            },
        ],
        "detect_categories": True,
        "validation": {"expected_rows": 21},  # 4 categories + 17 items
        "confirmed": True,
    },
    "lifestyle_expenses": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [72, 73],
        "headers": ["Lifestyle", "Price/Day"],
        "regions": [
            {
                "page": 72,
                "x_min": 323,
                "x_max": 546,
                "y_min": 675,
                "y_max": 695,
                "column_boundaries": [77],
            },  # Page 72 right: Wretched (y=680), Squalid (y=691)
            {
                "page": 73,
                "x_min": 52,
                "x_max": 200,
                "y_min": 70,
                "y_max": 127,
                "column_boundaries": [58],
            },  # Page 73 left: Poor through Aristocratic (boundary before "10" at x~110)
        ],
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,
        "validation": {"expected_rows": 7},  # PDF has 7 lifestyle levels including Wretched
        "notes": "Lifestyle Expenses - PDF source truth: includes Wretched (—) and preserves 'minimum' on Aristocratic (10 gp minimum)",
    },
    "mounts_and_other_animals": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [71, 72],
        "headers": ["Item", "Cost", "Speed", "Carrying Capacity"],
        "regions": [
            {
                "page": 71,
                "x_min": 323,
                "x_max": 500,
                "y_min": 660,
                "y_max": 695,
                "column_boundaries": [73, 107, 143],
            },  # Page 71 right: Camel, Donkey/mule, Elephant (boundary at x=396, before '200' at x=397.5)
            {
                "page": 72,
                "x_min": 52,
                "x_max": 225,
                "y_min": 66,
                "y_max": 120,
                "column_boundaries": [74, 108, 143],
            },  # Page 72 left: Horses, Mastiff, Pony, Warhorse
        ],
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,
        "validation": {"expected_rows": 8},  # 3 animals page 71 + 5 animals page 72
        "notes": "Mounts and Other Animals - Multi-page 4-column table",
    },
    "services": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [74],
        "headers": ["Service", "Cost"],
        "regions": [
            {
                "x_min": 323,
                "x_max": 560,
                "y_min": 95,
                "y_max": 195,  # Covers Coach cab through Ship's passage
                "column_boundaries": [77],  # Split at x=400 (323+77); Cost column starts at x=405
            }
        ],
        "detect_categories": True,
        "validation": {"expected_rows": 9},  # 2 categories + 4 sub-items + 3 standalone services
        "confirmed": True,
    },
    "tack_harness_vehicles": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [72],
        "headers": ["Item", "Cost", "Weight"],
        "regions": [
            {
                "x_min": 52,
                "x_max": 300,
                "y_min": 168,
                "y_max": 325,  # Covers Barding through Stabling
                "column_boundaries": [78, 113],  # Item/Cost at x=130, Cost/Weight at x=165
            }
        ],
        "detect_categories": True,
        "validation": {"expected_rows": 14},  # 1 category (Saddle) + 13 items
        "confirmed": True,
    },
    "tools": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [70],
        "headers": ["Item", "Cost", "Weight"],
        "regions": [
            {
                "x_min": 323,
                "x_max": 550,
                "y_min": 150,
                "y_max": 570,
                "column_boundaries": [102, 132],
            },  # Page 70 right: All tools with 3 categories (ends with Thieves' tools at y=560)
        ],
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,
        "detect_categories": True,
        "validation": {"expected_rows": 38},  # 3 categories + 35 items
        "notes": "Tools table with categories: Artisan's tools, Gaming set, Musical instrument",
    },
    "trade_goods": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [72],
        "headers": ["Cost", "Goods"],
        "regions": [
            {"x_min": 323, "x_max": 501, "y_min": 84, "y_max": 248},
        ],
        "column_boundaries": [31],  # Before Goods column (~360abs)
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,
        "validation": {"expected_rows": 13},  # Actually 13, not 15
        "notes": "Trade Goods - commodity costs per unit (wheat, flour, iron, spices, livestock, metals)",
    },
    "waterborne_vehicles": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [72],
        "headers": ["Item", "Cost", "Speed"],
        "regions": [
            {"x_min": 52, "x_max": 190, "y_min": 383, "y_max": 445},
        ],
        "column_boundaries": [55, 102],  # Before Cost(~107abs), Before Speed(~154abs)
        "chapter": "Chapter 5: Equipment",
        "data_driven": True,
        "confirmed": True,
        "validation": {"expected_rows": 6},
        "notes": "Waterborne Vehicles - costs and speeds for ships and boats",
    },
    "weapons": {
        "pattern_type": "split_column",
        "source": "srd",
        "pages": [65, 66],
        "headers": ["Name", "Cost", "Damage", "Weight"],
        "regions": [
            {
                "page": 65,
                "x_min": 52,
                "x_max": 300,
                "y_min": 678,
                "y_max": 685,  # Simple Melee Weapons category header (page 65)
                "column_boundaries": [103, 133, 208],
            },
            {
                "page": 66,
                "x_min": 52,
                "x_max": 300,
                "y_min": 60,
                "y_max": 505,  # All weapons from Club through Net (page 66)
                "column_boundaries": [103, 133, 208],
            },
        ],
        "detect_categories": True,
        "validation": {"expected_rows": 41},  # 4 categories + 37 weapons
        "confirmed": True,
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
