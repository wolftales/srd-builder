"""Test raw PDF extraction output structure.

This test validates the raw extraction output from extract_monsters.py
(monsters_raw.json) which is then stored as a test fixture.

The fixture represents the intermediate format between PDF extraction
and parsing - it has blocks, font metadata, and markers but not yet
the parsed stat block fields like armor_class, hit_points, etc.
"""

import json
from pathlib import Path


def test_raw_extraction_structure() -> None:
    """Verify raw extraction output has expected structure.

    Raw extraction from PDF should produce monsters with:
    - name: extracted monster name
    - blocks: array of text blocks with font metadata
    - pages: page numbers where monster appears
    - markers: detected section markers (Speed, Skills, etc.)
    - warnings: any extraction issues encountered
    """
    raw = json.loads(Path("tests/fixtures/srd_5_1/raw/monsters.json").read_text())
    assert isinstance(raw, list) and raw, "Raw extraction should be non-empty list"

    for monster in raw:
        # Core extraction fields
        assert "name" in monster, "Monster missing name field"
        assert "blocks" in monster, f"{monster.get('name', 'Unknown')} missing blocks"
        assert "pages" in monster, f"{monster.get('name', 'Unknown')} missing pages"
        assert "markers" in monster, f"{monster.get('name', 'Unknown')} missing markers"

        # Blocks should have font metadata
        if monster["blocks"]:
            first_block = monster["blocks"][0]
            assert "text" in first_block, "Block missing text"
            assert "bbox" in first_block, "Block missing bounding box"
