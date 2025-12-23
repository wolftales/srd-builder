"""Parse ability_scores dataset.

This module provides the 6 core D&D 5e ability scores as static data.
No PDF extraction is required - these are game constants.

Source: SRD pages 76-78 (ability score descriptions)
"""

from __future__ import annotations

__all__ = ["parse_ability_scores"]

# The 6 core D&D 5e ability scores from SRD pages 76-78
ABILITY_SCORES_DATA = [
    {
        "id": "ability:strength",
        "simple_name": "strength",
        "name": "Strength",
        "abbreviation": "STR",
        "description": [
            "Strength measures bodily power, athletic training, and the extent to which you can exert raw physical force."
        ],
        "skills": ["skill:athletics"],
        "page": 76,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "ability:dexterity",
        "simple_name": "dexterity",
        "name": "Dexterity",
        "abbreviation": "DEX",
        "description": ["Dexterity measures agility, reflexes, and balance."],
        "skills": ["skill:acrobatics", "skill:sleight_of_hand", "skill:stealth"],
        "page": 77,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "ability:constitution",
        "simple_name": "constitution",
        "name": "Constitution",
        "abbreviation": "CON",
        "description": ["Constitution measures health, stamina, and vital force."],
        "skills": [],
        "page": 77,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "ability:intelligence",
        "simple_name": "intelligence",
        "name": "Intelligence",
        "abbreviation": "INT",
        "description": [
            "Intelligence measures mental acuity, accuracy of recall, and the ability to reason."
        ],
        "skills": [
            "skill:arcana",
            "skill:history",
            "skill:investigation",
            "skill:nature",
            "skill:religion",
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "ability:wisdom",
        "simple_name": "wisdom",
        "name": "Wisdom",
        "abbreviation": "WIS",
        "description": [
            "Wisdom reflects how attuned you are to the world around you and represents perceptiveness and intuition."
        ],
        "skills": [
            "skill:animal_handling",
            "skill:insight",
            "skill:medicine",
            "skill:perception",
            "skill:survival",
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "ability:charisma",
        "simple_name": "charisma",
        "name": "Charisma",
        "abbreviation": "CHA",
        "description": [
            "Charisma measures your ability to interact effectively with others. It includes such factors as confidence and eloquence, and it can represent a charming or commanding personality."
        ],
        "skills": [
            "skill:deception",
            "skill:intimidation",
            "skill:performance",
            "skill:persuasion",
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
]


def parse_ability_scores() -> list[dict]:
    """Parse ability scores dataset.

    Returns:
        List of 6 ability score records (STR, DEX, CON, INT, WIS, CHA)

    Note:
        This returns static data - the 6 core ability scores are game constants.
        Descriptions are from SRD "Using Ability Scores" chapter (pages 76-78).
    """
    # Return a copy to prevent mutation
    return [dict(ability) for ability in ABILITY_SCORES_DATA]
