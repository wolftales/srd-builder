"""Tests for the equipment-descriptions PDF extractor.

Replaces the retired hand-curated literals
(``ADVENTURE_GEAR_DESCRIPTIONS``, ``TOOLS_DESCRIPTIONS``,
``ARMOR_DESCRIPTIONS``, ``LIFESTYLE_DESCRIPTIONS``) that lived in
``src/srd_builder/assemble/equipment_descriptions.py`` (~398 lines).

The new tests pin three things:
  - The page-63/66-68/70-71/73 extractor returns 69 descriptions in
    PDF reading order.
  - Each description's ``item_id``, source page, prefix, and suffix
    match a snapshot taken from the live PDF.
  - The four-section breakdown (armor, adventure_gear, tools,
    lifestyle) accounts for all 69 records.

For the per-section reproducer that proved the prose was extractable
in the first place, see ``tests/test_pdf_provenance.py``
(``test_equipment_descriptions_section_anchor_extractable`` and
``test_equipment_descriptions_item_signature_extractable``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srd_builder.extract.datasets.extract_equipment_descriptions import (
    extract_equipment_descriptions,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"


def _require_pdf() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")


# Per-item snapshot: (item_id, page, prefix[:35], suffix[-30:]).
#
# Two of the page numbers diverge from the retired curated module.
# Those are NOT bugs — they are corrections of curated drift, caught
# by the v0.27.6 reproducer in tests/test_pdf_provenance.py:
#   - item:antitoxin-vial: curated p.67 -> PDF p.66
#   - item:arcane-focus:   curated p.67 -> PDF p.66
#
# The descriptions for ``item:book``, ``item:gaming-set``,
# ``item:holy-symbol``, ``item:musical-instrument``, ``item:pouch``,
# and ``item:artisans-tools`` also include text that the curated
# module had editorially stripped (e.g. parenthetical
# cross-references, "as shown on the table"). The PDF is canonical.
_EXPECTED_DESCRIPTIONS: list[tuple[str, int, str, str]] = [
    ("item:padded", 63, "Padded armor consists of quilted la", "d layers of cloth and batting."),
    ("item:leather", 63, "The breastplate and shoulder protec", "r and more flexible materials."),
    (
        "item:studded-leather",
        63,
        "Made from tough but flexible leathe",
        "th close-set rivets or spikes.",
    ),
    ("item:hide", 63, "This crude armor consists of thick ", "needed to create better armor."),
    (
        "item:chain-shirt",
        63,
        "Made of interlocking metal rings, a",
        "to be muffled by outer layers.",
    ),
    (
        "item:scale-mail",
        63,
        "This armor consists of a coat and l",
        ". The suit includes gauntlets.",
    ),
    (
        "item:breastplate",
        63,
        "This armor consists of a fitted met",
        "earer relatively unencumbered.",
    ),
    (
        "item:half-plate",
        63,
        "Half plate consists of shaped metal",
        " attached with leather straps.",
    ),
    ("item:ring-mail", 63, "This armor is leather armor with he", "who can't afford better armor."),
    (
        "item:chain-mail",
        63,
        "Made of interlocking metal rings, c",
        ". The suit includes gauntlets.",
    ),
    ("item:splint", 63, "This armor is made of narrow vertic", "hain mail protects the joints."),
    ("item:plate", 63, "Plate consists of shaped, interlock", "bute the weight over the body."),
    ("item:acid-vial", 66, "As an action, you can splash the co", " target takes 2d6 acid damage."),
    (
        "item:alchemists-fire-flask",
        66,
        "This sticky, adhesive fluid ignites",
        "heck to extinguish the flames.",
    ),
    (
        "item:antitoxin-vial",
        66,
        "A creature that drinks this vial of",
        "nefit to undead or constructs.",
    ),
    (
        "item:arcane-focus",
        66,
        "An arcane focus is a special item—a",
        " item as a spellcasting focus.",
    ),
    (
        "item:ball-bearings-bag-of-1000",
        67,
        "As an action, you can spill these t",
        "doesn't need to make the save.",
    ),
    (
        "item:block-and-tackle",
        67,
        "A set of pulleys with a cable threa",
        " weight you can normally lift.",
    ),
    ("item:book", 67, "A book might contain poetry, histor", "cribed later in this section)."),
    (
        "item:caltrops-bag-of-20",
        67,
        "As an action, you can spread a bag ",
        "doesn't need to make the save.",
    ),
    ("item:candle", 67, "For 1 hour, a candle sheds bright l", "ight for an additional 5 feet."),
    (
        "item:case-crossbow-bolt",
        67,
        "This wooden case can hold up to twe",
        "d up to twenty crossbow bolts.",
    ),
    (
        "item:case-map-or-scroll",
        67,
        "This cylindrical leather case can h",
        "rolled-up sheets of parchment.",
    ),
    (
        "item:chain-10-feet",
        67,
        "A chain has 10 hit points. It can b",
        "ccessful DC 20 Strength check.",
    ),
    (
        "item:climbers-kit",
        67,
        "A climber's kit includes special pi",
        "nt without undoing the anchor.",
    ),
    (
        "item:component-pouch",
        67,
        "A component pouch is a small, water",
        "ted in a spell's description).",
    ),
    ("item:crowbar", 67, "Using a crowbar grants advantage to", "bar's leverage can be applied."),
    (
        "item:druidic-focus",
        67,
        "A druidic focus might be a sprig of",
        "bject as a spellcasting focus.",
    ),
    (
        "item:fishing-tackle",
        67,
        "This kit includes a wooden rod, sil",
        "vet lures, and narrow netting.",
    ),
    (
        "item:healers-kit",
        67,
        "This kit is a leather pouch contain",
        "ake a Wisdom (Medicine) check.",
    ),
    (
        "item:holy-symbol",
        67,
        "A holy symbol is a representation o",
        "sibly, or bear it on a shield.",
    ),
    (
        "item:holy-water-flask",
        67,
        "As an action, you can splash the co",
        "expend a 1st-level spell slot.",
    ),
    (
        "item:hunting-trap",
        67,
        "When you use your action to set it,",
        "amage to the trapped creature.",
    ),
    ("item:lamp", 68, "A lamp casts bright light in a 15-f", "rs on a flask (1 pint) of oil."),
    (
        "item:lantern-bullseye",
        68,
        "A bullseye lantern casts bright lig",
        "rs on a flask (1 pint) of oil.",
    ),
    (
        "item:lantern-hooded",
        68,
        "A hooded lantern casts bright light",
        " dim light in a 5-foot radius.",
    ),
    ("item:lock", 68, "A key is provided with the lock. Wi", "e available for higher prices."),
    (
        "item:magnifying-glass",
        68,
        "This lens allows a closer look at s",
        "t is small or highly detailed.",
    ),
    ("item:manacles", 68, "These metal restraints can bind a S", ". Manacles have 15 hit points."),
    ("item:mess-kit", 68, "This tin box contains a cup and sim", "er as a plate or shallow bowl."),
    ("item:oil-flask", 68, "Oil usually comes in a clay flask t", "his damage only once per turn."),
    (
        "item:poison-basic-vial",
        68,
        "You can use the poison in this vial",
        "cy for 1 minute before drying.",
    ),
    (
        "item:potion-of-healing",
        68,
        "A character who drinks the magical ",
        "ring a potion takes an action.",
    ),
    ("item:pouch", 68, "A cloth or leather pouch can hold u", "ibed earlier in this section)."),
    ("item:quiver", 68, "A quiver can hold up to 20 arrows.", "iver can hold up to 20 arrows."),
    (
        "item:ram-portable",
        68,
        "You can use a portable ram to break",
        "g you advantage on this check.",
    ),
    (
        "item:rations-1-day",
        68,
        "Rations consist of dry foods suitab",
        "ied fruit, hardtack, and nuts.",
    ),
    (
        "item:rope-hempen-50-feet",
        68,
        "Rope, whether made of hemp or silk,",
        "t with a DC 17 Strength check.",
    ),
    (
        "item:scale-merchants",
        68,
        "A scale includes a small balance, p",
        "to help determine their worth.",
    ),
    ("item:spellbook", 68, "Essential for wizards, a spellbook ", "suitable for recording spells."),
    ("item:spyglass", 68, "Objects viewed through a spyglass a", "magnified to twice their size."),
    ("item:tent", 68, "A simple and portable canvas shelte", "as shelter, a tent sleeps two."),
    ("item:tinderbox", 68, "This small container holds flint, f", "any other fire takes 1 minute."),
    ("item:torch", 68, "A torch burns for 1 hour, providing", "d hit, it deals 1 fire damage."),
    (
        "item:artisans-tools",
        70,
        "These special tools include the ite",
        "quires a separate proficiency.",
    ),
    (
        "item:disguise-kit",
        71,
        "This pouch of cosmetics, hair dye, ",
        "e to create a visual disguise.",
    ),
    (
        "item:forgery-kit",
        71,
        "This small box contains a variety o",
        "hysical forgery of a document.",
    ),
    (
        "item:gaming-set",
        71,
        "This item encompasses a wide range ",
        "quires a separate proficiency.",
    ),
    (
        "item:herbalism-kit",
        71,
        "This kit contains a variety of inst",
        "itoxin and potions of healing.",
    ),
    (
        "item:musical-instrument",
        71,
        "Several of the most common types of",
        "quires a separate proficiency.",
    ),
    (
        "item:navigators-tools",
        71,
        "This set of instruments is used for",
        " to avoid getting lost at sea.",
    ),
    (
        "item:poisoners-kit",
        71,
        "A poisoner's kit includes the vials",
        " make to craft or use poisons.",
    ),
    (
        "item:thieves-tools",
        71,
        "This set of tools includes a small ",
        "to disarm traps or open locks.",
    ),
    ("item:squalid", 73, "You live in a leaky stable, a mud-f", "xiles, or suffer from disease."),
    ("item:poor", 73, "A poor lifestyle means going withou", " and other disreputable types."),
    ("item:modest", 73, "A modest lifestyle keeps you out of", ", hedge wizards, and the like."),
    (
        "item:comfortable",
        73,
        "Choosing a comfortable lifestyle me",
        "people, and military officers.",
    ),
    ("item:wealthy", 73, "Choosing a wealthy lifestyle means ", "ave a small staff of servants."),
    (
        "item:aristocratic",
        73,
        "You live a life of plenty and comfo",
        "igue as a pawn or participant.",
    ),
]


def test_extract_equipment_descriptions_returns_69_in_pdf_order() -> None:
    _require_pdf()
    result = extract_equipment_descriptions(SRD_5_1_PDF)
    descs = result["descriptions"]

    assert len(descs) == 69, f"Expected 69 descriptions, got {len(descs)}"

    actual_ids = [d["item_id"] for d in descs]
    expected_ids = [t[0] for t in _EXPECTED_DESCRIPTIONS]
    assert actual_ids == expected_ids, (
        "Description order drifted from PDF reading order. "
        f"First mismatch at index {next(i for i, (a, e) in enumerate(zip(actual_ids, expected_ids, strict=False)) if a != e)}"
    )


def test_extract_equipment_descriptions_meta_block() -> None:
    _require_pdf()
    result = extract_equipment_descriptions(SRD_5_1_PDF)
    meta = result["_meta"]
    assert meta["descriptions_extracted"] == 69
    assert meta["pages_processed"] == [63, 66, 67, 68, 70, 71, 73]
    assert meta["sections"] == ["armor", "adventure_gear", "tools", "lifestyle"]
    assert "extractor_version" in meta


@pytest.mark.parametrize(
    ("item_id", "expected_page", "expected_prefix", "expected_suffix"),
    _EXPECTED_DESCRIPTIONS,
    ids=[t[0] for t in _EXPECTED_DESCRIPTIONS],
)
def test_extract_equipment_descriptions_per_item_signature(
    item_id: str,
    expected_page: int,
    expected_prefix: str,
    expected_suffix: str,
) -> None:
    """Each description's source page, opening, and closing must match
    a snapshot taken from the live PDF.
    """
    _require_pdf()
    result = extract_equipment_descriptions(SRD_5_1_PDF)
    by_id = {d["item_id"]: d for d in result["descriptions"]}
    assert item_id in by_id, f"{item_id!r} missing from extractor output"
    record = by_id[item_id]
    assert record["page"] == expected_page, (
        f"{item_id}: page drifted (expected {expected_page}, got {record['page']})"
    )
    desc = record["description"]
    assert desc.startswith(expected_prefix), (
        f"{item_id}: description prefix drifted.\n"
        f"  expected: {expected_prefix!r}\n"
        f"  got:      {desc[:35]!r}"
    )
    assert desc.endswith(expected_suffix), (
        f"{item_id}: description suffix drifted.\n"
        f"  expected: {expected_suffix!r}\n"
        f"  got:      {desc[-30:]!r}"
    )


def test_extract_equipment_descriptions_section_breakdown() -> None:
    """All 69 records account for the four-section split (12+42+9+6)."""
    _require_pdf()
    result = extract_equipment_descriptions(SRD_5_1_PDF)
    descs = result["descriptions"]
    by_page = {d["item_id"]: d["page"] for d in descs}
    armor_count = sum(1 for p in by_page.values() if p == 63)
    adventure_count = sum(1 for p in by_page.values() if p in (66, 67, 68))
    tools_count = sum(1 for p in by_page.values() if p in (70, 71))
    lifestyle_count = sum(1 for p in by_page.values() if p == 73)
    assert armor_count == 12
    assert adventure_count == 42
    assert tools_count == 9
    assert lifestyle_count == 6


def test_extract_equipment_descriptions_descriptions_end_with_period() -> None:
    """Every description ends with a period — guards against
    truncation at a page boundary or section terminator."""
    _require_pdf()
    result = extract_equipment_descriptions(SRD_5_1_PDF)
    for d in result["descriptions"]:
        assert d["description"].endswith("."), (
            f"{d['item_id']}: description does not end with '.': {d['description'][-60:]!r}"
        )
