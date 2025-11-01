#!/usr/bin/env python3
"""Extract equipment tables from SRD PDF using PyMuPDF table finder.

Equipment is structured in tables (pages 62-73) with different formats:
- Armor: Name | Cost | AC | Strength | Stealth | Weight
- Weapons: Name | Cost | Damage | Weight | Properties
- Gear: Name | Cost | Weight | (Description)

Strategy:
1. Use PyMuPDF find_tables() to extract table rows
2. Track section context via 18pt headers (Armor, Weapons, etc.)
3. Each table = one equipment row
4. Preserve raw column data for parsing phase
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from .context_tracker import ContextTracker

logger = logging.getLogger(__name__)

# Equipment section pages (0-indexed)
EQUIPMENT_START_PAGE = 61  # Page 62
EQUIPMENT_END_PAGE = 72  # Page 73

# Font patterns for section detection
SECTION_HEADER_SIZE = 18.0
SUBSECTION_HEADER_SIZE = 13.92

# Section keywords for categorization
ARMOR_KEYWORDS = ["armor", "light armor", "medium armor", "heavy armor"]
WEAPON_KEYWORDS = ["weapon", "simple melee", "simple ranged", "martial melee", "martial ranged"]
GEAR_KEYWORDS = ["adventuring gear", "tools", "equipment packs"]
MOUNT_KEYWORDS = ["mounts", "vehicles", "tack"]
TRADE_KEYWORDS = ["trade goods", "expenses"]


def extract_equipment(pdf_path: Path) -> dict[str, Any]:
    """Extract equipment from SRD PDF.

    Returns:
        Dictionary with:
        - equipment: list of raw equipment entries with table data
        - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Extracting equipment from {pdf_path}")

    doc = fitz.open(pdf_path)
    equipment_items: list[dict[str, Any]] = []
    warnings: list[str] = []

    tracker = ContextTracker(initial_category="gear")

    try:
        # Process equipment pages
        for page_num in range(EQUIPMENT_START_PAGE, EQUIPMENT_END_PAGE + 1):
            page = doc[page_num]
            page_items = _extract_page_equipment(page, page_num, tracker, warnings)
            equipment_items.extend(page_items)

        logger.info(f"Extracted {len(equipment_items)} equipment items")

    finally:
        doc.close()

    return {
        "equipment": equipment_items,
        "_meta": {
            "items_extracted": len(equipment_items),
            "pages_processed": list(range(EQUIPMENT_START_PAGE, EQUIPMENT_END_PAGE + 1)),
            "warnings": warnings,
        },
    }


def _extract_page_equipment(
    page: fitz.Page,
    page_num: int,
    tracker: ContextTracker,
    warnings: list[str],
) -> list[dict[str, Any]]:
    """Extract equipment from a single page using table finder.

    Returns:
        Tuple of (items, updated_section) to carry context across pages.
    """
    items = []

    tracker.start_page(page_num + 1)

    # Check for new section headers on this page (with Y positions)
    section_markers = _get_section_markers(page, page_num)

    marker_sections = [marker for _, marker in section_markers]

    # Extract tables (each row = one table)
    try:
        table_finder = page.find_tables()
        tables = table_finder.tables

        logger.debug(f"Page {page_num + 1}: Found {len(tables)} tables")

        for table in tables:
            raw_rows = table.extract()
            header, rows = _split_header_and_rows(raw_rows)
            if not rows:
                continue

            cleaned_rows = [_merge_split_name(row) for row in rows]

            for row_index, row in enumerate(cleaned_rows):
                if not _is_equipment_row(row):
                    logger.debug(f"  Skipped non-equipment: {row[0] if row else 'empty'}")
                    continue

                table_y = table.bbox[1]
                section_for_table = tracker.context_for_position(section_markers, table_y)

                item = {
                    "page": page_num + 1,
                    "section": dict(section_for_table),
                    "table_row": row,
                    "table_headers": header,
                    "row_index": row_index,
                    "bbox": table.bbox,
                }
                items.append(item)
                logger.debug(
                    f"  Extracted: {row[0] if row else 'empty'} (cat={section_for_table['category']})"
                )

    except Exception as e:
        warnings.append(f"Page {page_num + 1}: Table extraction failed - {e}")
        logger.warning(f"Page {page_num + 1}: {e}")

    tracker.propagate(marker_sections)

    return items


