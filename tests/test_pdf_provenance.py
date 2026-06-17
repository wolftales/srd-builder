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

import re
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


def _normalized(text: str) -> str:
    """Collapse the SRD's tab+CR+nbsp word separators into single spaces."""
    text = re.sub(r"[\t\r\xa0]+", " ", text)
    return re.sub(r"\s+", " ", text)


def test_lineage_pages_are_extractable_after_whitespace_normalization() -> None:
    """SRD 5.1 lineage pages (3-7) ARE extractable, despite the claim in
    src/srd_builder/srd_5_1/lineage_targets.py that they are corrupted.

    The original "PDF text is corrupted" assertion (written years ago,
    likely against an older PyMuPDF) does not hold under pymupdf 1.27.x.
    The body text uses non-breaking spaces (U+00A0) and tab+CR sequences
    as word separators; once normalized, all lineage names and trait
    keywords are present.

    If this test starts FAILING (lineage names missing from a page),
    the PDF or PyMuPDF really has changed and a fresh investigation is
    needed. Either way, the manual LINEAGE_DATA override in
    lineage_targets.py is a strong candidate for retirement (see
    docs/PROVENANCE.md and docs/BACKLOG.md re-extraction candidates).
    """
    _require_pdf_and_fitz()
    import fitz

    doc = fitz.open(str(SRD_5_1_PDF))

    # Lineage keywords with the PDF index where each first appears under
    # normal text extraction. PDF indices are 0-based; SRD page = idx+1.
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

    missing: list[str] = []
    for keyword, pdf_idx in expected.items():
        text = _normalized(doc.load_page(pdf_idx).get_text("text"))
        if keyword not in text:
            missing.append(f"{keyword!r} expected on PDF index {pdf_idx}")

    assert not missing, (
        "Lineage keywords no longer extractable from expected pages — "
        "investigate before changing LINEAGE_DATA assumptions:\n  - " + "\n  - ".join(missing)
    )
