"""Reproducer tests for provenance claims in docs/PROVENANCE.md.

Each test pins a specific assertion about what PDF extraction yields
*today* for a region we currently override with hand-curated data. The
tests are not regression guards — they are *truth probes*. When one
fails, our understanding of the source has shifted and the matching
manual override should be reassessed.

Tests skip gracefully when the source PDF is not present (CI / container
builds without the SRD bundle).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"


def _require_pdf_and_fitz():
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_lineage_pages_are_extractable_after_whitespace_normalization() -> None:
    """SRD 5.1 lineage pages ARE extractable, despite the claim in
    src/srd_builder/srd_5_1/lineage_targets.py that they are corrupted.

    The original "PDF text is corrupted" assertion (written years ago,
    likely against an older PyMuPDF) does not hold under pymupdf 1.27.x.
    The body text uses non-breaking spaces (U+00A0) and tab+CR sequences
    as word separators; once normalized via utils.pdf_probe, all lineage
    names and trait keywords are present.

    If this test starts FAILING (lineage names missing from a page),
    the PDF or PyMuPDF really has changed and a fresh investigation is
    needed. Either way, the manual LINEAGE_DATA override in
    lineage_targets.py is a strong candidate for retirement (see
    docs/PROVENANCE.md).
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.page_index import PAGE_INDEX
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        page_text,
        srd_page_to_pdf_index,
    )

    page_range = PAGE_INDEX["lineages"]["pages"]
    pdf_start = srd_page_to_pdf_index(page_range["start"])
    pdf_end = srd_page_to_pdf_index(page_range["end"])

    expected = {
        "Dwarf": 2,
        "Hill Dwarf": 3,
        "High Elf": 3,
        "Halfling": 4,
        "Lightfoot": 4,
        "Dragonborn": 4,
        "Gnome": 5,
        "Half-Elf": 5,
        "Half-Orc": 6,
        "Tiefling": 6,
    }

    for keyword, idx in expected.items():
        assert pdf_start <= idx <= pdf_end, (
            f"Test fixture out of sync with PAGE_INDEX: "
            f"{keyword!r} at PDF index {idx} not within "
            f"[{pdf_start}, {pdf_end}]"
        )

    missing: list[str] = []
    with open_pdf(SRD_5_1_PDF) as doc:
        for keyword, pdf_idx in expected.items():
            text = page_text(doc, pdf_idx)
            if keyword not in text:
                missing.append(f"{keyword!r} expected on PDF index {pdf_idx}")

    assert not missing, (
        "Lineage keywords no longer extractable from expected pages — "
        "investigate before changing LINEAGE_DATA assumptions:\n  - " + "\n  - ".join(missing)
    )


