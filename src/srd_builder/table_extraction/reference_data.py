"""Reference table data for SRD 5.1.

This module contains hardcoded table data that cannot be reliably extracted
from the PDF due to formatting issues. Data is organized by extraction pattern.

All data is sourced from SRD 5.1 and matches the official rulebook.
"""

from typing import Any

# ============================================================================
# CALCULATED REFERENCE TABLES
# These tables are generated from formulas rather than hardcoded data
# ============================================================================

CALCULATED_TABLES = {
    "ability_scores_and_modifiers": {
        "formula": lambda score: (score - 10) // 2,
        "range": range(1, 31),
        "headers": ["Score", "Modifier"],
        "format_modifier": lambda mod: f"+{mod}" if mod > 0 else str(mod),
    },
    "proficiency_bonus": {
        "data": {
            range(1, 5): "+2",
            range(5, 9): "+3",
            range(9, 13): "+4",
            range(13, 17): "+5",
            range(17, 21): "+6",
        },
        "headers": ["Level", "Proficiency Bonus"],
    },
    "carrying_capacity": {
        "formula": lambda strength: strength * 15,
        "range": range(1, 31),
        "headers": ["Strength Score", "Carrying Capacity (lbs)"],
    },
}

# ============================================================================
# STATIC REFERENCE TABLES
# Simple lookup tables with fixed data
# ============================================================================

REFERENCE_TABLES: dict[str, dict[str, Any]] = {
    "experience_by_cr": {
        "headers": ["Challenge Rating", "XP"],
        "rows": [
            ["0", 0],
            ["1/8", 25],
            ["1/4", 50],
            ["1/2", 100],
            ["1", 200],
            ["2", 450],
            ["3", 700],
            ["4", 1100],
            ["5", 1800],
            ["6", 2300],
            ["7", 2900],
            ["8", 3900],
            ["9", 5000],
            ["10", 5900],
            ["11", 7200],
            ["12", 8400],
            ["13", 10000],
            ["14", 11500],
            ["15", 13000],
            ["16", 15000],
            ["17", 18000],
            ["18", 20000],
            ["19", 22000],
            ["20", 25000],
            ["21", 33000],
            ["22", 41000],
            ["23", 50000],
            ["24", 62000],
            ["25", 75000],
            ["26", 90000],
            ["27", 105000],
            ["28", 120000],
            ["29", 135000],
            ["30", 155000],
        ],
    },
    "spell_slots_by_level": {
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
        "notes": "Full caster progression (Cleric, Druid, Wizard)",
    },
    "cantrip_damage": {
        "headers": ["Character Level", "Damage"],
        "rows": [
            ["1st-4th", "1 die"],
            ["5th-10th", "2 dice"],
            ["11th-16th", "3 dice"],
            ["17th-20th", "4 dice"],
        ],
    },
    "travel_pace": {
        "headers": ["Pace", "Distance per Minute", "Distance per Hour", "Distance per Day"],
        "rows": [
            ["Fast", "400 feet", "4 miles", "30 miles"],
            ["Normal", "300 feet", "3 miles", "24 miles"],
            ["Slow", "200 feet", "2 miles", "18 miles"],
        ],
    },
    "creature_size": {
        "headers": ["Size", "Space"],
        "rows": [
            ["Tiny", "2½ by 2½ ft."],
            ["Small", "5 by 5 ft."],
            ["Medium", "5 by 5 ft."],
            ["Large", "10 by 10 ft."],
            ["Huge", "15 by 15 ft."],
            ["Gargantuan", "20 by 20 ft. or larger"],
        ],
    },
}

# ============================================================================
# PRICING TABLES
# Item/service tables with costs
# NOTE: food_drink_lodging, services, and lifestyle_expenses moved to TEXT_PARSED_TABLES
# to use coordinate-based PDF extraction instead of hardcoded data (v0.9.3)
# ============================================================================

PRICING_TABLES: dict[str, dict[str, Any]] = {
    # All pricing tables now extracted via TEXT_PARSED_TABLES
}

# ============================================================================
# TEXT-PARSED TABLES
# Tables extracted via text parsing (no grid borders in PDF)
# ============================================================================

