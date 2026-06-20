"""Pin extract_monsters output against the shipped SRD 5.1 PDF.

Parity gate for the v0.37.0 pdf_probe migration of
src/srd_builder/extract/datasets/extract_monsters.py. The byte hash is
computed over the canonical JSON form of the full result (excluding
pdf_sha256 and extractor_version, which would otherwise rebaseline on
every PDF or release bump). If any monster entry, page assignment,
block, or marker drifts, the test fails loudly.

Skips on container / CI builds where the source PDF isn't bundled.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"

EXPECTED_SHA256 = "fd89da5624ba82bb8019c052cd80a4ddb997453c570c4870d588b0b000b9380d"


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_extract_monsters_srd_5_1_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_monsters import (
        ExtractionConfig,
        extract_monsters,
    )

    config = ExtractionConfig()
    result = extract_monsters(SRD_5_1_PDF)

    assert sorted(result.keys()) == ["_meta", "monsters"]
    assert len(result["monsters"]) == 317

    meta = result["_meta"]
    assert meta["pdf_filename"] == "SRD_CC_v5.1.pdf"
    assert meta["monster_count"] == 317
    assert meta["pages_processed"] == config.page_end - config.page_start + 1
    assert meta["total_warnings"] == 0
    assert meta["extraction_warnings"] == []

    sample = result["monsters"][0]
    assert set(sample.keys()) >= {"name", "pages", "blocks", "markers", "warnings"}
    assert sample["name"] == "Aboleth"
    assert all(config.page_start <= p <= config.page_end for p in sample["pages"])

    # All monsters live in the monsters chapter.
    for monster in result["monsters"]:
        assert monster["name"]
        assert monster["pages"]
        for page in monster["pages"]:
            assert config.page_start <= page <= config.page_end


def test_extract_monsters_srd_5_1_byte_parity() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_monsters import extract_monsters

    result = extract_monsters(SRD_5_1_PDF)
    stable = {k: v for k, v in result.items() if k != "_meta"}
    stable["_meta"] = {
        k: v for k, v in result["_meta"].items() if k not in {"pdf_sha256", "extractor_version"}
    }
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == EXPECTED_SHA256, (
        f"extract_monsters output drifted; got {digest}, expected {EXPECTED_SHA256}"
    )
