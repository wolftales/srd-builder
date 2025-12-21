#!/usr/bin/env python3
"""Extract raw spell class list text from SRD PDF pages 105-113.

This is step 1: get the corrupted text from the PDF.
Step 2 will be manual mapping to canonical spell names.
"""

import json
from pathlib import Path

import pymupdf


def extract_spell_class_pages() -> dict[str, str]:
    """Extract raw text from spell class list pages."""
    pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")
    pdf = pymupdf.open(pdf_path)

    # Page ranges for each class (0-indexed)
    class_pages = {
        "bard": (104, 106),  # Pages 105-106
        "cleric": (105, 107),  # Pages 106-107
        "druid": (106, 108),  # Pages 107-108
        "paladin": (107, 109),  # Pages 108-109
        "ranger": (108, 109),  # Page 109
        "sorcerer": (108, 110),  # Pages 109-110
        "warlock": (109, 111),  # Pages 110-111
        "wizard": (110, 113),  # Pages 111-113
    }

    raw_text = {}
    for class_name, (start_page, end_page) in class_pages.items():
        text_parts = []
        for page_num in range(start_page, end_page):
            page = pdf[page_num]
            text_parts.append(page.get_text())
        raw_text[class_name] = "\n".join(text_parts)

    pdf.close()
    return raw_text


if __name__ == "__main__":
    raw_text = extract_spell_class_pages()

    # Save raw extraction
    output_path = Path("rulesets/srd_5_1/raw/spell_class_lists_raw.json")
    output_path.write_text(
        json.dumps(raw_text, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Extracted raw spell class lists to: {output_path}")
    for class_name, text in raw_text.items():
        spell_count = text.count("\n  ")  # Rough count of indented lines
        print(f"  {class_name}: ~{spell_count} spell entries (corrupted)")