TEXT_PARSED_TABLES = {
    "adventure_gear": {
        "parser": "parse_adventure_gear_table",
        "pages": [69],
    },
    "armor": {
        "parser": "parse_armor_table",
        "pages": [63, 64],
    },
    "container_capacity": {
        "parser": "parse_container_capacity_table",
        "pages": [69, 70],
    },
    "donning_doffing_armor": {
        "parser": "parse_donning_doffing_armor_table",
        "pages": [64],
    },
    "exchange_rates": {
        "parser": "parse_exchange_rates_table",
        "pages": [62],
    },
    "food_drink_lodging": {
        "parser": "parse_food_drink_lodging_table",
        "pages": [73, 74],
    },
    "lifestyle_expenses": {
        "parser": "parse_lifestyle_expenses_table",
        "pages": [72, 73],
    },
    "mounts_and_other_animals": {
        "parser": "parse_mounts_and_other_animals_table",
        "pages": [71, 72],
    },
    "services": {
        "parser": "parse_services_table",
        "pages": [74],
    },
    "tack_harness_vehicles": {
        "parser": "parse_tack_harness_vehicles_table",
        "pages": [72],
    },
    "tools": {
        "parser": "parse_tools_table",
        "pages": [70],
    },
    "trade_goods": {
        "parser": "parse_trade_goods_table",
        "pages": [72],
    },
    "waterborne_vehicles": {
        "parser": "parse_waterborne_vehicles_table",
        "pages": [72],
    },
    "weapons": {
        "parser": "parse_weapons_table",
        "pages": [65, 66],
    },
}

# ============================================================================
# CLASS PROGRESSION TABLES
# Level 1-20 progression for all 12 classes
# ============================================================================

