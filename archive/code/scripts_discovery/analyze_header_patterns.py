#!/usr/bin/env python3
"""Analyze what makes condition section headers different from body mentions."""

from pathlib import Path

import fitz


def analyze_header_patterns():
    """Check font metadata and patterns around condition headers."""
    pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")
    doc = fitz.open(pdf_path)

    # Focus on page 358 where we know Blinded/Charmed/Deafened are
    page = doc[357]  # 0-indexed

    print("Analyzing text blocks on page 358...\n")
    print("Looking for patterns that distinguish section headers from body text.\n")

    blocks = page.get_text("dict")["blocks"]

    condition_blocks = []
    for block in blocks:
        if "lines" not in block:
            continue

        bbox = block["bbox"]
        text = ""
        fonts = []
        sizes = []

        for line in block["lines"]:
            for span in line["spans"]:
                text += span["text"]
                fonts.append(span["font"])
                sizes.append(span["size"])

        # Check if this block contains a condition name
        conditions = ["Blinded", "Charmed", "Deafened", "Grappled", "Invisible"]
        for cond in conditions:
            if cond in text:
                condition_blocks.append(
                    {
                        "text": text[:150],
                        "bbox": bbox,
                        "fonts": list(set(fonts)),
                        "sizes": list(set(sizes)),
                        "condition": cond,
                    }
                )

    # Show the blocks
    print(f"Found {len(condition_blocks)} blocks mentioning conditions:\n")
    for i, block in enumerate(condition_blocks, 1):
        x, y = block["bbox"][0], block["bbox"][1]
        column = "LEFT " if x < 306 else "RIGHT"
        print(f"{i}. {column} | x={x:5.1f}, y={y:5.1f}")
        print(f"   Condition: {block['condition']}")
        print(f"   Fonts: {block['fonts']}")
        print(f"   Sizes: {block['sizes']}")
        print(f"   Text: {block['text'][:100]}...")
        print()

    doc.close()


if __name__ == "__main__":
    analyze_header_patterns()
