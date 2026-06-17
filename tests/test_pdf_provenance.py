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
