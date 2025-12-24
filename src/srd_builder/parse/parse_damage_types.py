"""Parse damage type dataset.

This module contains the canonical 13 D&D 5e damage types. These are game constants
that don't require extraction from PDF - they're defined in the SRD on page 97.
"""

from __future__ import annotations

DAMAGE_TYPES_DATA = [
    {
        "simple_name": "acid",
        "name": "Acid",
        "description": [
            "The corrosive spray of a black dragon's breath and the dissolving enzymes secreted by a black pudding deal acid damage."
        ],
        "examples": ["black dragon breath", "black pudding enzymes"],
    },
    {
        "simple_name": "bludgeoning",
        "name": "Bludgeoning",
        "description": [
            "Blunt force attacks—hammers, falling, constriction, and the like—deal bludgeoning damage."
        ],
        "examples": ["hammers", "falling", "constriction"],
    },
    {
        "simple_name": "cold",
        "name": "Cold",
        "description": [
            "The infernal chill radiating from an ice devil's spear and the frigid blast of a white dragon's breath deal cold damage."
        ],
        "examples": ["ice devil spear", "white dragon breath"],
    },
    {
        "simple_name": "fire",
        "name": "Fire",
        "description": [
            "Red dragons breathe fire, and many spells conjure flames to deal fire damage."
        ],
        "examples": ["red dragon breath", "fireball spell", "flame tongue weapon"],
    },
    {
        "simple_name": "force",
        "name": "Force",
        "description": [
            "Force is pure magical energy focused into a damaging form. Most effects that deal force damage are spells, including magic missile and spiritual weapon."
        ],
        "examples": ["magic missile", "spiritual weapon"],
    },
    {
        "simple_name": "lightning",
        "name": "Lightning",
        "description": ["A lightning bolt spell and a blue dragon's breath deal lightning damage."],
        "examples": ["lightning bolt spell", "blue dragon breath"],
    },
    {
        "simple_name": "necrotic",
        "name": "Necrotic",
        "description": [
            "Necrotic damage, dealt by certain undead and a spell such as chill touch, withers matter and even the soul."
        ],
        "examples": ["undead touch", "chill touch spell"],
    },
    {
        "simple_name": "piercing",
        "name": "Piercing",
        "description": [
            "Puncturing and impaling attacks, including spears and monsters' bites, deal piercing damage."
        ],
        "examples": ["spears", "monster bites", "arrows"],
    },
    {
        "simple_name": "poison",
        "name": "Poison",
        "description": [
            "Venomous stings and the toxic gas of a green dragon's breath deal poison damage."
        ],
        "examples": ["venomous stings", "green dragon breath", "poison spray"],
    },
    {
        "simple_name": "psychic",
        "name": "Psychic",
        "description": [
            "Mental abilities such as a mind flayer's psionic blast deal psychic damage."
        ],
        "examples": ["mind flayer psionic blast", "psychic scream"],
    },
    {
        "simple_name": "radiant",
        "name": "Radiant",
        "description": [
            "Radiant damage, dealt by a cleric's flame strike spell or an angel's smiting weapon, sears the flesh like fire and overloads the spirit with power."
        ],
        "examples": ["flame strike spell", "angel weapon", "sacred flame"],
    },
    {
        "simple_name": "slashing",
        "name": "Slashing",
        "description": ["Swords, axes, and monsters' claws deal slashing damage."],
        "examples": ["swords", "axes", "monster claws"],
    },
    {
        "simple_name": "thunder",
        "name": "Thunder",
        "description": [
            "A concussive burst of sound, such as the effect of the thunderwave spell, deals thunder damage."
        ],
        "examples": ["thunderwave spell", "sonic attacks"],
    },
]


def parse_damage_types() -> list[dict]:
    """Parse damage type dataset.

    Returns canonical 13 D&D 5e damage types with descriptions.

    Returns:
        List of damage type records matching damage_type.schema.json
    """
    damage_types = []

    for dtype in DAMAGE_TYPES_DATA:
        damage_type = {
            "id": f"damage:{dtype['simple_name']}",
            "simple_name": dtype["simple_name"],
            "name": dtype["name"],
            "description": dtype["description"],
            "examples": dtype.get("examples", []),
            "page": 97,  # All damage types described on page 97
            "source": "SRD_CC_v5.1",
        }
        damage_types.append(damage_type)

    return damage_types
