#!/usr/bin/env python3
"""Debug the actual order of conditions in the PDF to understand layout."""

from pathlib import Path

import fitz


def analyze_condition_layout():
    """Show exactly where each condition header appears in the PDF."""
    pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")
    doc = fitz.open(pdf_path)

    conditions = [
        "Blinded",
        "Charmed",
        "Deafened",
        "Exhaustion",
        "Frightened",
        "Grappled",
        "Incapacitated",
        "Invisible",
        "Paralyzed",
        "Petrified",
        "Poisoned",
        "Prone",
        "Restrained",
        "Stunned",
        "Unconscious",
    ]

    print("Searching for condition headers on pages 358-359...\n")

    for page_num in [357, 358]:  # 0-indexed
        page = doc[page_num]
        print(f"=== PAGE {page_num + 1} ===")
        print(f"Page dimensions: {page.rect.width:.1f} x {page.rect.height:.1f}")
        print()

        # Search for each condition
        found_conditions = []
        for condition in conditions:
            # Search for the condition name
            instances = page.search_for(condition)
            for inst in instances:
                x, y = inst.x0, inst.y0
                found_conditions.append((y, x, condition, inst))

        # Sort by y position (top to bottom)
        found_conditions.sort()

        print(f"Found {len(found_conditions)} condition references:\n")
        for y, x, name, rect in found_conditions:
            column = "LEFT " if x < 306 else "RIGHT"
            print(f"  {column} | y={y:6.1f}, x={x:6.1f} | {name:15s} | bbox={rect}")
        print()

    doc.close()


if __name__ == "__main__":
    analyze_condition_layout()
