"""Extended equipment items - enhancements to the SRD dataset.

These items are referenced in equipment packs or other SRD content but don't
appear in the SRD equipment tables. They are added with estimated costs/weights
based on similar items to maintain referential integrity and complete the dataset.

This module is maintained separately from core SRD extraction to clearly identify
items that have been inferred or enhanced beyond the source material.
"""

from typing import Any, NotRequired, TypedDict


class ExtendedItem(TypedDict):
    """Extended equipment item with estimated/inferred values."""

    id: str
    name: str
    simple_name: str
    category: str
    sub_category: str
    cost: dict[str, Any]
    page: int
    source: str
    is_magic: bool
    _note: str
    weight_lb: NotRequired[float]  # Optional field
    description: NotRequired[str]  # Optional field
    weapon_type: NotRequired[str]  # Optional for weapons
    damage: NotRequired[dict[str, str]]  # Optional for weapons
    properties: NotRequired[list[str]]  # Optional for weapons


# Extended equipment items - not in SRD tables but logically needed
EXTENDED_EQUIPMENT: list[ExtendedItem] = [
    {
        "id": "item:string-10-feet",
        "name": "String (10 feet)",
        "simple_name": "string-10-feet",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 1, "currency": "sp"},  # Estimated: cheaper than rope
        "weight_lb": 0.0,  # Negligible
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "A length of cord used for tying packages, marking paths, or other light-duty purposes. Not suitable for climbing.",
        "_note": "Extended item - referenced in Burglar's Pack but not in SRD tables. Cost/weight estimated. Cost/weight estimated.",
    },
    {
        "id": "item:alms-box",
        "name": "Alms box",
        "simple_name": "alms-box",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 5, "currency": "gp"},  # Estimated: religious item
        "weight_lb": 1.0,
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "A small wooden or metal box used by clerics to collect charitable donations.",
        "_note": "Extended item - referenced in Priest's Pack but not in SRD tables. Cost/weight estimated.",
    },
    {
        "id": "item:incense-2-blocks",
        "name": "Incense (2 blocks)",
        "simple_name": "incense-2-blocks",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 1, "currency": "gp"},  # Estimated: consumable
        "weight_lb": 0.0,  # Negligible
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "Compressed blocks of fragrant resin burned during religious ceremonies. Each block burns for approximately 1 hour.",
        "_note": "Extended item - referenced in Priest's Pack but not in SRD tables. Cost/weight estimated.",
    },
    {
        "id": "item:censer",
        "name": "Censer",
        "simple_name": "censer",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 5, "currency": "gp"},  # Estimated: religious item
        "weight_lb": 1.0,
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "A container suspended on chains, used to burn incense during religious rituals. The smoke billows out through perforations.",
        "_note": "Extended item - referenced in Priest's Pack but not in SRD tables. Cost/weight estimated.",
    },
    {
        "id": "item:vestments",
        "name": "Vestments",
        "simple_name": "vestments",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 15, "currency": "gp"},  # Estimated: similar to fine clothes
        "weight_lb": 4.0,
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "Ceremonial robes worn by priests and clerics during religious services. Often decorated with symbols of the deity.",
        "_note": "Extended item - referenced in Priest's Pack but not in SRD tables. Cost/weight estimated.",
    },
    {
        "id": "item:book-of-lore",
        "name": "Book of lore",
        "simple_name": "book-of-lore",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 25, "currency": "gp"},  # Estimated: valuable book
        "weight_lb": 3.0,
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "A bound volume containing historical accounts, scholarly research, or collected knowledge on a particular subject. Useful for research and reference.",
        "_note": "Extended item - referenced in Scholar's Pack but not in SRD tables. Cost/weight estimated.",
    },
    {
        "id": "item:bag-of-sand-little",
        "name": "Bag of sand (little)",
        "simple_name": "bag-of-sand-little",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 1, "currency": "cp"},  # Estimated: very cheap
        "weight_lb": 0.0,  # Negligible
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "A small pouch of fine sand used to blot wet ink on parchment, preventing smudges and speeding drying.",
        "_note": "Extended item - referenced in Scholar's Pack but not in SRD tables. Cost/weight estimated.",
    },
    {
        "id": "item:knife-small",
        "name": "Knife (small)",
        "simple_name": "knife-small",
        "category": "weapon",
        "sub_category": "simple_melee",
        "weapon_type": "melee",
        "cost": {"amount": 2, "currency": "gp"},  # Estimated: similar to dagger
        "weight_lb": 0.5,
        "damage": {"dice": "1d4", "type": "slashing"},
        "properties": ["finesse", "light"],
        "page": 70,
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "A small utility knife suitable for cutting string, sharpening quills, and other everyday tasks. Can be used as a weapon in a pinch.",
        "_note": "Extended item - referenced in Scholar's Pack but not in SRD tables. Cost/weight estimated.",
    },
    {
        "id": "item:natural-armor",
        "name": "Natural armor",
        "simple_name": "natural_armor",
        "category": "armor",
        "sub_category": "natural",
        "cost": {"amount": 0, "currency": "gp"},  # Not purchasable
        "page": 63,  # Armor section
        "source": "SRD 5.1 (extended)",
        "is_magic": False,
        "description": "Some creatures have natural armor from tough hide, scales, thick fur, or similar innate protection. Natural armor provides a base AC that may be modified by Dexterity, depending on the creature.",
        "_note": "Extended item - referenced in monster stat blocks but not in SRD armor tables. Included for cross-reference completeness.",
    },
]


def get_extended_equipment() -> list[dict[str, Any]]:
    """Get list of extended equipment items.

    Returns:
        List of extended item dictionaries
    """
    return [dict(item) for item in EXTENDED_EQUIPMENT]
