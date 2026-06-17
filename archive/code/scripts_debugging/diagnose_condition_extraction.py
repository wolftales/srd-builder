#!/usr/bin/env python3
"""Diagnostic script to understand condition extraction issues.

Reproduces the exact bug: condition:prone gets condition:blinded text,
condition:invisible concatenates ALL conditions due to poor column handling.
"""

import json
from pathlib import Path


def extract_with_default(pdf_path: Path):
    """Extract using default get_text() - what we currently do (BROKEN)."""
    import fitz

    doc = fitz.open(pdf_path)
    text = ""
    for page_num in [357, 358]:  # 0-indexed
        page = doc[page_num]
        text += page.get_text()
    doc.close()

    return text


def extract_with_blocks(pdf_path: Path):
    """Extract using text blocks with position info."""
    import fitz

    doc = fitz.open(pdf_path)
    blocks_info = []

    for page_num in [357, 358]:  # 0-indexed
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            bbox = block["bbox"]
            text = ""
            for line in block["lines"]:
                for span in line["spans"]:
                    text += span["text"]
                text += " "

            blocks_info.append(
                {
                    "page": page_num + 1,
                    "x": round(bbox[0], 1),
                    "y": round(bbox[1], 1),
                    "width": round(bbox[2] - bbox[0], 1),
                    "text": text.strip()[:100],  # First 100 chars
                }
            )

    doc.close()
    return blocks_info


def extract_with_sort(pdf_path: Path):
    """Extract with explicit column sorting."""
    import fitz

    doc = fitz.open(pdf_path)

    for page_num in [357, 358]:  # 0-indexed
        page = doc[page_num]

        # Get page dimensions
        page_rect = page.rect
        mid_x = page_rect.width / 2

        print(f"\n=== PAGE {page_num + 1} (width={page_rect.width:.1f}) ===")
        print(f"Column split at x={mid_x:.1f}\n")

        # Extract blocks with position
        blocks = page.get_text("dict")["blocks"]

        left_col = []
        right_col = []

        for block in blocks:
            if "lines" not in block:
                continue

            bbox = block["bbox"]
            block_x = bbox[0]
            block_y = bbox[1]

            text = ""
            for line in block["lines"]:
                for span in line["spans"]:
                    text += span["text"]

            if block_x < mid_x:
                left_col.append((block_y, text.strip()))
            else:
                right_col.append((block_y, text.strip()))

        # Sort by y position
        left_col.sort()
        right_col.sort()

        print("LEFT COLUMN:")
        for y, text in left_col[:10]:  # First 10 blocks
            print(f"  y={y:5.1f}: {text[:80]}")

        print("\nRIGHT COLUMN:")
        for y, text in right_col[:10]:  # First 10 blocks
            print(f"  y={y:5.1f}: {text[:80]}")

    doc.close()


def main():
    """Run diagnostics."""
    import sys

    if len(sys.argv) < 2:
        # Default to known location
        pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")
        if not pdf_path.exists():
            print("Usage: python diagnose_condition_extraction.py <pdf_path>")
            print(f"Default PDF not found: {pdf_path}")
            return 1
        print(f"Using default PDF: {pdf_path}")
    else:
        pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return 1

    print(f"Analyzing: {pdf_path}\n")
    print("=" * 80)

    # Diagnostic 1: Default extraction (what we currently do)
    print("\n### DIAGNOSTIC 1: Default get_text() ###")
    default_text = extract_with_default(pdf_path)

    # Look for condition headers
    condition_names = [
        "Blinded",
        "Charmed",
        "Deafened",
        "Grappled",
        "Incapacitated",
        "Invisible",
        "Prone",
    ]

    print("\nCondition header positions in linearized text:")
    for name in condition_names:
        pos = default_text.find(name)
        if pos >= 0:
            context = default_text[max(0, pos - 50) : pos + 100]
            print(f"\n{name} at pos {pos}:")
            print(f"  ...{context}...")

    # Diagnostic 2: Block positions
    print("\n\n" + "=" * 80)
    print("### DIAGNOSTIC 2: Block positions ###")
    blocks = extract_with_blocks(pdf_path)

    # Save to file for analysis
    output_path = Path("condition_blocks.json")
    with open(output_path, "w") as f:
        json.dump(blocks, f, indent=2)
    print(f"\nSaved block data to: {output_path}")

    # Show blocks containing condition names
    print("\nBlocks containing condition names:")
    for block in blocks:
        text_lower = block["text"].lower()
        for name in condition_names:
            if name.lower() in text_lower:
                print(f"\n{name} found:")
                print(f"  Page {block['page']}, x={block['x']}, y={block['y']}")
                print(f"  Text: {block['text'][:120]}")

    # Diagnostic 3: Column-aware extraction
    print("\n\n" + "=" * 80)
    print("### DIAGNOSTIC 3: Column-aware sorting ###")
    extract_with_sort(pdf_path)

    print("\n\n" + "=" * 80)
    print("\nDiagnostics complete!")
    print("\nConclusions:")
    print("1. Check if default extraction jumps between columns")
    print("2. Review block positions to see if we need spatial sorting")
    print("3. Compare column-aware sorting to see proper reading order")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
