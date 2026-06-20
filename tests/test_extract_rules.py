"""Pin extract_rules output against the shipped SRD 5.1 PDF.

Parity gate for the v0.32.0 pdf_probe migration of
src/srd_builder/extract/datasets/extract_rules.py. The byte hash is
computed over the canonical JSON form of the full result; if any block
text, font metadata, bbox, or section count drifts, this test fails
loudly.

Skips on container / CI builds where the source PDF isn't bundled.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"

# Captured against pre-migration output (raw fitz.open() + page.get_text("dict"))
# and re-verified against post-migration output (pdf_probe.open_pdf + page_dict).
EXPECTED_SHA256 = "d4b325bf08b231820bc0f8283e80546dd06620860fad182aa883420ef1336128"


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_extract_rules_srd_5_1_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_rules import (
        RULES_SECTIONS,
        extract_rules,
    )

    result = extract_rules(SRD_5_1_PDF)

    assert sorted(result.keys()) == ["_meta", "sections", "text_blocks"]
    assert len(result["text_blocks"]) == 3086
    assert len(result["sections"]) == len(RULES_SECTIONS) == 7

    meta = result["_meta"]
    assert meta["pdf_filename"] == "SRD_CC_v5.1.pdf"
    assert meta["sections_processed"] == 7
    assert meta["pages_processed"] == 30
    assert meta["total_blocks"] == 3086
    assert meta["total_warnings"] == 0
    assert meta["warnings"] == []

    # Section names + page ranges come from PAGE_INDEX; pin them so a
    # PAGE_INDEX edit can't silently shift rule extraction.
    section_names = [s["name"] for s in result["sections"]]
    assert section_names == RULES_SECTIONS

    first = result["sections"][0]
    assert first["name"] == "using_ability_scores"
    assert first["pages"] == {"start": 76, "end": 83}
    assert first["block_count"] > 0


def test_extract_rules_srd_5_1_byte_parity() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_rules import extract_rules

    result = extract_rules(SRD_5_1_PDF)
    # Drop pdf_sha256 / extractor_version so the hash tracks extraction
    # behaviour, not PDF or version-string bytes.
    stable = {k: v for k, v in result.items() if k != "_meta"}
    stable["_meta"] = {
        k: v for k, v in result["_meta"].items() if k not in {"pdf_sha256", "extractor_version"}
    }
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == EXPECTED_SHA256, (
        f"extract_rules output drifted; got {digest}, expected {EXPECTED_SHA256}"
    )


def test_extract_rules_text_block_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_rules import extract_rules

    result = extract_rules(SRD_5_1_PDF)
    block = result["text_blocks"][0]

    expected_keys = {
        "text",
        "page",
        "font_name",
        "font_size",
        "font_flags",
        "is_bold",
        "is_italic",
        "bbox",
        "block_idx",
        "line_idx",
        "span_idx",
    }
    assert set(block.keys()) == expected_keys
    assert set(block["bbox"].keys()) == {"x0", "y0", "x1", "y1"}
    # First block lands on page 76 (start of using_ability_scores chapter).
    assert block["page"] == 76
