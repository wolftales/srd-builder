"""Pin extract_magic_items output against the shipped SRD 5.1 PDF.

Parity gate for the v0.34.0 pdf_probe migration of
src/srd_builder/extract/datasets/extract_magic_items.py. The byte hash
is computed over the canonical JSON form of the full result (excluding
pdf_sha256 and extractor_version, which would otherwise rebaseline on
every PDF or release bump). If any item, page assignment, or
description/metadata block drifts, this test fails loudly.

Skips on container / CI builds where the source PDF isn't bundled.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"

EXPECTED_SHA256 = "06c55a3f9c01a1cc50e76a9867e58f9f888cdcbb81497d8dd0247ac87f77fde4"


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_extract_magic_items_srd_5_1_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_magic_items import (
        MAGIC_ITEMS_END_PAGE,
        MAGIC_ITEMS_START_PAGE,
        extract_magic_items,
    )

    result = extract_magic_items(SRD_5_1_PDF)

    assert sorted(result.keys()) == ["_meta", "items"]
    assert len(result["items"]) == 245

    meta = result["_meta"]
    assert meta["pdf_filename"] == "SRD_CC_v5.1.pdf"
    assert meta["item_count"] == 245
    assert meta["pages_processed"] == MAGIC_ITEMS_END_PAGE - MAGIC_ITEMS_START_PAGE + 1
    assert meta["total_warnings"] == 0
    assert meta["extraction_warnings"] == []

    sample = result["items"][0]
    assert set(sample.keys()) >= {"name", "page", "description_blocks", "metadata_blocks"}
    assert sample["name"] == "Adamantine Armor"
    assert MAGIC_ITEMS_START_PAGE <= sample["page"] <= MAGIC_ITEMS_END_PAGE

    # All items live in the magic-items chapter.
    for item in result["items"]:
        assert MAGIC_ITEMS_START_PAGE <= item["page"] <= MAGIC_ITEMS_END_PAGE
        assert item["name"]


def test_extract_magic_items_srd_5_1_byte_parity() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_magic_items import extract_magic_items

    result = extract_magic_items(SRD_5_1_PDF)
    stable = {k: v for k, v in result.items() if k != "_meta"}
    stable["_meta"] = {
        k: v for k, v in result["_meta"].items() if k not in {"pdf_sha256", "extractor_version"}
    }
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == EXPECTED_SHA256, (
        f"extract_magic_items output drifted; got {digest}, expected {EXPECTED_SHA256}"
    )