CLASS_PROGRESSIONS: dict[str, dict[str, Any]] = {
    "barbarian": {
        "headers": ["Level", "Proficiency Bonus", "Features", "Rages", "Rage Damage"],
        "rows": [
            [1, "+2", "Rage, Unarmored Defense", 2, "+2"],
            [2, "+2", "Reckless Attack, Danger Sense", 2, "+2"],
            [3, "+2", "Primal Path", 3, "+2"],
            [4, "+2", "Ability Score Improvement", 3, "+2"],
            [5, "+3", "Extra Attack, Fast Movement", 3, "+2"],
            [6, "+3", "Path feature", 4, "+2"],
            [7, "+3", "Feral Instinct", 4, "+2"],
            [8, "+3", "Ability Score Improvement", 4, "+2"],
            [9, "+4", "Brutal Critical (1 die)", 4, "+3"],
            [10, "+4", "Path feature", 4, "+3"],
            [11, "+4", "Relentless Rage", 4, "+3"],
            [12, "+4", "Ability Score Improvement", 5, "+3"],
            [13, "+5", "Brutal Critical (2 dice)", 5, "+3"],
            [14, "+5", "Path feature", 5, "+3"],
            [15, "+5", "Persistent Rage", 5, "+3"],
            [16, "+5", "Ability Score Improvement", 5, "+4"],
            [17, "+6", "Brutal Critical (3 dice)", 6, "+4"],
            [18, "+6", "Indomitable Might", 6, "+4"],
            [19, "+6", "Ability Score Improvement", 6, "+4"],
            [20, "+6", "Primal Champion", "Unlimited", "+4"],
        ],
    },
    "bard": {
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
        "rows": [
            [1, "+2", "Spellcasting, Bardic Inspiration (d6)", 2, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, "+2", "Jack of All Trades, Song of Rest (d6)", 2, 5, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, "+2", "Bard College, Expertise", 2, 6, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 3, 7, 4, 3, 0, 0, 0, 0, 0, 0, 0],
            [
                5,
                "+3",
                "Bardic Inspiration (d8), Font of Inspiration",
                3,
                8,
                4,
                3,
                2,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [6, "+3", "Countercharm, Bard College feature", 3, 9, 4, 3, 3, 0, 0, 0, 0, 0, 0],
            [7, "+3", "—", 3, 10, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [8, "+3", "Ability Score Improvement", 3, 11, 4, 3, 3, 2, 0, 0, 0, 0, 0],
            [9, "+4", "Song of Rest (d8)", 3, 12, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [
                10,
                "+4",
                "Bardic Inspiration (d10), Expertise, Magical Secrets",
                4,
                14,
                4,
                3,
                3,
                3,
                2,
                0,
                0,
                0,
                0,
            ],
            [11, "+4", "—", 4, 15, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 4, 15, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "Song of Rest (d10)", 4, 16, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Magical Secrets, Bard College feature", 4, 18, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "Bardic Inspiration (d12)", 4, 19, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 4, 19, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [17, "+6", "Song of Rest (d12)", 4, 20, 4, 3, 3, 3, 2, 1, 1, 1, 1],
            [18, "+6", "Magical Secrets", 4, 22, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 4, 22, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Superior Inspiration", 4, 22, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ],
    },
    "cleric": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Cantrips Known", "type": "integer"},
            {"name": "1st", "type": "integer"},
            {"name": "2nd", "type": "integer"},
            {"name": "3rd", "type": "integer"},
            {"name": "4th", "type": "integer"},
            {"name": "5th", "type": "integer"},
            {"name": "6th", "type": "integer"},
            {"name": "7th", "type": "integer"},
            {"name": "8th", "type": "integer"},
            {"name": "9th", "type": "integer"},
        ],
        "rows": [
            [1, "+2", "Spellcasting, Divine Domain", 3, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [
                2,
                "+2",
                "Channel Divinity (1/rest), Divine Domain feature",
                3,
                3,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [3, "+2", "—", 3, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 4, 4, 3, 0, 0, 0, 0, 0, 0, 0],
            [5, "+3", "Destroy Undead (CR 1/2)", 4, 4, 3, 2, 0, 0, 0, 0, 0, 0],
            [
                6,
                "+3",
                "Channel Divinity (2/rest), Divine Domain feature",
                4,
                4,
                3,
                3,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [7, "+3", "—", 4, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [
                8,
                "+3",
                "Ability Score Improvement, Destroy Undead (CR 1), Divine Domain feature",
                4,
                4,
                3,
                3,
                2,
                0,
                0,
                0,
                0,
                0,
            ],
            [9, "+4", "—", 4, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [10, "+4", "Divine Intervention", 5, 4, 3, 3, 3, 2, 0, 0, 0, 0],
            [11, "+4", "Destroy Undead (CR 2)", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Destroy Undead (CR 3)", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [
                17,
                "+6",
                "Destroy Undead (CR 4), Divine Domain feature",
                5,
                4,
                3,
                3,
                3,
                2,
                1,
                1,
                1,
                1,
            ],
            [18, "+6", "Channel Divinity (3/rest)", 5, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 5, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Divine Intervention improvement", 5, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ],
    },
    "druid": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Cantrips Known", "type": "integer"},
            {"name": "1st", "type": "integer"},
            {"name": "2nd", "type": "integer"},
            {"name": "3rd", "type": "integer"},
            {"name": "4th", "type": "integer"},
            {"name": "5th", "type": "integer"},
            {"name": "6th", "type": "integer"},
            {"name": "7th", "type": "integer"},
            {"name": "8th", "type": "integer"},
            {"name": "9th", "type": "integer"},
        ],
        "rows": [
            [1, "+2", "Druidic, Spellcasting", 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, "+2", "Wild Shape, Druid Circle", 2, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, "+2", "—", 2, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [
                4,
                "+2",
                "Wild Shape improvement, Ability Score Improvement",
                3,
                4,
                3,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [5, "+3", "—", 3, 4, 3, 2, 0, 0, 0, 0, 0, 0],
            [6, "+3", "Druid Circle feature", 3, 4, 3, 3, 0, 0, 0, 0, 0, 0],
            [7, "+3", "—", 3, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [
                8,
                "+3",
                "Wild Shape improvement, Ability Score Improvement",
                3,
                4,
                3,
                3,
                2,
                0,
                0,
                0,
                0,
                0,
            ],
            [9, "+4", "—", 3, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [10, "+4", "Druid Circle feature", 4, 4, 3, 3, 3, 2, 0, 0, 0, 0],
            [11, "+4", "—", 4, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 4, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "—", 4, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Druid Circle feature", 4, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "—", 4, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 4, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [17, "+6", "—", 4, 4, 3, 3, 3, 2, 1, 1, 1, 1],
            [18, "+6", "Timeless Body, Beast Spells", 4, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 4, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Archdruid", 4, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ],
    },
    "fighter": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
        ],
        "rows": [
            [1, "+2", "Fighting Style, Second Wind"],
            [2, "+2", "Action Surge (one use)"],
            [3, "+2", "Martial Archetype"],
            [4, "+2", "Ability Score Improvement"],
            [5, "+3", "Extra Attack"],
            [6, "+3", "Ability Score Improvement"],
            [7, "+3", "Martial Archetype feature"],
            [8, "+3", "Ability Score Improvement"],
            [9, "+4", "Indomitable (one use)"],
            [10, "+4", "Martial Archetype feature"],
            [11, "+4", "Extra Attack (2)"],
            [12, "+4", "Ability Score Improvement"],
            [13, "+5", "Indomitable (two uses)"],
            [14, "+5", "Ability Score Improvement"],
            [15, "+5", "Martial Archetype feature"],
            [16, "+5", "Ability Score Improvement"],
            [17, "+6", "Action Surge (two uses), Indomitable (three uses)"],
            [18, "+6", "Martial Archetype feature"],
            [19, "+6", "Ability Score Improvement"],
            [20, "+6", "Extra Attack (3)"],
        ],
    },
    "monk": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Martial Arts", "type": "dice"},
            {"name": "Ki Points", "type": "mixed"},
            {"name": "Unarmored Movement", "type": "string"},
        ],
        "rows": [
            [1, "+2", "Unarmored Defense, Martial Arts", "1d4", "—", "—"],
            [2, "+2", "Ki, Unarmored Movement", "1d4", 2, "+10 ft."],
            [3, "+2", "Monastic Tradition, Deflect Missiles", "1d4", 3, "+10 ft."],
            [4, "+2", "Ability Score Improvement, Slow Fall", "1d4", 4, "+10 ft."],
            [5, "+3", "Extra Attack, Stunning Strike", "1d6", 5, "+10 ft."],
            [6, "+3", "Ki-Empowered Strikes, Monastic Tradition feature", "1d6", 6, "+15 ft."],
            [7, "+3", "Evasion, Stillness of Mind", "1d6", 7, "+15 ft."],
            [8, "+3", "Ability Score Improvement", "1d6", 8, "+15 ft."],
            [9, "+4", "Unarmored Movement improvement", "1d6", 9, "+15 ft."],
            [10, "+4", "Purity of Body", "1d6", 10, "+20 ft."],
            [11, "+4", "Monastic Tradition feature", "1d8", 11, "+20 ft."],
            [12, "+4", "Ability Score Improvement", "1d8", 12, "+20 ft."],
            [13, "+5", "Tongue of the Sun and Moon", "1d8", 13, "+20 ft."],
            [14, "+5", "Diamond Soul", "1d8", 14, "+25 ft."],
            [15, "+5", "Timeless Body", "1d8", 15, "+25 ft."],
            [16, "+5", "Ability Score Improvement", "1d8", 16, "+25 ft."],
            [17, "+6", "Monastic Tradition feature", "1d10", 17, "+25 ft."],
            [18, "+6", "Empty Body", "1d10", 18, "+30 ft."],
            [19, "+6", "Ability Score Improvement", "1d10", 19, "+30 ft."],
            [20, "+6", "Perfect Self", "1d10", 20, "+30 ft."],
        ],
    },
    "paladin": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "1st", "type": "integer"},
            {"name": "2nd", "type": "integer"},
            {"name": "3rd", "type": "integer"},
            {"name": "4th", "type": "integer"},
            {"name": "5th", "type": "integer"},
        ],
        "rows": [
            [1, "+2", "Divine Sense, Lay on Hands", 0, 0, 0, 0, 0],
            [2, "+2", "Fighting Style, Spellcasting, Divine Smite", 2, 0, 0, 0, 0],
            [3, "+2", "Divine Health, Sacred Oath", 3, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 3, 0, 0, 0, 0],
            [5, "+3", "Extra Attack", 4, 2, 0, 0, 0],
            [6, "+3", "Aura of Protection", 4, 2, 0, 0, 0],
            [7, "+3", "Sacred Oath feature", 4, 3, 0, 0, 0],
            [8, "+3", "Ability Score Improvement", 4, 3, 0, 0, 0],
            [9, "+4", "—", 4, 3, 2, 0, 0],
            [10, "+4", "Aura of Courage", 4, 3, 2, 0, 0],
            [11, "+4", "Improved Divine Smite", 4, 3, 3, 0, 0],
            [12, "+4", "Ability Score Improvement", 4, 3, 3, 0, 0],
            [13, "+5", "—", 4, 3, 3, 1, 0],
            [14, "+5", "Cleansing Touch", 4, 3, 3, 1, 0],
            [15, "+5", "Sacred Oath feature", 4, 3, 3, 2, 0],
            [16, "+5", "Ability Score Improvement", 4, 3, 3, 2, 0],
            [17, "+6", "—", 4, 3, 3, 3, 1],
            [18, "+6", "Aura improvements", 4, 3, 3, 3, 1],
            [19, "+6", "Ability Score Improvement", 4, 3, 3, 3, 2],
            [20, "+6", "Sacred Oath feature", 4, 3, 3, 3, 2],
        ],
    },
    "ranger": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Spells Known", "type": "integer"},
            {"name": "1st", "type": "integer"},
            {"name": "2nd", "type": "integer"},
            {"name": "3rd", "type": "integer"},
            {"name": "4th", "type": "integer"},
            {"name": "5th", "type": "integer"},
        ],
        "rows": [
            [1, "+2", "Favored Enemy, Natural Explorer", 0, 0, 0, 0, 0, 0],
            [2, "+2", "Fighting Style, Spellcasting", 2, 2, 0, 0, 0, 0],
            [3, "+2", "Ranger Archetype, Primeval Awareness", 3, 3, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 3, 3, 0, 0, 0, 0],
            [5, "+3", "Extra Attack", 4, 4, 2, 0, 0, 0],
            [6, "+3", "Favored Enemy and Natural Explorer improvements", 4, 4, 2, 0, 0, 0],
            [7, "+3", "Ranger Archetype feature", 5, 4, 3, 0, 0, 0],
            [8, "+3", "Ability Score Improvement, Land's Stride", 5, 4, 3, 0, 0, 0],
            [9, "+4", "—", 6, 4, 3, 2, 0, 0],
            [10, "+4", "Natural Explorer improvement, Hide in Plain Sight", 6, 4, 3, 2, 0, 0],
            [11, "+4", "Ranger Archetype feature", 7, 4, 3, 3, 0, 0],
            [12, "+4", "Ability Score Improvement", 7, 4, 3, 3, 0, 0],
            [13, "+5", "—", 8, 4, 3, 3, 1, 0],
            [14, "+5", "Favored Enemy improvement, Vanish", 8, 4, 3, 3, 1, 0],
            [15, "+5", "Ranger Archetype feature", 9, 4, 3, 3, 2, 0],
            [16, "+5", "Ability Score Improvement", 9, 4, 3, 3, 2, 0],
            [17, "+6", "—", 10, 4, 3, 3, 3, 1],
            [18, "+6", "Feral Senses", 10, 4, 3, 3, 3, 1],
            [19, "+6", "Ability Score Improvement", 11, 4, 3, 3, 3, 2],
            [20, "+6", "Foe Slayer", 11, 4, 3, 3, 3, 2],
        ],
    },
    "rogue": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Sneak Attack", "type": "dice"},
        ],
        "rows": [
            [1, "+2", "Expertise, Sneak Attack, Thieves' Cant", "1d6"],
            [2, "+2", "Cunning Action", "1d6"],
            [3, "+2", "Roguish Archetype", "2d6"],
            [4, "+2", "Ability Score Improvement", "2d6"],
            [5, "+3", "Uncanny Dodge", "3d6"],
            [6, "+3", "Expertise", "3d6"],
            [7, "+3", "Evasion", "4d6"],
            [8, "+3", "Ability Score Improvement", "4d6"],
            [9, "+4", "Roguish Archetype feature", "5d6"],
            [10, "+4", "Ability Score Improvement", "5d6"],
            [11, "+4", "Reliable Talent", "6d6"],
            [12, "+4", "Ability Score Improvement", "6d6"],
            [13, "+5", "Roguish Archetype feature", "7d6"],
            [14, "+5", "Blindsense", "7d6"],
            [15, "+5", "Slippery Mind", "8d6"],
            [16, "+5", "Ability Score Improvement", "8d6"],
            [17, "+6", "Roguish Archetype feature", "9d6"],
            [18, "+6", "Elusive", "9d6"],
            [19, "+6", "Ability Score Improvement", "10d6"],
            [20, "+6", "Stroke of Luck", "10d6"],
        ],
    },
    "sorcerer": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Cantrips Known", "type": "integer"},
            {"name": "Spells Known", "type": "integer"},
            {"name": "1st", "type": "integer"},
            {"name": "2nd", "type": "integer"},
            {"name": "3rd", "type": "integer"},
            {"name": "4th", "type": "integer"},
            {"name": "5th", "type": "integer"},
            {"name": "6th", "type": "integer"},
            {"name": "7th", "type": "integer"},
            {"name": "8th", "type": "integer"},
            {"name": "9th", "type": "integer"},
            {"name": "Sorcery Points", "type": "mixed"},
        ],
        "rows": [
            [1, "+2", "Spellcasting, Sorcerous Origin", 4, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, "—"],
            [2, "+2", "Font of Magic", 4, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 2],
            [3, "+2", "Metamagic", 4, 4, 4, 2, 0, 0, 0, 0, 0, 0, 0, 3],
            [4, "+2", "Ability Score Improvement", 5, 5, 4, 3, 0, 0, 0, 0, 0, 0, 0, 4],
            [5, "+3", "—", 5, 6, 4, 3, 2, 0, 0, 0, 0, 0, 0, 5],
            [6, "+3", "Sorcerous Origin feature", 5, 7, 4, 3, 3, 0, 0, 0, 0, 0, 0, 6],
            [7, "+3", "—", 5, 8, 4, 3, 3, 1, 0, 0, 0, 0, 0, 7],
            [8, "+3", "Ability Score Improvement", 5, 9, 4, 3, 3, 2, 0, 0, 0, 0, 0, 8],
            [9, "+4", "—", 5, 10, 4, 3, 3, 3, 1, 0, 0, 0, 0, 9],
            [10, "+4", "Metamagic", 6, 11, 4, 3, 3, 3, 2, 0, 0, 0, 0, 10],
            [11, "+4", "—", 6, 12, 4, 3, 3, 3, 2, 1, 0, 0, 0, 11],
            [12, "+4", "Ability Score Improvement", 6, 12, 4, 3, 3, 3, 2, 1, 0, 0, 0, 12],
            [13, "+5", "—", 6, 13, 4, 3, 3, 3, 2, 1, 1, 0, 0, 13],
            [14, "+5", "Sorcerous Origin feature", 6, 13, 4, 3, 3, 3, 2, 1, 1, 0, 0, 14],
            [15, "+5", "—", 6, 14, 4, 3, 3, 3, 2, 1, 1, 1, 0, 15],
            [16, "+5", "Ability Score Improvement", 6, 14, 4, 3, 3, 3, 2, 1, 1, 1, 0, 16],
            [17, "+6", "Metamagic", 6, 15, 4, 3, 3, 3, 2, 1, 1, 1, 1, 17],
            [18, "+6", "Sorcerous Origin feature", 6, 15, 4, 3, 3, 3, 3, 1, 1, 1, 1, 18],
            [19, "+6", "Ability Score Improvement", 6, 15, 4, 3, 3, 3, 3, 2, 1, 1, 1, 19],
            [20, "+6", "Sorcerous Restoration", 6, 15, 4, 3, 3, 3, 3, 2, 2, 1, 1, 20],
        ],
    },
    "warlock": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Cantrips Known", "type": "integer"},
            {"name": "Spells Known", "type": "integer"},
            {"name": "Spell Slots", "type": "integer"},
            {"name": "Slot Level", "type": "string"},
            {"name": "Invocations Known", "type": "integer"},
        ],
        "rows": [
            [1, "+2", "Otherworldly Patron, Pact Magic", 2, 2, 1, "1st", 0],
            [2, "+2", "Eldritch Invocations", 2, 3, 2, "1st", 2],
            [3, "+2", "Pact Boon", 2, 4, 2, "2nd", 2],
            [4, "+2", "Ability Score Improvement", 3, 5, 2, "2nd", 2],
            [5, "+3", "—", 3, 6, 2, "3rd", 3],
            [6, "+3", "Otherworldly Patron feature", 3, 7, 2, "3rd", 3],
            [7, "+3", "—", 3, 8, 2, "4th", 4],
            [8, "+3", "Ability Score Improvement", 3, 9, 2, "4th", 4],
            [9, "+4", "—", 3, 10, 2, "5th", 5],
            [10, "+4", "Otherworldly Patron feature", 4, 10, 2, "5th", 5],
            [11, "+4", "Mystic Arcanum (6th level)", 4, 11, 3, "5th", 5],
            [12, "+4", "Ability Score Improvement", 4, 11, 3, "5th", 6],
            [13, "+5", "Mystic Arcanum (7th level)", 4, 12, 3, "5th", 6],
            [14, "+5", "Otherworldly Patron feature", 4, 12, 3, "5th", 6],
            [15, "+5", "Mystic Arcanum (8th level)", 4, 13, 3, "5th", 7],
            [16, "+5", "Ability Score Improvement", 4, 13, 3, "5th", 7],
            [17, "+6", "Mystic Arcanum (9th level)", 4, 14, 4, "5th", 7],
            [18, "+6", "—", 4, 14, 4, "5th", 8],
            [19, "+6", "Ability Score Improvement", 4, 15, 4, "5th", 8],
            [20, "+6", "Eldritch Master", 4, 15, 4, "5th", 8],
        ],
    },
    "wizard": {
        "headers": [
            {"name": "Level", "type": "integer"},
            {"name": "Proficiency Bonus", "type": "string"},
            {"name": "Features", "type": "string"},
            {"name": "Cantrips Known", "type": "integer"},
            {"name": "1st", "type": "integer"},
            {"name": "2nd", "type": "integer"},
            {"name": "3rd", "type": "integer"},
            {"name": "4th", "type": "integer"},
            {"name": "5th", "type": "integer"},
            {"name": "6th", "type": "integer"},
            {"name": "7th", "type": "integer"},
            {"name": "8th", "type": "integer"},
            {"name": "9th", "type": "integer"},
        ],
        "rows": [
            [1, "+2", "Spellcasting, Arcane Recovery", 3, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, "+2", "Arcane Tradition", 3, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, "+2", "—", 3, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 4, 4, 3, 0, 0, 0, 0, 0, 0, 0],
            [5, "+3", "—", 4, 4, 3, 2, 0, 0, 0, 0, 0, 0],
            [6, "+3", "Arcane Tradition feature", 4, 4, 3, 3, 0, 0, 0, 0, 0, 0],
            [7, "+3", "—", 4, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [8, "+3", "Ability Score Improvement", 4, 4, 3, 3, 2, 0, 0, 0, 0, 0],
            [9, "+4", "—", 4, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [10, "+4", "Arcane Tradition feature", 5, 4, 3, 3, 3, 2, 0, 0, 0, 0],
            [11, "+4", "—", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Arcane Tradition feature", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [17, "+6", "—", 5, 4, 3, 3, 3, 2, 1, 1, 1, 1],
            [18, "+6", "Spell Mastery", 5, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 5, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Signature Spell", 5, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ],
    },
}


def get_table_data(simple_name: str) -> dict[str, Any] | None:
    """Get reference data for a table by simple_name.

    Args:
        simple_name: Table simple_name (e.g., "barbarian_progression")

    Returns:
        Table configuration dict or None if not found
    """
    # Check class progressions (strip _progression suffix)
    if simple_name.endswith("_progression"):
        class_name = simple_name.replace("_progression", "")
        if class_name in CLASS_PROGRESSIONS:
            return CLASS_PROGRESSIONS[class_name]
    elif simple_name in CLASS_PROGRESSIONS:
        return CLASS_PROGRESSIONS[simple_name]

    # Check reference tables
    if simple_name in REFERENCE_TABLES:
        return REFERENCE_TABLES[simple_name]

    # Check text-parsed tables first (requires PDF path - handled by caller)
    # These are extracted directly from PDF using coordinate-based parsing
    if simple_name in TEXT_PARSED_TABLES:
        return {"type": "text_parsed", "config": TEXT_PARSED_TABLES[simple_name]}

    # Check pricing tables (currently empty - all migrated to TEXT_PARSED)
    if simple_name in PRICING_TABLES:
        return PRICING_TABLES[simple_name]

    # Check calculated tables
    if simple_name in CALCULATED_TABLES:
        config = CALCULATED_TABLES[simple_name]
        return dict(config) if isinstance(config, dict) else None

    return None
