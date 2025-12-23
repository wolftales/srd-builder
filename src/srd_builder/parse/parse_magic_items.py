#!/usr/bin/env python3
"""Parser for raw magic item data extracted from PDF.

Converts font-tagged raw text into structured magic item records.
"""

from __future__ import annotations

import re
from typing import Any

# Rarity keywords (in order of precedence)
RARITY_KEYWORDS = [
    "artifact",
    "legendary",
    "very rare",
    "rare",
    "uncommon",
    "common",
    "varies",
]

# Item type keywords
ITEM_TYPES = [
    "armor",
    "weapon",
    "wondrous item",
    "potion",
    "ring",
    "rod",
    "scroll",
    "staff",
    "wand",
]


def parse_magic_items(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse raw magic item data into structured records.

    Args:
        raw_data: Dict with 'items' list from extract_magic_items

    Returns:
        List of parsed magic item dictionaries
    """
    items = []

    for raw_item in raw_data.get("items", []):
        try:
            parsed = _parse_single_item(raw_item)

            # Filter out sentient magic item rule headers (page 251)
            # These are section headers like "Abilities", "Communication", etc.
            # that describe rules for sentient items, not actual items
            if _is_sentient_rule_header(parsed):
                continue

            items.append(parsed)
        except Exception as e:
            # Log warning but continue
            print(f"Warning: Failed to parse item '{raw_item.get('name', 'UNKNOWN')}': {e}")
            continue

    return items


def _parse_single_item(raw: dict[str, Any]) -> dict[str, Any]:
    """Parse a single raw magic item.

    Args:
        raw: Raw item dict with name, metadata_blocks, description_blocks, page

    Returns:
        Parsed magic item dict (not normalized - normalization happens in postprocess)
    """
    name = raw["name"].strip()

    # Parse metadata (rarity, type, attunement)
    metadata_text = _reconstruct_text(raw.get("metadata_blocks", []))
    rarity = _extract_rarity(metadata_text)
    item_type = _extract_type(metadata_text)
    requires_attunement, attunement_reqs = _extract_attunement(metadata_text)

    # Parse description
    desc_text = _reconstruct_text(raw.get("description_blocks", []))
    description = _segment_description(desc_text)

    # Extract metadata
    page = raw.get("page")
    if page is None:
        raise ValueError(f"Missing page number for item '{name}'")

    result = {
        "name": name,
        "type": item_type,
        "rarity": rarity,
        "requires_attunement": requires_attunement,
        "description": description,
        "page": page,
        "source": "SRD_CC_v5.1",
    }

    # Optional fields
    if attunement_reqs:
        result["attunement_requirements"] = attunement_reqs

    return result


def _reconstruct_text(blocks: list[dict[str, Any]]) -> str:
    """Reconstruct text from span blocks, handling whitespace.

    Args:
        blocks: List of span dicts with 'text' field

    Returns:
        Cleaned text string
    """
    if not blocks:
        return ""

    # Join all text, normalize whitespace
    text = "".join(block.get("text", "") for block in blocks)

    # Normalize whitespace (tabs, NBSP, multiple spaces)
    text = re.sub(r"[\t\r\u00a0]+", " ", text)
    text = re.sub(r" +", " ", text)
    text = text.strip()

    return text


def _extract_rarity(metadata: str) -> str:
    """Extract rarity from metadata text.

    Args:
        metadata: Metadata text (e.g., "Armor (plate), legendary")

    Returns:
        Rarity string or "common" if not found
    """
    metadata_lower = metadata.lower()

    for rarity in RARITY_KEYWORDS:
        if rarity in metadata_lower:
            return rarity

    # Default to common if not specified
    return "common"


def _extract_type(metadata: str) -> str:
    """Extract item type from metadata text.

    Args:
        metadata: Metadata text (e.g., "Armor (plate), legendary")

    Returns:
        Item type string
    """
    metadata_lower = metadata.lower()

    # Check for known types
    for item_type in ITEM_TYPES:
        if item_type in metadata_lower:
            # Capitalize properly
            if item_type == "wondrous item":
                return "Wondrous item"
            return item_type.capitalize()

    # Try to extract from parentheses (e.g., "Weapon (any sword)")
    paren_match = re.search(r"^(\w+)\s*\(", metadata)
    if paren_match:
        return paren_match.group(1).capitalize()

    # Fallback: first word
    first_word = metadata.split()[0] if metadata else "Item"
    return first_word.capitalize()


def _extract_attunement(metadata: str) -> tuple[bool, str | None]:
    """Extract attunement requirement from metadata.

    Args:
        metadata: Metadata text

    Returns:
        Tuple of (requires_attunement, attunement_requirements)
    """
    metadata_lower = metadata.lower()

    if "requires attunement" not in metadata_lower:
        return False, None

    # Check for specific requirements
    # Pattern: "requires attunement by a cleric"
    req_match = re.search(r"requires attunement\s+by\s+([^,)]+)", metadata_lower)
    if req_match:
        requirements = req_match.group(1).strip()
        return True, requirements

    # Just "requires attunement" with no specifics
    return True, None


def _segment_description(text: str) -> list[str]:
    """Segment description text into paragraphs.

    Args:
        text: Full description text

    Returns:
        List of paragraph strings
    """
    if not text:
        return [""]

    # Split on sentence boundaries that indicate new paragraphs
    # Look for period followed by capital letter (new sentence that might be new paragraph)
    # For now, keep as single paragraph since we don't have clear paragraph markers

    # Clean up the text
    text = text.strip()

    # For v1, return as single paragraph
    # TODO: Add smarter paragraph detection if needed
    return [text] if text else [""]


def _is_sentient_rule_header(item: dict[str, Any]) -> bool:
    """Check if item is a sentient magic item rule section header.

    Page 251 has section headers for sentient magic items rules
    (Abilities, Communication, Senses, Alignment, Special Purpose)
    that get extracted as items. Filter these out.

    Args:
        item: Parsed magic item dict

    Returns:
        True if this is a rule header, not an actual item
    """
    # Check if type is "Item" (these headers don't match standard types)
    if item.get("type") != "Item":
        return False

    # Check if description mentions sentient items (rule headers do)
    description = " ".join(item.get("description", []))
    if "sentient" in description.lower():
        return True

    return False


def main() -> None:
    """CLI entry point for testing parsing."""
    import json
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <raw_magic_items.json>")
        sys.exit(1)

    raw_path = Path(sys.argv[1])
    raw_data = json.loads(raw_path.read_text())

    items = parse_magic_items(raw_data)

    print(f"Parsed {len(items)} magic items")

    # Show first few
    for item in items[:5]:
        print(f"\n{item['name']}")
        print(f"  ID: {item['id']}")
        print(f"  Type: {item['type']}, Rarity: {item['rarity']}")
        print(f"  Attunement: {item['requires_attunement']}")
        if item.get("attunement_requirements"):
            print(f"  Attunement reqs: {item['attunement_requirements']}")
        print(f"  Description: {item['description'][0][:100]}...")


if __name__ == "__main__":
    main()
