"""Pin extract_spells output against the shipped SRD 5.1 PDF.

Parity gate for the v0.36.0 pdf_probe migration of
src/srd_builder/extract/datasets/extract_spells.py. The byte hash is
computed over the canonical JSON form of the full result (excluding
pdf_sha256 and extractor_version, which would otherwise rebaseline on
every PDF or release bump). If any spell entry, page assignment,
header block, or description block drifts, the test fails loudly.

Skips on container / CI builds where the source PDF isn't bundled.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"

EXPECTED_SHA256 = "70df0558ac16ddfd45fb9a8c09839c091e13ff8dc37b330becbe1c1cdd804d68"


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_extract_spells_srd_5_1_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_spells import (
        SPELL_END_PAGE,
        SPELL_START_PAGE,
        extract_spells,
    )

    result = extract_spells(SRD_5_1_PDF)

    assert sorted(result.keys()) == ["_meta", "spells"]
    assert len(result["spells"]) == 319

    meta = result["_meta"]
    assert meta["pdf_filename"] == "SRD_CC_v5.1.pdf"
    assert meta["spell_count"] == 319
    assert meta["pages_processed"] == SPELL_END_PAGE - SPELL_START_PAGE + 1
    assert meta["total_warnings"] == 0
    assert meta["extraction_warnings"] == []

    sample = result["spells"][0]
    assert set(sample.keys()) >= {
        "name",
        "page",
        "pages",
        "level_and_school",
        "header_blocks",
        "description_blocks",
    }
    assert sample["name"] == "Acid Arrow"
    assert SPELL_START_PAGE <= sample["page"] <= SPELL_END_PAGE

    # All spells live in the spell-descriptions chapter.
    for spell in result["spells"]:
        assert SPELL_START_PAGE <= spell["page"] <= SPELL_END_PAGE
        assert spell["name"]


def test_extract_spells_srd_5_1_byte_parity() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_spells import extract_spells

    result = extract_spells(SRD_5_1_PDF)
    stable = {k: v for k, v in result.items() if k != "_meta"}
    stable["_meta"] = {
        k: v for k, v in result["_meta"].items() if k not in {"pdf_sha256", "extractor_version"}
    }
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == EXPECTED_SHA256, (
        f"extract_spells output drifted; got {digest}, expected {EXPECTED_SHA256}"
    )
