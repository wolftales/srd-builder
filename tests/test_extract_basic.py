"""Test basic monster extraction and parsing.

This test suite verifies fundamental extraction capabilities:
- Monster name detection
- Stat label parsing (AC, HP, Speed, etc.)
- Font pattern recognition
- Block structure correctness
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


def test_extraction_completeness(monsters_raw):
    """Verify we extract the expected number of monsters."""
    assert len(monsters_raw) == 317, f"Expected 317 monsters, got {len(monsters_raw)}"


def test_monster_has_required_structure(monsters_raw):
    """Every monster should have name, pages, blocks, and warnings fields."""
    for name, monster in list(monsters_raw.items())[:10]:  # Sample 10 monsters
        assert "name" in monster, f"{name}: missing 'name' field"
        assert "pages" in monster, f"{name}: missing 'pages' field"
        assert "blocks" in monster, f"{name}: missing 'blocks' field"
        assert "warnings" in monster, f"{name}: missing 'warnings' field"

        assert isinstance(monster["pages"], list), f"{name}: pages should be list"
        assert isinstance(monster["blocks"], list), f"{name}: blocks should be list"
        assert isinstance(monster["warnings"], list), f"{name}: warnings should be list"


def test_monster_name_detection(monsters_raw):
    """Verify monster names are extracted correctly (known examples)."""
    expected_names = [
        "Aboleth",
        "Adult Black Dragon",
        "Goblin",
        "Tarrasque",
        "Ancient Red Dragon",
    ]

    for name in expected_names:
        assert name in monsters_raw, f"Expected monster '{name}' not found"


def test_blocks_have_required_fields(monsters_raw):
    """Every block should have text, font, size, and bbox fields."""
    goblin = monsters_raw.get("Goblin")
    assert goblin is not None, "Goblin not found"

    for i, block in enumerate(goblin["blocks"][:20]):  # Check first 20 blocks
        assert "text" in block, f"Goblin block {i}: missing 'text'"
        assert "font" in block, f"Goblin block {i}: missing 'font'"
        assert "size" in block, f"Goblin block {i}: missing 'size'"
        assert "bbox" in block, f"Goblin block {i}: missing 'bbox'"
        assert "page" in block, f"Goblin block {i}: missing 'page'"


def test_font_pattern_recognition(monsters_raw):
    """Verify font patterns are preserved (Bold, Italic, etc.)."""
    goblin = monsters_raw.get("Goblin")
    assert goblin is not None

    # Find Bold blocks (stat labels like "Armor Class", "Hit Points")
    bold_blocks = [b for b in goblin["blocks"] if "Bold" in b.get("font", "")]
    assert len(bold_blocks) > 5, "Goblin should have multiple Bold blocks for stat labels"

    # Find Italic blocks (size/type/alignment line)
    italic_blocks = [b for b in goblin["blocks"] if "Italic" in b.get("font", "")]
    assert len(italic_blocks) > 0, "Goblin should have Italic blocks"


def test_stat_label_detection(monsters_raw):
    """Verify common stat labels are present in extracted blocks."""
    aboleth = monsters_raw.get("Aboleth")
    assert aboleth is not None

    # Collect all block text
    all_text = " ".join(b.get("text", "") for b in aboleth["blocks"]).lower()

    # Common stat labels that should appear
    expected_labels = ["armor", "class", "hit", "points", "speed", "str", "dex", "con"]

    for label in expected_labels:
        assert label in all_text, f"Aboleth should have '{label}' in block text"


def test_page_numbers_are_valid(monsters_raw):
    """All monsters should have valid page numbers (261-403)."""
    for name, monster in monsters_raw.items():
        pages = monster.get("pages", [])
        assert len(pages) > 0, f"{name}: should have at least one page"

        for page in pages:
            assert 261 <= page <= 403, f"{name}: page {page} outside SRD creature section (261-403)"


def test_no_extraction_warnings(monsters_raw):
    """Most monsters should extract without warnings."""
    monsters_with_warnings = [
        name for name, m in monsters_raw.items() if len(m.get("warnings", [])) > 0
    ]

    # Allow some warnings but not too many
    warning_rate = len(monsters_with_warnings) / len(monsters_raw)
    assert warning_rate < 0.05, (
        f"Too many monsters with warnings: {len(monsters_with_warnings)}/296 ({warning_rate:.1%})"
    )


def test_block_count_reasonable(monsters_raw):
    """Monsters should have reasonable block counts (not empty, not excessive)."""
    for name, monster in list(monsters_raw.items())[:50]:  # Sample 50 monsters
        block_count = len(monster.get("blocks", []))
        assert block_count >= 10, f"{name}: too few blocks ({block_count}), stat block incomplete?"
        assert block_count <= 500, f"{name}: too many blocks ({block_count}), extraction error?"


def test_font_sizes_in_expected_range(monsters_raw):
    """Block font sizes should be in expected range (9-13pt for monster stats)."""
    goblin = monsters_raw.get("Goblin")
    assert goblin is not None

    for block in goblin["blocks"]:
        size = block.get("size", 0)
        # Most monster stat block text is 9-13pt
        # (9.84pt for stats, 10.8pt for headers, 12pt for name)
        if size > 0:  # Skip blocks without size info
            assert 8 <= size <= 14, (
                f"Goblin block has unusual font size: {size}pt (text: {block.get('text', '')[:50]})"
            )