def test_spell_lists_pages_class_headers_are_extractable() -> None:
    """SRD 5.1 spell-list pages (105–113) ARE extractable, despite the
    claim in src/srd_builder/srd_5_1/spell_class_targets.py that the
    text is corrupted.

    spell_class_targets.py is the largest hand-curated surface in the
    project (~888 lines, 8 class spell lists, wired into every spell
    record via postprocess/spells.py). The "PDF text is corrupted;
    manually mapped via visual inspection" rationale is the same era
    and same author as the lineage claim that has already been disproved.

    This probe asserts that (a) all 8 class section headers and (b) a
    sampling of well-known spells appear in pages 105–113 after the
    standard whitespace normalization. If they do, SPELL_CLASSES is a
    retirement candidate; v0.27.0 should plan a real
    extract_spell_classes.py on top of utils.pdf_probe.
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.page_index import PAGE_INDEX
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        pages_text,
        srd_page_to_pdf_index,
    )

    page_range = PAGE_INDEX["spell_lists"]["pages"]
    pdf_start = srd_page_to_pdf_index(page_range["start"])
    pdf_end = srd_page_to_pdf_index(page_range["end"])
    pdf_indices = range(pdf_start, pdf_end + 1)

    expected_headers = [
        "Bard Spells",
        "Cleric Spells",
        "Druid Spells",
        "Paladin Spells",
        "Ranger Spells",
        "Sorcerer Spells",
        "Warlock Spells",
        "Wizard Spells",
    ]

    expected_spells = [
        "Vicious Mockery",
        "Sacred Flame",
        "Druidcraft",
        "Eldritch Blast",
        "Fire Bolt",
    ]

    with open_pdf(SRD_5_1_PDF) as doc:
        all_text = "\n".join(pages_text(doc, pdf_indices).values())

    missing_headers = [h for h in expected_headers if h not in all_text]
    missing_spells = [s for s in expected_spells if s not in all_text]

    assert not missing_headers, (
        "Spell-list class headers not found in pages "
        f"{page_range['start']}–{page_range['end']} after whitespace "
        "normalization:\n  - " + "\n  - ".join(missing_headers)
    )
    assert not missing_spells, (
        "Well-known spell names not found in pages "
        f"{page_range['start']}–{page_range['end']} after whitespace "
        "normalization (body text may genuinely be unreadable):\n  - "
        + "\n  - ".join(missing_spells)
    )


def test_class_pages_are_extractable_after_whitespace_normalization() -> None:
    """SRD 5.1 class pages (8–55) ARE extractable, despite the claim in
    src/srd_builder/rulesets/srd_5_1/class_targets.py that the data was
    "manually transcribed via visual inspection."

    class_targets.py is the third-largest hand-curated surface in the
    project (~763 lines, all 12 classes with hit_die, proficiencies,
    feature lists, subclasses, and 20-level progression). Like
    lineage_targets.py (retired in v0.27.0 P1) and spell_class_targets.py
    (retired in v0.27.0 P2), the "manual transcription" rationale is
    the same era and same author as the lineage/spell-class claims
    already disproved.

    This probe asserts that (a) all 12 class names, (b) a sampling of
    well-known features, and (c) common section headers appear in
    pages 8–55 after the standard whitespace normalization. If they
    do, CLASS_DATA is a retirement candidate; a future release should
    plan a real extract_classes.py on top of utils.pdf_probe + the
    font-fingerprint walk pattern used by extract_lineages.py and
    extract_spell_classes.py. The full structural payload (proficiencies
    dict, feature IDs, level progression) is significantly richer than
    a flat spell list, so a retirement will need a larger extractor —
    the point of this probe is only to confirm the *text* is present.
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.page_index import PAGE_INDEX
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        pages_text,
        srd_page_to_pdf_index,
    )

    page_range = PAGE_INDEX["classes"]["pages"]
    pdf_start = srd_page_to_pdf_index(page_range["start"])
    pdf_end = srd_page_to_pdf_index(page_range["end"])
    pdf_indices = range(pdf_start, pdf_end + 1)

    expected_class_names = [
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
    ]
    expected_features = [
        "Rage",
        "Unarmored Defense",
        "Spellcasting",
        "Sneak Attack",
        "Action Surge",
        "Wild Shape",
        "Lay on Hands",
        "Divine Sense",
        "Favored Enemy",
        "Cunning Action",
        "Sorcerous Origin",
        "Pact Magic",
        "Arcane Recovery",
        "Bardic Inspiration",
        "Channel Divinity",
    ]
    expected_sections = [
        "Hit Points",
        "Proficiencies",
        "Equipment",
        "Primal Path",
        "Bard College",
        "Divine Domain",
    ]

    with open_pdf(SRD_5_1_PDF) as doc:
        all_text = "\n".join(pages_text(doc, pdf_indices).values())

    missing_classes = [c for c in expected_class_names if c not in all_text]
    missing_features = [f for f in expected_features if f not in all_text]
    missing_sections = [s for s in expected_sections if s not in all_text]

    assert not missing_classes, (
        f"Class names not found in pages {page_range['start']}–"
        f"{page_range['end']} after whitespace normalization:\n  - "
        + "\n  - ".join(missing_classes)
    )
    assert not missing_features, (
        f"Well-known class features not found in pages {page_range['start']}–"
        f"{page_range['end']} after whitespace normalization "
        "(body text may genuinely be unreadable):\n  - " + "\n  - ".join(missing_features)
    )
    assert not missing_sections, (
        f"Class section headers not found in pages {page_range['start']}–"
        f"{page_range['end']} after whitespace normalization:\n  - "
        + "\n  - ".join(missing_sections)
    )