def _get_section_markers(  # noqa: C901
    page: fitz.Page, page_num: int
) -> list[tuple[float, dict[str, str | None]]]:
    """Get section markers with Y positions for position-aware categorization.

    Returns:
        List of (y_position, section_dict) sorted by Y position.
    """
    markers: list[tuple[float, dict[str, str | None]]] = []
    blocks = page.get_text("dict")["blocks"]

    for block in blocks:
        if block.get("type") != 0:
            continue

        y_pos = block["bbox"][1]  # y0 (top)

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip().lower()
                size = span.get("size", 0)
                category = None
                subcategory = None

                # Section header (18pt)
                if abs(size - SECTION_HEADER_SIZE) < 0.5:
                    if "armor" in text:
                        category = "armor"
                    elif "weapon" in text:
                        category = "weapon"
                    elif any(kw in text for kw in GEAR_KEYWORDS):
                        category = "gear"
                    elif any(kw in text for kw in MOUNT_KEYWORDS):
                        category = "mount"
                    elif any(kw in text for kw in TRADE_KEYWORDS):
                        category = "trade_good"

                # Subsection header (13.92pt)
                elif abs(size - SUBSECTION_HEADER_SIZE) < 0.5:
                    if "armor" in text:
                        category = "armor"
                        if "light" in text:
                            subcategory = "light"
                        elif "medium" in text:
                            subcategory = "medium"
                        elif "heavy" in text:
                            subcategory = "heavy"

                if category:
                    markers.append((y_pos, {"category": category, "subcategory": subcategory}))

    return sorted(markers)  # Sort by Y position


def _detect_section_context(  # noqa: C901
    page: fitz.Page, page_num: int
) -> dict[str, str | None] | None:
    """Detect current section context from headers.

    Returns:
        Dict with category, subcategory if headers found, None otherwise.
    """
    blocks = page.get_text("dict")["blocks"]

    # Scan for section headers (18pt or 13.92pt)
    category = None
    subcategory = None

    for block in blocks:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip().lower()
                size = span.get("size", 0)

                # Section header (18pt)
                if abs(size - SECTION_HEADER_SIZE) < 0.5:
                    if "armor" in text:
                        category = "armor"
                    elif "weapon" in text:
                        category = "weapon"
                    elif any(kw in text for kw in GEAR_KEYWORDS):
                        category = "gear"
                    elif any(kw in text for kw in MOUNT_KEYWORDS):
                        category = "mount"
                    elif any(kw in text for kw in TRADE_KEYWORDS):
                        category = "trade_good"

                # Subsection header (13.92pt)
                elif abs(size - SUBSECTION_HEADER_SIZE) < 0.5:
                    if "armor" in text:
                        # Armor subcategories also set the category
                        category = "armor"
                        if "light" in text:
                            subcategory = "light"
                        elif "medium" in text:
                            subcategory = "medium"
                        elif "heavy" in text:
                            subcategory = "heavy"
                    elif "melee" in text or "ranged" in text:
                        # Weapon subcategories
                        if "simple" in text and "melee" in text:
                            subcategory = "simple_melee"
                        elif "simple" in text and "ranged" in text:
                            subcategory = "simple_ranged"
                        elif "martial" in text and "melee" in text:
                            subcategory = "martial_melee"
                        elif "martial" in text and "ranged" in text:
                            subcategory = "martial_ranged"

    # Only return if we found something
    if category is not None:
        return {"category": category, "subcategory": subcategory}

    return None


