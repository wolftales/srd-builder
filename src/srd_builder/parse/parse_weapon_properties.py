"""Parse weapon_properties dataset.

This module provides the 10 D&D 5e weapon properties as static data.
No PDF extraction is required - these are game constants.

Source: SRD page 147 (weapon properties in Equipment chapter)
"""

from __future__ import annotations

__all__ = ["parse_weapon_properties"]

# The 10 D&D 5e weapon properties from SRD page 147
WEAPON_PROPERTIES_DATA = [
    {
        "id": "weapon_property:ammunition",
        "simple_name": "ammunition",
        "name": "Ammunition",
        "description": [
            "You can use a weapon that has the ammunition property to make a ranged attack only if you have ammunition to fire from the weapon. Each time you attack with the weapon, you expend one piece of ammunition. Drawing the ammunition from a quiver, case, or other container is part of the attack (you need a free hand to load a one-handed weapon). At the end of the battle, you can recover half your expended ammunition by taking a minute to search the battlefield.",
            'If you use a weapon that has the ammunition property to make a melee attack, you treat the weapon as an improvised weapon (see "Improvised Weapons" later in the section). A sling must be loaded to deal any damage when used in this way.',
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:finesse",
        "simple_name": "finesse",
        "name": "Finesse",
        "description": [
            "When making an attack with a finesse weapon, you use your choice of your Strength or Dexterity modifier for the attack and damage rolls. You must use the same modifier for both rolls."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:heavy",
        "simple_name": "heavy",
        "name": "Heavy",
        "description": [
            "Small creatures have disadvantage on attack rolls with heavy weapons. A heavy weapon's size and bulk make it too large for a Small creature to use effectively."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:light",
        "simple_name": "light",
        "name": "Light",
        "description": [
            "A light weapon is small and easy to handle, making it ideal for use when fighting with two weapons."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:loading",
        "simple_name": "loading",
        "name": "Loading",
        "description": [
            "Because of the time required to load this weapon, you can fire only one piece of ammunition from it when you use an action, bonus action, or reaction to fire it, regardless of the number of attacks you can normally make."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:range",
        "simple_name": "range",
        "name": "Range",
        "description": [
            "A weapon that can be used to make a ranged attack has a range in parentheses after the ammunition or thrown property. The range lists two numbers. The first is the weapon's normal range in feet, and the second indicates the weapon's long range. When attacking a target beyond normal range, you have disadvantage on the attack roll. You can't attack a target beyond the weapon's long range."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:reach",
        "simple_name": "reach",
        "name": "Reach",
        "description": [
            "This weapon adds 5 feet to your reach when you attack with it, as well as when determining your reach for opportunity attacks with it."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:special",
        "simple_name": "special",
        "name": "Special",
        "description": [
            'A weapon with the special property has unusual rules governing its use, explained in the weapon\'s description (see "Special Weapons" later in this section).'
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:thrown",
        "simple_name": "thrown",
        "name": "Thrown",
        "description": [
            "If a weapon has the thrown property, you can throw the weapon to make a ranged attack. If the weapon is a melee weapon, you use the same ability modifier for that attack roll and damage roll that you would use for a melee attack with the weapon. For example, if you throw a handaxe, you use your Strength, but if you throw a dagger, you can use either your Strength or your Dexterity, since the dagger has the finesse property."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:two_handed",
        "simple_name": "two_handed",
        "name": "Two-Handed",
        "description": ["This weapon requires two hands when you attack with it."],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "weapon_property:versatile",
        "simple_name": "versatile",
        "name": "Versatile",
        "description": [
            "This weapon can be used with one or two hands. A damage value in parentheses appears with the property—the damage when the weapon is used with two hands to make a melee attack."
        ],
        "page": 147,
        "source": "SRD_CC_v5.1",
    },
]


def parse_weapon_properties() -> list[dict]:
    """Parse weapon properties dataset.

    Returns:
        List of 11 weapon property records

    Note:
        This returns static data - the weapon properties are game constants.
        Descriptions are from SRD Equipment chapter (page 147).
    """
    # Return a copy to prevent mutation
    return [dict(prop) for prop in WEAPON_PROPERTIES_DATA]
