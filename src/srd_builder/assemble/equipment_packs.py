"""Equipment Packs - Extracted from SRD 5.1 page 70.

Equipment packs are collections of adventuring gear sold as bundles.
This module provides structured data for pack contents, aggregates weight/cost,
and validates against existing equipment items.
"""

from typing import TypedDict


class PackContents(TypedDict):
    """Individual item within a pack with quantity."""

    item_id: str  # References item in equipment.json
    item_name: str  # Human-readable name
    quantity: int


class EquipmentPack(TypedDict):
    """Equipment pack with metadata and contents."""

    name: str
    cost_gp: int
    description: str  # SRD prose
    contents: list[PackContents]
    total_weight_lb: float  # Calculated from contents
    missing_items: list[str]  # Items not yet in equipment.json


# Equipment Packs from SRD 5.1 page 70
# Format: exact SRD text with structured parsing
EQUIPMENT_PACKS: list[EquipmentPack] = [
    {
        "name": "Burglar's Pack",
        "cost_gp": 16,
        "description": (
            "Includes a backpack, a bag of 1,000 ball bearings, 10 feet of string, "
            "a bell, 5 candles, a crowbar, a hammer, 10 pitons, a hooded lantern, "
            "2 flasks of oil, 5 days rations, a tinderbox, and a waterskin. "
            "The pack also has 50 feet of hempen rope strapped to the side of it."
        ),
        "contents": [
            {"item_id": "item:backpack", "item_name": "Backpack", "quantity": 1},
            {
                "item_id": "item:ball-bearings-bag-of-1000",
                "item_name": "Ball bearings (bag of 1,000)",
                "quantity": 1,
            },
            {"item_id": "item:string-10-feet", "item_name": "String (10 feet)", "quantity": 1},
            {"item_id": "item:bell", "item_name": "Bell", "quantity": 1},
            {"item_id": "item:candle", "item_name": "Candle", "quantity": 5},
            {"item_id": "item:crowbar", "item_name": "Crowbar", "quantity": 1},
            {"item_id": "item:hammer", "item_name": "Hammer", "quantity": 1},
            {"item_id": "item:piton", "item_name": "Piton", "quantity": 10},
            {
                "item_id": "item:lantern-hooded",
                "item_name": "Lantern, hooded",
                "quantity": 1,
            },
            {"item_id": "item:oil-flask", "item_name": "Oil (flask)", "quantity": 2},
            {
                "item_id": "item:rations-1-day",
                "item_name": "Rations (1 day)",
                "quantity": 5,
            },
            {"item_id": "item:tinderbox", "item_name": "Tinderbox", "quantity": 1},
            {"item_id": "item:waterskin", "item_name": "Waterskin", "quantity": 1},
            {
                "item_id": "item:rope-hempen-50-feet",
                "item_name": "Rope, hempen (50 feet)",
                "quantity": 1,
            },
        ],
        "total_weight_lb": 0.0,  # Will be calculated
        "missing_items": [],  # Not in SRD equipment tables
    },
    {
        "name": "Diplomat's Pack",
        "cost_gp": 39,
        "description": (
            "Includes a chest, 2 cases for maps and scrolls, a set of fine clothes, "
            "a bottle of ink, an ink pen, a lamp, 2 flasks of oil, 5 sheets of paper, "
            "a vial of perfume, sealing wax, and soap."
        ),
        "contents": [
            {"item_id": "item:chest", "item_name": "Chest", "quantity": 1},
            {
                "item_id": "item:case-map-or-scroll",
                "item_name": "Case, map or scroll",
                "quantity": 2,
            },
            {
                "item_id": "item:clothes-fine",
                "item_name": "Clothes, fine",
                "quantity": 1,
            },
            {
                "item_id": "item:ink-1-ounce-bottle",
                "item_name": "Ink (1 ounce bottle)",
                "quantity": 1,
            },
            {"item_id": "item:ink-pen", "item_name": "Ink pen", "quantity": 1},
            {"item_id": "item:lamp", "item_name": "Lamp", "quantity": 1},
            {"item_id": "item:oil-flask", "item_name": "Oil (flask)", "quantity": 2},
            {
                "item_id": "item:paper-one-sheet",
                "item_name": "Paper (one sheet)",
                "quantity": 5,
            },
            {
                "item_id": "item:perfume-vial",
                "item_name": "Perfume (vial)",
                "quantity": 1,
            },
            {
                "item_id": "item:sealing-wax",
                "item_name": "Sealing wax",
                "quantity": 1,
            },
            {"item_id": "item:soap", "item_name": "Soap", "quantity": 1},
        ],
        "total_weight_lb": 0.0,
        "missing_items": [],
    },
    {
        "name": "Dungeoneer's Pack",
        "cost_gp": 12,
        "description": (
            "Includes a backpack, a crowbar, a hammer, 10 pitons, 10 torches, "
            "a tinderbox, 10 days of rations, and a waterskin. "
            "The pack also has 50 feet of hempen rope strapped to the side of it."
        ),
        "contents": [
            {"item_id": "item:backpack", "item_name": "Backpack", "quantity": 1},
            {"item_id": "item:crowbar", "item_name": "Crowbar", "quantity": 1},
            {"item_id": "item:hammer", "item_name": "Hammer", "quantity": 1},
            {"item_id": "item:piton", "item_name": "Piton", "quantity": 10},
            {"item_id": "item:torch", "item_name": "Torch", "quantity": 10},
            {"item_id": "item:tinderbox", "item_name": "Tinderbox", "quantity": 1},
            {
                "item_id": "item:rations-1-day",
                "item_name": "Rations (1 day)",
                "quantity": 10,
            },
            {"item_id": "item:waterskin", "item_name": "Waterskin", "quantity": 1},
            {
                "item_id": "item:rope-hempen-50-feet",
                "item_name": "Rope, hempen (50 feet)",
                "quantity": 1,
            },
        ],
        "total_weight_lb": 0.0,
        "missing_items": [],
    },
    {
        "name": "Entertainer's Pack",
        "cost_gp": 40,
        "description": (
            "Includes a backpack, a bedroll, 2 costumes, 5 candles, "
            "5 days of rations, a waterskin, and a disguise kit."
        ),
        "contents": [
            {"item_id": "item:backpack", "item_name": "Backpack", "quantity": 1},
            {"item_id": "item:bedroll", "item_name": "Bedroll", "quantity": 1},
            {
                "item_id": "item:clothes-costume",
                "item_name": "Clothes, costume",
                "quantity": 2,
            },
            {"item_id": "item:candle", "item_name": "Candle", "quantity": 5},
            {
                "item_id": "item:rations-1-day",
                "item_name": "Rations (1 day)",
                "quantity": 5,
            },
            {"item_id": "item:waterskin", "item_name": "Waterskin", "quantity": 1},
            {
                "item_id": "item:disguise-kit",
                "item_name": "Disguise kit",
                "quantity": 1,
            },
        ],
        "total_weight_lb": 0.0,
        "missing_items": [],
    },
    {
        "name": "Explorer's Pack",
        "cost_gp": 10,
        "description": (
            "Includes a backpack, a bedroll, a mess kit, a tinderbox, 10 torches, "
            "10 days of rations, and a waterskin. "
            "The pack also has 50 feet of hempen rope strapped to the side of it."
        ),
        "contents": [
            {"item_id": "item:backpack", "item_name": "Backpack", "quantity": 1},
            {"item_id": "item:bedroll", "item_name": "Bedroll", "quantity": 1},
            {"item_id": "item:mess-kit", "item_name": "Mess kit", "quantity": 1},
            {"item_id": "item:tinderbox", "item_name": "Tinderbox", "quantity": 1},
            {"item_id": "item:torch", "item_name": "Torch", "quantity": 10},
            {
                "item_id": "item:rations-1-day",
                "item_name": "Rations (1 day)",
                "quantity": 10,
            },
            {"item_id": "item:waterskin", "item_name": "Waterskin", "quantity": 1},
            {
                "item_id": "item:rope-hempen-50-feet",
                "item_name": "Rope, hempen (50 feet)",
                "quantity": 1,
            },
        ],
        "total_weight_lb": 0.0,
        "missing_items": [],
    },
    {
        "name": "Priest's Pack",
        "cost_gp": 19,
        "description": (
            "Includes a backpack, a blanket, 10 candles, a tinderbox, an alms box, "
            "2 blocks of incense, a censer, vestments, 2 days of rations, and a waterskin."
        ),
        "contents": [
            {"item_id": "item:backpack", "item_name": "Backpack", "quantity": 1},
            {"item_id": "item:blanket", "item_name": "Blanket", "quantity": 1},
            {"item_id": "item:candle", "item_name": "Candle", "quantity": 10},
            {"item_id": "item:tinderbox", "item_name": "Tinderbox", "quantity": 1},
            {"item_id": "item:alms-box", "item_name": "Alms box", "quantity": 1},
            {
                "item_id": "item:incense-2-blocks",
                "item_name": "Incense (2 blocks)",
                "quantity": 1,
            },
            {"item_id": "item:censer", "item_name": "Censer", "quantity": 1},
            {"item_id": "item:vestments", "item_name": "Vestments", "quantity": 1},
            {
                "item_id": "item:rations-1-day",
                "item_name": "Rations (1 day)",
                "quantity": 2,
            },
            {"item_id": "item:waterskin", "item_name": "Waterskin", "quantity": 1},
        ],
        "total_weight_lb": 0.0,
        "missing_items": [],  # Religious items not in SRD tables
    },
    {
        "name": "Scholar's Pack",
        "cost_gp": 40,
        "description": (
            "Includes a backpack, a book of lore, a bottle of ink, an ink pen, "
            "10 sheets of parchment, a little bag of sand, and a small knife."
        ),
        "contents": [
            {"item_id": "item:backpack", "item_name": "Backpack", "quantity": 1},
            {"item_id": "item:book-of-lore", "item_name": "Book of lore", "quantity": 1},
            {
                "item_id": "item:ink-1-ounce-bottle",
                "item_name": "Ink (1 ounce bottle)",
                "quantity": 1,
            },
            {"item_id": "item:ink-pen", "item_name": "Ink pen", "quantity": 1},
            {
                "item_id": "item:parchment-one-sheet",
                "item_name": "Parchment (one sheet)",
                "quantity": 10,
            },
            {
                "item_id": "item:bag-of-sand-little",
                "item_name": "Bag of sand (little)",
                "quantity": 1,
            },
            {"item_id": "item:knife-small", "item_name": "Knife (small)", "quantity": 1},
        ],
        "total_weight_lb": 0.0,
        "missing_items": [],  # Scholarly items not in SRD tables
    },
]


def calculate_pack_weight(pack: EquipmentPack, equipment_lookup: dict[str, dict]) -> float:
    """Calculate total weight of pack from individual item weights.

    Args:
        pack: Equipment pack data
        equipment_lookup: Dict mapping item_id to equipment item data

    Returns:
        Total weight in pounds
    """
    total = 0.0
    for content in pack["contents"]:
        item = equipment_lookup.get(content["item_id"])
        if item and item.get("weight_lb"):
            total += item["weight_lb"] * content["quantity"]
    return round(total, 1)


def validate_pack_contents(pack: EquipmentPack, equipment_lookup: dict[str, dict]) -> dict:
    """Validate that all pack contents exist in equipment.json.

    Args:
        pack: Equipment pack data
        equipment_lookup: Dict mapping item_id to equipment item data

    Returns:
        Dict with validation results: found_count, missing_count, missing_items
    """
    found = []
    missing = []

    for content in pack["contents"]:
        if content["item_id"] in equipment_lookup:
            found.append(content["item_name"])
        else:
            missing.append(content["item_name"])

    # Add pre-identified missing items
    missing.extend(pack.get("missing_items", []))

    return {
        "found_count": len(found),
        "missing_count": len(missing),
        "missing_items": missing,
    }
