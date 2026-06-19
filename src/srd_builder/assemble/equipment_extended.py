"""Extended equipment items - enhancements to the SRD dataset.

These items are referenced in equipment packs or monster stat blocks but
don't appear in the SRD equipment tables. They are added with estimated
costs/weights based on similar items to maintain referential integrity
and complete the dataset.

Each item carries a structured ``_provenance`` block (see
``ExtendedProvenance`` below) so downstream consumers can filter,
flag, or surface inferred items distinctly from PDF-extracted ones.
See ``docs/PROVENANCE.md`` § `equipment_extended.py` and
``docs/BACKLOG.md`` § "Provenance metadata in records" for the
design rationale.
"""

from typing import Any, Literal, NotRequired, TypedDict


class ExtendedProvenance(TypedDict):
    """Structured provenance block emitted on every extended item.

    Replaces the prior free-text ``_note`` field per BACKLOG proposal 2
    so consumers can programmatically distinguish inferred from
    PDF-extracted records.
    """

    source: Literal["inferred"]
    reason: Literal["pack_cross_reference", "monster_cross_reference"]
    referenced_by: str
    module: str
    estimates: list[Literal["cost", "weight"]]


class ExtendedItem(TypedDict):
    """Extended equipment item with estimated/inferred values."""

    id: str
    name: str
    simple_name: str
    category: str
    sub_category: str
    cost: dict[str, Any]
    page: int
    is_magic: bool
    _provenance: ExtendedProvenance
    weight_lb: NotRequired[float]
    description: NotRequired[str]
    weapon_type: NotRequired[str]
    damage: NotRequired[dict[str, str]]
    properties: NotRequired[list[str]]


_MODULE = "equipment_extended.py"


def _pack_provenance(pack_name: str) -> ExtendedProvenance:
    return {
        "source": "inferred",
        "reason": "pack_cross_reference",
        "referenced_by": pack_name,
        "module": _MODULE,
        "estimates": ["cost", "weight"],
    }


def _monster_provenance(referenced_by: str) -> ExtendedProvenance:
    return {
        "source": "inferred",
        "reason": "monster_cross_reference",
        "referenced_by": referenced_by,
        "module": _MODULE,
        "estimates": [],
    }


# Extended equipment items - not in SRD tables but logically needed
EXTENDED_EQUIPMENT: list[ExtendedItem] = [
    {
        "id": "item:string_10_feet",
        "name": "String (10 feet)",
        "simple_name": "string_10_feet",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 1, "currency": "sp"},
        "weight_lb": 0.0,
        "page": 70,
        "is_magic": False,
        "description": "A length of cord used for tying packages, marking paths, or other light-duty purposes. Not suitable for climbing.",
        "_provenance": _pack_provenance("Burglar's Pack"),
    },
    {
        "id": "item:alms_box",
        "name": "Alms box",
        "simple_name": "alms_box",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 5, "currency": "gp"},
        "weight_lb": 1.0,
        "page": 70,
        "is_magic": False,
        "description": "A small wooden or metal box used by clerics to collect charitable donations.",
        "_provenance": _pack_provenance("Priest's Pack"),
    },
    {
        "id": "item:incense_2_blocks",
        "name": "Incense (2 blocks)",
        "simple_name": "incense_2_blocks",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 1, "currency": "gp"},
        "weight_lb": 0.0,
        "page": 70,
        "is_magic": False,
        "description": "Compressed blocks of fragrant resin burned during religious ceremonies. Each block burns for approximately 1 hour.",
        "_provenance": _pack_provenance("Priest's Pack"),
    },
    {
        "id": "item:censer",
        "name": "Censer",
        "simple_name": "censer",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 5, "currency": "gp"},
        "weight_lb": 1.0,
        "page": 70,
        "is_magic": False,
        "description": "A container suspended on chains, used to burn incense during religious rituals. The smoke billows out through perforations.",
        "_provenance": _pack_provenance("Priest's Pack"),
    },
    {
        "id": "item:vestments",
        "name": "Vestments",
        "simple_name": "vestments",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 15, "currency": "gp"},
        "weight_lb": 4.0,
        "page": 70,
        "is_magic": False,
        "description": "Ceremonial robes worn by priests and clerics during religious services. Often decorated with symbols of the deity.",
        "_provenance": _pack_provenance("Priest's Pack"),
    },
    {
        "id": "item:book_of_lore",
        "name": "Book of lore",
        "simple_name": "book_of_lore",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 25, "currency": "gp"},
        "weight_lb": 3.0,
        "page": 70,
        "is_magic": False,
        "description": "A bound volume containing historical accounts, scholarly research, or collected knowledge on a particular subject. Useful for research and reference.",
        "_provenance": _pack_provenance("Scholar's Pack"),
    },
    {
        "id": "item:bag_of_sand_little",
        "name": "Bag of sand (little)",
        "simple_name": "bag_of_sand_little",
        "category": "gear",
        "sub_category": "adventuring_gear",
        "cost": {"amount": 1, "currency": "cp"},
        "weight_lb": 0.0,
        "page": 70,
        "is_magic": False,
        "description": "A small pouch of fine sand used to blot wet ink on parchment, preventing smudges and speeding drying.",
        "_provenance": _pack_provenance("Scholar's Pack"),
    },
    {
        "id": "item:knife_small",
        "name": "Knife (small)",
        "simple_name": "knife_small",
        "category": "weapon",
        "sub_category": "simple_melee",
        "weapon_type": "melee",
        "cost": {"amount": 2, "currency": "gp"},
        "weight_lb": 0.5,
        "damage": {"dice": "1d4", "type": "slashing"},
        "properties": ["finesse", "light"],
        "page": 70,
        "is_magic": False,
        "description": "A small utility knife suitable for cutting string, sharpening quills, and other everyday tasks. Can be used as a weapon in a pinch.",
        "_provenance": _pack_provenance("Scholar's Pack"),
    },
    {
        "id": "item:natural_armor",
        "name": "Natural armor",
        "simple_name": "natural_armor",
        "category": "armor",
        "sub_category": "natural",
        "cost": {"amount": 0, "currency": "gp"},
        "page": 63,
        "is_magic": False,
        "description": "Some creatures have natural armor from tough hide, scales, thick fur, or similar innate protection. Natural armor provides a base AC that may be modified by Dexterity, depending on the creature.",
        "_provenance": _monster_provenance("monster_stat_blocks"),
    },
]


def get_extended_equipment(source: str) -> list[dict[str, Any]]:
    """Get list of extended equipment items.

    Args:
        source: Base source_id; stamped on each item with an ``(extended)`` suffix.

    Returns:
        List of extended item dictionaries
    """
    extended_source = f"{source} (extended)"
    return [dict(item, source=extended_source) for item in EXTENDED_EQUIPMENT]
