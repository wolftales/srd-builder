"""Pin extract_equipment output against the shipped SRD 5.1 PDF.

Parity gate for the v0.33.0 pdf_probe migration of
src/srd_builder/extract/datasets/extract_equipment.py. The byte hash
is computed over the canonical JSON form of the full result (excluding
extractor_version, which would otherwise rebaseline on every release
bump). If any equipment row, section category, page number, or bbox
drifts, this test fails loudly.

Skips on container / CI builds where the source PDF isn't bundled.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"

# Captured against pre-migration output (raw fitz.open()) and re-verified
# against post-migration output (pdf_probe.open_pdf).
EXPECTED_SHA256 = "b8108ce97b4937da83a9a8741f47720f3e1c31fb37df893706cecfaf7085ca5f"


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_extract_equipment_srd_5_1_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_equipment import (
        EQUIPMENT_END_PAGE,
        EQUIPMENT_START_PAGE,
        extract_equipment,
    )

    result = extract_equipment(SRD_5_1_PDF)

    assert sorted(result.keys()) == ["_meta", "equipment"]
    assert len(result["equipment"]) == 119

    meta = result["_meta"]
    assert meta["items_extracted"] == 119
    assert meta["warnings"] == []
    assert meta["pages_processed"] == list(range(EQUIPMENT_START_PAGE, EQUIPMENT_END_PAGE + 1))
    assert len(meta["pages_processed"]) == 13

    # Each item carries the table-row provenance the downstream parser needs.
    sample = result["equipment"][0]
    assert set(sample.keys()) >= {
        "page",
        "section",
        "table_row",
        "table_headers",
        "row_index",
        "bbox",
    }
    assert set(sample["section"].keys()) == {"category", "subcategory"}

    # Every item is anchored to an equipment-chapter page.
    for item in result["equipment"]:
        assert EQUIPMENT_START_PAGE <= item["page"] <= EQUIPMENT_END_PAGE
        assert item["section"]["category"] in {"armor", "weapon", "gear", "mount"}


def test_extract_equipment_srd_5_1_byte_parity() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_equipment import extract_equipment

    result = extract_equipment(SRD_5_1_PDF)
    stable = {k: v for k, v in result.items() if k != "_meta"}
    stable["_meta"] = {k: v for k, v in result["_meta"].items() if k != "extractor_version"}
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == EXPECTED_SHA256, (
        f"extract_equipment output drifted; got {digest}, expected {EXPECTED_SHA256}"
    )