def _is_equipment_row(row: list[str]) -> bool:  # noqa: C901
    """Check if table row contains actual equipment (vs headers/descriptions).

    Filters out:
    - Empty rows or headers
    - Section header rows (Light Armor, Medium Armor, etc.)
    - Currency table entries
    - Reference tables (Trade Goods pricing, Lifestyle Expenses, Food/Drink)
    - Descriptive text
    """
    if not row or len(row) < 2:
        return False

    # First column should be item name (not empty, not a header)
    name = row[0].strip()
    if not name:
        return False

    # Filter section header rows (armor subcategory labels within tables)
    # These appear as single-cell rows like "Light Armor", "Medium Armor", "Heavy Armor"
    if name.lower() in ["light armor", "medium armor", "heavy armor", "shields"]:
        return False

    # Filter Trade Goods pricing tables where first cell is price (reversed structure)
    # Example: ['1 cp', '1 lb. of wheat'] - price first, item second
    if re.match(r"^\d+\s*(cp|sp|ep|gp|pp)$", name, re.IGNORECASE):
        return False

    # Filter Lifestyle Expenses levels (not actual items)
    lifestyle_levels = [
        "poor",
        "modest",
        "comfortable",
        "wealthy",
        "aristocratic",
        "wretched",
        "squalid",
    ]
    if name.lower() in lifestyle_levels:
        return False

    # Filter Food/Drink/Lodging incomplete extractions
    # Single-word entries with only a price in second column are likely reference table fragments
    if len(row) == 2 and len(name.split()) == 1:
        second_cell = row[1].strip()
        # If second cell is just a price, this is likely a pricing reference, not equipment
        if re.match(r"^\d+\s*(cp|sp|ep|gp|pp)$", second_cell, re.IGNORECASE):
            # Exception: Some valid items are single words (Rope, Tent, etc.)
            # But those appear in tables with more columns typically
            return False

    # Skip currency table entries
    currency_keywords = ["copper", "silver", "electrum", "gold", "platinum"]
    if any(kw in name.lower() for kw in currency_keywords):
        # Check if it's just the currency name (not "Gold ring", etc.)
        if any(name.lower().startswith(kw) for kw in currency_keywords):
            return False

    # Skip obvious headers
    header_keywords = [
        "armor",
        "weapon",
        "item",
        "name",
        "cost",
        "damage",
        "weight",
        "properties",
        "category",
        "simple",
        "martial",
        "melee",
        "ranged",
    ]
    if any(kw in name.lower() for kw in header_keywords) and len(name) < 25:
        return False

    # Skip descriptive text (usually long paragraphs)
    if len(name) > 100:
        return False

    # Must have at least one non-empty value in other columns (cost, damage, etc.)
    has_data = any(cell.strip() and cell.strip() != "—" for cell in row[1:])

    return has_data


def _merge_split_name(row: list[str]) -> list[str]:
    """
    Merge split item names across first two columns.
    PyMuPDF sometimes splits names like "Longswor" + "d" → "Longsword"
    """
    if len(row) < 2:
        return row

    first = str(row[0]).strip()
    second = str(row[1]).strip()

    # If second column is very short (1-3 chars) and looks like a fragment, merge it
    if second and len(second) <= 3 and second.isalpha() and not second.islower():
        # Merge and remove second column
        merged_name = first + second.lower()
        return [merged_name] + row[2:]

    # If second column is very short and is lowercase, it's likely a fragment
    if second and len(second) <= 3 and second.islower():
        merged_name = first + second
        return [merged_name] + row[2:]

    return row


def _split_header_and_rows(
    table_rows: list[list[str]] | None,
) -> tuple[list[str] | None, list[list[str]]]:
    """Separate header row from data rows when possible."""

    if not table_rows:
        return None, []

    cleaned_rows: list[list[str]] = []
    for raw_row in table_rows:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in raw_row]
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return None, []

    header_candidate = cleaned_rows[0]
    if _looks_like_header(header_candidate):
        return header_candidate, cleaned_rows[1:]

    return None, cleaned_rows


def _looks_like_header(row: list[str]) -> bool:
    """Heuristically determine whether a row is a column header."""

    header_keywords = [
        "armor",
        "armor class",
        "ac",
        "cost",
        "damage",
        "weight",
        "properties",
        "strength",
        "stealth",
        "type",
    ]

    normalized_cells = [cell.lower() for cell in row if cell and cell.strip()]
    if not normalized_cells:
        return False

    matches = 0
    for cell in normalized_cells:
        if any(keyword in cell for keyword in header_keywords):
            matches += 1

    return matches >= max(1, len(normalized_cells) // 2)


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.DEBUG)

    pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")

    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    result = extract_equipment(pdf_path)

    print(f"\n{'=' * 80}")
    print("EXTRACTION RESULTS")
    print("=" * 80)
    print(f"Items extracted: {result['_meta']['items_extracted']}")
    print(f"Pages processed: {len(result['_meta']['pages_processed'])}")
    print(f"Warnings: {len(result['_meta']['warnings'])}")

    if result["_meta"]["warnings"]:
        print("\nWarnings:")
        for warning in result["_meta"]["warnings"]:
            print(f"  - {warning}")

    # Show samples
    categories: dict[str, list[dict[str, Any]]] = {}
    for item in result["equipment"]:
        cat = item["section"]["category"]
        categories.setdefault(cat, []).append(item)

    print(f"\nCategories found: {list(categories.keys())}")

    for cat, items in categories.items():
        print(f"\n{cat.upper()} ({len(items)} items) - First 3:")
        for item in items[:3]:
            row = item["table_row"]
            print(f"  - {row[0][:50]} | Page {item['page']}")
            print(f"    Subcategory: {item['section'].get('subcategory')}")
            print(f"    Columns: {len(row)}")

    # Save for inspection
    output_path = Path("/tmp/equipment_extracted.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nFull output saved to: {output_path}")
