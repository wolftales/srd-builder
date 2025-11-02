#!/usr/bin/env python3
"""Build comprehensive table of contents for SRD PDF.

This creates a reusable reference document that maps PDF structure,
avoiding re-scanning on every new dataset extraction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pymupdf


def build_srd_toc(pdf_path: Path) -> dict[str, Any]:
    """Scan PDF and build comprehensive table of contents.

    Returns:
        Dictionary with section mappings, page ranges, and content markers
    """
    pdf = pymupdf.open(pdf_path)

    toc: dict[str, Any] = {
        "metadata": {
            "total_pages": len(pdf),
            "pdf_sha256": None,  # Will be filled from pdf_meta.json
        },
        "sections": {},
        "content_markers": [],
    }

    # Known section keywords to look for
    section_keywords: dict[str, list[str]] = {
        "races": ["Races", "Racial Traits"],
        "classes": ["Classes", "Class Features"],
        "beyond_1st_level": ["Beyond 1st Level"],
        "equipment": ["Equipment"],
        "feats": ["Feats"],
        "using_ability_scores": ["Using Ability Scores"],
        "adventuring": ["Adventuring"],
        "combat": ["Combat"],
        "spellcasting": ["Spellcasting"],
        "spell_lists": ["Spell Lists", "Bard Spells", "Cleric Spells"],
        "spell_descriptions": ["Spell Descriptions"],
        "conditions": ["Conditions", "Appendix A"],
        "gods": ["Gods", "Appendix B"],
        "planes": ["Planes of Existence"],
        "creatures": ["Creatures", "Monsters"],
        "monster_lists": ["Monster Lists"],
    }

    # Scan for section markers
    for page_num in range(len(pdf)):
        page = pdf[page_num]
        text = page.get_text()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Check first 15 lines of each page for section headers
        for line in lines[:15]:
            for section_id, keywords in section_keywords.items():
                for keyword in keywords:
                    if keyword in line and section_id not in toc["sections"]:
                        toc["sections"][section_id] = {
                            "start_page": page_num + 1,
                            "marker": line,
                        }
                        toc["content_markers"].append(
                            {
                                "page": page_num + 1,
                                "section": section_id,
                                "text": line,
                            }
                        )

    # Calculate end pages by looking at next section
    section_list = sorted(toc["sections"].items(), key=lambda x: x[1]["start_page"])
    for i, (_section_id, data) in enumerate(section_list):
        if i < len(section_list) - 1:
            next_start = section_list[i + 1][1]["start_page"]
            data["end_page"] = next_start - 1
        else:
            data["end_page"] = len(pdf)

    # Add specific content we know about
    toc["known_content"] = {
        "lineages": {
            "names": [
                "Dwarf",
                "Elf",
                "Halfling",
                "Human",
                "Dragonborn",
                "Gnome",
                "Half-Elf",
                "Half-Orc",
                "Tiefling",
            ],
            "section": "races",
        },
        "classes": {
            "names": [
                "Barbarian",
                "Bard",
                "Cleric",
                "Druid",
                "Fighter",
                "Monk",
                "Paladin",
                "Ranger",
                "Rogue",
                "Sorcerer",
                "Warlock",
                "Wizard",
            ],
            "section": "classes",
        },
        "conditions": {
            "names": [
                "Blinded",
                "Charmed",
                "Deafened",
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
            ],
            "section": "conditions",
        },
    }

    pdf.close()
    return toc


def main():
    pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")
    output_path = Path("rulesets/srd_5_1/raw/srd_toc.json")

    print("Building SRD table of contents...")
    toc = build_srd_toc(pdf_path)

    # Add PDF hash from pdf_meta.json if available
    pdf_meta_path = Path("rulesets/srd_5_1/raw/pdf_meta.json")
    if pdf_meta_path.exists():
        with open(pdf_meta_path) as f:
            pdf_meta = json.load(f)
            toc["metadata"]["pdf_sha256"] = pdf_meta.get("pdf_sha256")

    # Write TOC
    output_path.write_text(json.dumps(toc, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✓ Table of contents saved to: {output_path}")
    print(f"  Total pages: {toc['metadata']['total_pages']}")
    print(f"  Sections identified: {len(toc['sections'])}")
    print("\nSections found:")
    for section_id, data in sorted(toc["sections"].items(), key=lambda x: x[1]["start_page"]):
        start = data["start_page"]
        end = data.get("end_page", "?")
        print(f"  {section_id:20s}: pages {start:3d}-{end:3d}")


if __name__ == "__main__":
    main()
