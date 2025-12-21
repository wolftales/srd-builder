"""Test cross-page monster extraction.

This test suite prevents regression of the cross-page monster bug fixed in commit 7abeb74.
Before the fix, monsters spanning page boundaries were truncated (e.g., Deva had only 28 blocks).
After the fix, all monsters have complete stat blocks regardless of page breaks.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def monsters_raw():
    """Load extracted monsters from raw JSON."""
    raw_path = Path("rulesets/srd_5_1/raw/monsters_raw.json")
    if not raw_path.exists():
        pytest.skip("monsters_raw.json not found - run extraction first")

    with open(raw_path, encoding="utf-8") as f:
        data = json.load(f)

    return {m["name"]: m for m in data["monsters"]}


def test_deva_spans_multiple_pages(monsters_raw):
    """Deva should span pages 261-262 with complete stat block.

    Regression test for commit 7abeb74.
    Before fix: 28 blocks, page 261 only
    After fix: 70+ blocks, pages 261-262
    """
    deva = monsters_raw.get("Deva")
    assert deva is not None, "Deva not found in extraction"

    # Must span multiple pages
    assert len(deva["pages"]) >= 2, f"Deva should span 2+ pages, got {deva['pages']}"
    assert 261 in deva["pages"], "Deva should include page 261"
    assert 262 in deva["pages"], "Deva should include page 262"

    # Must have complete stat block (70+ blocks)
    block_count = len(deva["blocks"])
    assert (
        block_count >= 70
    ), f"Deva should have 70+ blocks for complete stat block, got {block_count}"

    # Verify no warnings
    assert (
        len(deva["warnings"]) == 0
    ), f"Deva extraction should have no warnings, got {deva['warnings']}"


def test_solar_complete_extraction(monsters_raw):
    """Solar should have complete stat block across pages.

    Solar was one of the monsters affected by the cross-page bug.
    Before fix: Only 17 blocks
    After fix: Complete stat block with 70+ blocks
    """
    solar = monsters_raw.get("Solar")
    assert solar is not None, "Solar not found in extraction"

    # Must have substantial block count (complex monster)
    block_count = len(solar["blocks"])
    assert (
        block_count >= 70
    ), f"Solar should have 70+ blocks for complete stat block, got {block_count}"

    # Verify no warnings
    assert (
        len(solar["warnings"]) == 0
    ), f"Solar extraction should have no warnings, got {solar['warnings']}"


def test_planetar_complete_extraction(monsters_raw):
    """Planetar should have complete stat block.

    Another celestial like Deva/Solar, likely multi-page.
    """
    planetar = monsters_raw.get("Planetar")
    assert planetar is not None, "Planetar not found in extraction"

    # Must have substantial block count
    block_count = len(planetar["blocks"])
    assert block_count >= 70, f"Planetar should have 70+ blocks, got {block_count}"


def test_all_monsters_minimum_blocks(monsters_raw):
    """All monsters should have at least 20 blocks.

    Regression test to catch any extraction truncation bugs.
    Even simple beasts should have ~25-30 blocks for a complete stat block.
    """
    too_short = []

    for name, monster in monsters_raw.items():
        block_count = len(monster["blocks"])
        if block_count < 20:
            too_short.append((name, block_count))

    assert len(too_short) == 0, (
        f"Found {len(too_short)} monsters with suspiciously low block counts: "
        f"{too_short[:5]}... (this may indicate extraction truncation bug)"
    )


def test_cross_page_monsters_identified(monsters_raw):
    """Identify and verify all monsters that span multiple pages.

    This test documents which monsters cross page boundaries
    and ensures they all have complete extractions.
    """
    cross_page_monsters = [
        (name, monster) for name, monster in monsters_raw.items() if len(monster["pages"]) > 1
    ]

    # Should have at least a few cross-page monsters
    assert len(cross_page_monsters) > 0, "Expected at least some monsters to span pages"

    # All cross-page monsters must have substantial block counts
    for name, monster in cross_page_monsters:
        block_count = len(monster["blocks"])
        assert block_count >= 30, (
            f"{name} spans pages {monster['pages']} but only has {block_count} blocks - "
            "possible extraction truncation"
        )


def test_no_monsters_with_zero_blocks(monsters_raw):
    """No monster should have zero blocks.

    This would indicate a severe extraction failure.
    """
    empty_monsters = [name for name, monster in monsters_raw.items() if len(monster["blocks"]) == 0]

    assert (
        len(empty_monsters) == 0
    ), f"Found {len(empty_monsters)} monsters with zero blocks: {empty_monsters}"


def test_extraction_coverage(monsters_raw):
    """Verify we extracted all 317 expected creatures."""
    assert len(monsters_raw) == 317, f"Expected 317 creatures, got {len(monsters_raw)}"


@pytest.mark.parametrize(
    "monster_name,expected_min_blocks",
    [
        ("Deva", 70),
        ("Solar", 70),
        ("Planetar", 70),
        ("Aboleth", 90),  # Known complex monster
        ("Ancient Red Dragon", 85),  # Very complex (actual: 91 blocks)
        ("Lich", 80),  # Complex spellcaster
    ],
)
def test_complex_monsters_block_counts(monsters_raw, monster_name, expected_min_blocks):
    """Verify complex monsters have substantial block counts.

    These monsters have extensive stat blocks with many traits/actions.
    Low block counts indicate incomplete extraction.
    """
    monster = monsters_raw.get(monster_name)
    if monster is None:
        pytest.skip(f"{monster_name} not found in extraction")

    block_count = len(monster["blocks"])
    assert (
        block_count >= expected_min_blocks
    ), f"{monster_name} should have {expected_min_blocks}+ blocks, got {block_count}"


def test_page_continuity(monsters_raw):
    """Verify monsters spanning pages have continuous page numbers.

    Pages should be sequential (e.g., [261, 262] not [261, 265]).
    Gaps would indicate extraction logic issues.
    """
    for name, monster in monsters_raw.items():
        pages = sorted(monster["pages"])
        if len(pages) <= 1:
            continue

        # Check for gaps
        for i in range(len(pages) - 1):
            gap = pages[i + 1] - pages[i]
            assert gap <= 2, (
                f"{name} has suspicious page gap: {pages} "
                f"(gap of {gap} between pages {pages[i]} and {pages[i + 1]})"
            )
