"""Pin extract_pdf_metadata output against the shipped SRD 5.1 PDF.

Parity gate for the v0.31.0 pdf_probe migration of
src/srd_builder/extract/datasets/extract_pdf_metadata.py. Skips on
container / CI builds where the source PDF isn't bundled.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_extract_pdf_metadata_srd_5_1() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_pdf_metadata import (
        extract_pdf_metadata,
    )

    meta = extract_pdf_metadata(SRD_5_1_PDF)

    assert meta["title"] == "System Reference Document 5.1"
    assert meta["version"] == "5.1"
    assert meta["license_type"] == "CC-BY-4.0"
    assert meta["license_url"] == "https://creativecommons.org/licenses/by/4.0/legalcode"
    assert meta["official_url"] == "https://dnd.wizards.com/resources/systems-reference-document"
    assert meta["filename"] == "SRD_CC_v5.1.pdf"

    attribution = meta["attribution"]
    assert attribution is not None
    assert attribution.startswith("This work includes material taken from")
    assert attribution.endswith("/licenses/by/4.0/legalcode.")
    assert "Wizards of the Coast LLC" in attribution
    # Curly quotes preserved (the SRD page-1 text uses them around "SRD 5.1").
    assert "\u201cSRD 5.1\u201d" in attribution

    # XMP fields: the shipped SRD PDF has no embedded XMP metadata, so every
    # property is an empty string. Pinning the contract so downstream callers
    # can rely on the keys being present regardless of source.
    for key in (
        "pdf_title",
        "pdf_author",
        "pdf_subject",
        "pdf_creator",
        "pdf_producer",
        "pdf_creation_date",
        "pdf_mod_date",
    ):
        assert meta[key] == "", f"expected {key} empty, got {meta[key]!r}"