def test_poison_pages_are_extractable_after_whitespace_normalization() -> None:
    """SRD 5.1 poison pages (204–205) ARE extractable, despite the
    "corrupted text on pages 204-205" claim in
    src/srd_builder/rulesets/srd_5_1/poison_descriptions.py.

    Fourth hand-curated "PDF corruption" claim in the codebase, fourth
    one to fail under reproducer scrutiny. Same era, same author as
    lineage_targets (retired v0.27.0 P1), spell_class_targets
    (retired v0.27.0 P2), and class_targets (DISPUTED v0.27.0 P3).

    This probe asserts that (a) all 14 SRD poison names, (b) the
    standard mechanic keywords (DC numbers, "Constitution saving
    throw", duration phrases), and (c) the opening section title
    "Poisons" appear in pages 204–205 after the standard whitespace
    normalization. They do — every one.

    **However, retirement is NOT a straight cutover.** The live
    `parse_poison_description_records` pipeline already exists and runs,
    but the upstream prose section-splitter has bugs:

    - The "assassin's blood" entry is dropped entirely (the fancy
      apostrophe U+2019 in the heading appears to defeat the section
      detector).
    - The `malice` description absorbs ~2000 extra characters from
      neighboring sections.
    - The `torpor` description absorbs ~3700 extra characters.

    Until the section splitter is fixed, the hand-curated
    POISON_DESCRIPTIONS map remains correct behavior. PROVENANCE marks
    the entry **DISPUTED** with this test as the truth probe; retirement
    is gated on fixing the section splitter, not on PDF readability.
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        pages_text,
        srd_page_to_pdf_index,
    )

    pdf_start = srd_page_to_pdf_index(204)
    pdf_end = srd_page_to_pdf_index(205)
    pdf_indices = range(pdf_start, pdf_end + 1)

    expected_poison_names = [
        "Assassin",  # 'Assassin's Blood' — fancy apostrophe in PDF
        "Burnt Othur Fumes",
        "Crawler Mucus",
        "Drow Poison",
        "Essence of Ether",
        "Malice",
        "Midnight Tears",
        "Oil of Taggit",
        "Pale Tincture",
        "Purple Worm Poison",
        "Serpent Venom",
        "Torpor",
        "Truth Serum",
        "Wyvern Poison",
    ]
    expected_mechanics = [
        "DC 10",
        "DC 13",
        "DC 15",
        "DC 17",
        "DC 19",
        "Constitution saving throw",
        "poison damage",
        "1 minute",
        "1 hour",
        "24 hours",
    ]
    expected_sections = ["Poisons"]

    with open_pdf(SRD_5_1_PDF) as doc:
        all_text = "\n".join(pages_text(doc, pdf_indices).values())

    missing_poisons = [p for p in expected_poison_names if p not in all_text]
    missing_mechanics = [m for m in expected_mechanics if m not in all_text]
    missing_sections = [s for s in expected_sections if s not in all_text]

    assert not missing_poisons, (
        "Poison names not found in pages 204–205 after whitespace "
        "normalization:\n  - " + "\n  - ".join(missing_poisons)
    )
    assert not missing_mechanics, (
        "Poison mechanics keywords not found in pages 204–205 after "
        "whitespace normalization (body text may genuinely be "
        "unreadable):\n  - " + "\n  - ".join(missing_mechanics)
    )
    assert not missing_sections, (
        "Poison section header not found in pages 204–205 after "
        "whitespace normalization:\n  - " + "\n  - ".join(missing_sections)
    )
