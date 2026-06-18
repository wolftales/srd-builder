"""Tests for the equipment-packs PDF extractor.

Replaces the legacy ``tests/test_equipment_packs.py`` which exercised the
retired hand-curated ``EQUIPMENT_PACKS`` literal in
``src/srd_builder/assemble/equipment_packs.py``.

The new tests pin three things:
  - The page-70 extractor returns 7 packs in the SRD's natural order.
  - Each pack's name, cost, item count, contents IDs, and quantities
    match the snapshot of the retired literal (byte-perfect parity).
  - The integration test still passes against ``dist/srd_5_1/equipment.json``
    when a build is available.

For the per-page reproducer that proved the prose was extractable in
the first place, see ``tests/test_pdf_provenance.py``
(``test_equipment_packs_pdf_page_70_*``).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from srd_builder.extract.datasets.extract_equipment_packs import (
    extract_equipment_packs,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"


def _require_pdf() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")


# Snapshot of the retired EQUIPMENT_PACKS literal — minimum invariants the
# extractor must reproduce. Listed as (name, cost_gp, item_count) so adding
# or dropping a pack item by accident fails this test loudly.
_EXPECTED_PACK_SUMMARIES: list[tuple[str, int, int]] = [
    ("Burglar's Pack", 16, 14),
    ("Diplomat's Pack", 39, 11),
    ("Dungeoneer's Pack", 12, 9),
    ("Entertainer's Pack", 40, 7),
    ("Explorer's Pack", 10, 8),
    ("Priest's Pack", 19, 10),
    ("Scholar's Pack", 40, 7),
]


# Per-pack contents pinned as ordered ``(item_id, quantity)`` lists. These
# are the byte-perfect snapshot of the retired EQUIPMENT_PACKS literal —
# any drift here is a real semantic regression.
_EXPECTED_PACK_CONTENTS: dict[str, list[tuple[str, int]]] = {
    "Burglar's Pack": [
        ("item:backpack", 1),
        ("item:ball_bearings_bag_of_1000", 1),
        ("item:string_10_feet", 1),
        ("item:bell", 1),
        ("item:candle", 5),
        ("item:crowbar", 1),
        ("item:hammer", 1),
        ("item:piton", 10),
        ("item:lantern_hooded", 1),
        ("item:oil_flask", 2),
        ("item:rations_1_day", 5),
        ("item:tinderbox", 1),
        ("item:waterskin", 1),
        ("item:rope_hempen_50_feet", 1),
    ],
    "Diplomat's Pack": [
        ("item:chest", 1),
        ("item:case_map_or_scroll", 2),
        ("item:clothes_fine", 1),
        ("item:ink_1_ounce_bottle", 1),
        ("item:ink_pen", 1),
        ("item:lamp", 1),
        ("item:oil_flask", 2),
        ("item:paper_one_sheet", 5),
        ("item:perfume_vial", 1),
        ("item:sealing_wax", 1),
        ("item:soap", 1),
    ],
    "Dungeoneer's Pack": [
        ("item:backpack", 1),
        ("item:crowbar", 1),
        ("item:hammer", 1),
        ("item:piton", 10),
        ("item:torch", 10),
        ("item:tinderbox", 1),
        ("item:rations_1_day", 10),
        ("item:waterskin", 1),
        ("item:rope_hempen_50_feet", 1),
    ],
    "Entertainer's Pack": [
        ("item:backpack", 1),
        ("item:bedroll", 1),
        ("item:clothes_costume", 2),
        ("item:candle", 5),
        ("item:rations_1_day", 5),
        ("item:waterskin", 1),
        ("item:disguise_kit", 1),
    ],
    "Explorer's Pack": [
        ("item:backpack", 1),
        ("item:bedroll", 1),
        ("item:mess_kit", 1),
        ("item:tinderbox", 1),
        ("item:torch", 10),
        ("item:rations_1_day", 10),
        ("item:waterskin", 1),
        ("item:rope_hempen_50_feet", 1),
    ],
    "Priest's Pack": [
        ("item:backpack", 1),
        ("item:blanket", 1),
        ("item:candle", 10),
        ("item:tinderbox", 1),
        ("item:alms_box", 1),
        ("item:incense_2_blocks", 1),
        ("item:censer", 1),
        ("item:vestments", 1),
        ("item:rations_1_day", 2),
        ("item:waterskin", 1),
    ],
    "Scholar's Pack": [
        ("item:backpack", 1),
        ("item:book_of_lore", 1),
        ("item:ink_1_ounce_bottle", 1),
        ("item:ink_pen", 1),
        ("item:parchment_one_sheet", 10),
        ("item:bag_of_sand_little", 1),
        ("item:knife_small", 1),
    ],
}


def test_extract_equipment_packs_returns_seven_packs_in_order() -> None:
    _require_pdf()
    result = extract_equipment_packs(SRD_5_1_PDF)
    packs = result["packs"]

    assert len(packs) == 7, f"Expected 7 packs, got {len(packs)}"

    actual = [(p["name"], p["cost_gp"], len(p["contents"])) for p in packs]
    assert actual == _EXPECTED_PACK_SUMMARIES, (
        "Pack summaries (name, cost, item_count) drifted from snapshot of "
        "retired EQUIPMENT_PACKS literal."
    )


def test_extract_equipment_packs_meta_block() -> None:
    _require_pdf()
    result = extract_equipment_packs(SRD_5_1_PDF)
    meta = result["_meta"]
    assert meta["packs_extracted"] == 7
    assert meta["pages_processed"] == [70]
    assert "extractor_version" in meta


@pytest.mark.parametrize(
    ("pack_name", "expected_contents"),
    list(_EXPECTED_PACK_CONTENTS.items()),
)
def test_extract_equipment_packs_contents_byte_perfect(
    pack_name: str,
    expected_contents: list[tuple[str, int]],
) -> None:
    """Each pack's ``[(item_id, quantity), …]`` list must match the snapshot.

    This is the byte-perfect parity gate: when v0.27.5 retires the
    hand-curated ``EQUIPMENT_PACKS`` literal, the new PDF extractor must
    yield exactly the same content lists, in the same order, with the
    same item IDs and quantities.
    """
    _require_pdf()
    result = extract_equipment_packs(SRD_5_1_PDF)
    packs_by_name = {p["name"]: p for p in result["packs"]}
    assert pack_name in packs_by_name, f"Pack {pack_name!r} missing from extractor output"
    pack = packs_by_name[pack_name]
    actual = [(c["item_id"], c["quantity"]) for c in pack["contents"]]
    assert actual == expected_contents, (
        f"{pack_name} contents drifted from snapshot.\n"
        f"  expected: {expected_contents}\n"
        f"  got:      {actual}"
    )


def test_extract_equipment_packs_descriptions_start_with_includes() -> None:
    """Every pack's description begins with the SRD's ``Includes …`` lead-in."""
    _require_pdf()
    result = extract_equipment_packs(SRD_5_1_PDF)
    for pack in result["packs"]:
        assert pack["description"].startswith("Includes "), (
            f"{pack['name']} description does not start with 'Includes ': "
            f"{pack['description'][:60]!r}"
        )
        assert pack["description"].endswith("."), (
            f"{pack['name']} description does not end with '.': {pack['description'][-60:]!r}"
        )


@pytest.mark.skipif(
    not (Path("dist/srd_5_1/equipment.json").exists()),
    reason="equipment.json not built yet",
)
def test_built_equipment_packs_have_resolvable_contents() -> None:
    """Integration check: every pack item in the built dataset resolves to
    a known equipment item.

    Replaces the ``test_all_real_packs_have_valid_contents`` integration
    test from the retired ``tests/test_equipment_packs.py``.
    """
    equipment = json.loads(Path("dist/srd_5_1/equipment.json").read_text())
    items_by_id = {item["id"]: item for item in equipment["items"]}

    pack_records = [
        item for item in equipment["items"] if item.get("sub_category") == "equipment_pack"
    ]
    assert len(pack_records) == 7, (
        f"Expected 7 pack records in equipment.json, got {len(pack_records)}"
    )

    for pack in pack_records:
        for content in pack["pack_contents"]:
            assert content["item_id"] in items_by_id, (
                f"{pack['name']}: pack content {content['item_id']!r} "
                f"({content['item_name']!r}) does not resolve to a known item."
            )
