#!/usr/bin/env python3
"""Count monster stat blocks directly from the SRD PDF.

This script scans the PDF pages 261-394 looking for monster names
using the same pattern our extractor uses (12pt Calibri-Bold).
This gives us the ground truth for how many monsters actually exist.
"""

from pathlib import Path

import fitz  # PyMuPDF


def count_monsters_in_pdf(pdf_path: Path) -> tuple[int, list[str]]:
    """Count monsters by scanning for 12pt Bold monster names.

    Returns:
        (count, list of monster names)
    """
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return 0, []

    monster_names = []

    with fitz.open(pdf_path) as doc:
        # Pages 261-394 (0-indexed: 260-393)
        for page_num in range(260, 394):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if block.get("type") != 0:  # Only text blocks
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        font = span.get("font", "")
                        size = span.get("size", 0)
                        flags = span.get("flags", 0)

                        # Monster name pattern: 12pt Calibri-Bold at start of stat block
                        # We look for 12pt, Bold, and reasonable text
                        is_bold = (flags & 2**4) != 0  # Bold flag
                        is_12pt = 11.5 <= size <= 12.5
                        is_calibri = "Calibri" in font

                        # Filter: reasonable monster name length and structure
                        is_reasonable_name = (
                            len(text) > 2
                            and len(text) < 80
                            and text[0].isupper()
                            and not text.endswith(":")
                            and not text.startswith("Chapter")
                        )

                        if is_bold and is_12pt and is_calibri and is_reasonable_name:
                            # Likely a monster name
                            if text not in monster_names:
                                monster_names.append(text)

    return len(monster_names), monster_names


def main() -> None:  # noqa: C901
    """Main entry point."""
    print("=" * 80)
    print("PDF Monster Count Analysis")
    print("=" * 80)
    print()

    # Find any PDF in raw directory
    raw_dir = Path("rulesets/srd_5_1/raw")
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        print("Error: No PDF found in rulesets/srd_5_1/raw/")
        print("Please download the SRD PDF and place it in that directory.")
        return
    pdf_path = pdf_files[0]
    print(f"Using PDF: {pdf_path.name}")

    count, names = count_monsters_in_pdf(pdf_path)

    print(f"📊 Total monsters found: {count}")
    print("📄 Pages scanned: 261-394 (134 pages)")
    print()

    if names:
        print("First 20 monsters:")
        for name in names[:20]:
            print(f"  • {name}")

        if count > 20:
            print(f"  ... and {count - 20} more")

        print()
        print("Last 10 monsters:")
        for name in names[-10:]:
            print(f"  • {name}")

    print()
    print("=" * 80)
    print("Comparison with Our Extraction")
    print("=" * 80)

    # Load our extraction
    import json

    our_path = Path("dist/srd_5_1/data/monsters.json")
    if our_path.exists():
        our_data = json.loads(our_path.read_text(encoding="utf-8"))
        our_names = {m["name"] for m in our_data["items"]}

        print(f"\n✅ Our extraction: {len(our_names)} monsters")
        print(f"📊 PDF 12pt Bold count: {count}")
        print(f"📈 Difference: {count - len(our_names)}")

        if count == len(our_names):
            print("\n🎉 Perfect match! We extracted all monsters from the PDF.")
        elif count > len(our_names):
            # Find what we're missing
            pdf_set = set(names)
            missing = pdf_set - our_names
            print(f"\n⚠️  Missing from our extraction: {len(missing)}")
            for name in sorted(missing)[:20]:
                print(f"  • {name}")
        else:
            # We have more than the simple count suggests
            our_only = our_names - set(names)
            print(f"\n🤔 We extracted MORE than simple 12pt Bold count: {len(our_only)}")
            print("   (This could be multi-column monsters or special formatting)")
            for name in sorted(our_only)[:20]:
                print(f"  • {name}")
    else:
        print(
            "\n⚠️  No extraction found. Run: python -m srd_builder.build --ruleset srd_5_1 --out dist"
        )

    print()
    print("=" * 80)
    print("Conclusion")
    print("=" * 80)
    print(
        """
This script counts 12pt Calibri-Bold text blocks in pages 261-394,
which is the same pattern used by our extractor to identify monster names.

If the counts match, we can confidently say we've extracted all monsters.
If not, we need to investigate the discrepancy.

Note: This is a simple heuristic. Some edge cases may exist:
- Monsters with unusual formatting
- Split stat blocks across pages
- Headers/footers that match the pattern
"""
    )


if __name__ == "__main__":
    main()
