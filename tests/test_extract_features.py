"""Pin extract_features output against the shipped SRD 5.1 PDF.

Parity gate for the v0.35.0 pdf_probe migration of
src/srd_builder/extract/datasets/extract_features.py. Two entry points
are wired through 'build.py' ('extract_class_features' over pages
8-55 and 'extract_lineage_traits' over pages 3-7), so this test pins
both with their own byte hashes. If any feature name, page assignment,
or text body drifts, the test fails loudly.

Skips on container / CI builds where the source PDF isn't bundled.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"

CLASS_FEATURES_SHA256 = "8b962f4aed4ddeb514a4fff5e8afbc325309e7cea02a10bfc386d9d200df5b9a"
LINEAGE_TRAITS_SHA256 = "5a912ceabb1fdc317709db2ca34df352ed1b24034fb381c254964bb15a533ba1"


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def _hash_canonical(result: dict) -> str:
    blob = json.dumps(result, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def test_extract_class_features_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_features import extract_class_features

    result = extract_class_features(SRD_5_1_PDF)

    assert sorted(result.keys()) == ["extraction_warnings", "features", "source_pages"]
    assert result["source_pages"] == "8-55"
    assert result["extraction_warnings"] == []
    assert len(result["features"]) == 155

    sample = result["features"][0]
    assert set(sample.keys()) == {"name", "page", "text"}
    assert sample["name"] == "Rage"
    assert 8 <= sample["page"] <= 55

    for feat in result["features"]:
        assert 8 <= feat["page"] <= 55
        assert feat["name"]
        assert feat["text"]


def test_extract_lineage_traits_shape() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_features import extract_lineage_traits

    result = extract_lineage_traits(SRD_5_1_PDF)

    assert sorted(result.keys()) == ["extraction_warnings", "features", "source_pages"]
    assert result["source_pages"] == "3-7"
    assert result["extraction_warnings"] == []
    assert len(result["features"]) == 102

    for feat in result["features"]:
        assert 3 <= feat["page"] <= 7
        assert feat["name"]


def test_extract_features_byte_parity() -> None:
    _require_pdf_and_fitz()
    from srd_builder.extract.datasets.extract_features import (
        extract_class_features,
        extract_lineage_traits,
    )

    cf_digest = _hash_canonical(extract_class_features(SRD_5_1_PDF))
    lt_digest = _hash_canonical(extract_lineage_traits(SRD_5_1_PDF))

    assert cf_digest == CLASS_FEATURES_SHA256, (
        f"extract_class_features drifted; got {cf_digest}, expected {CLASS_FEATURES_SHA256}"
    )
    assert lt_digest == LINEAGE_TRAITS_SHA256, (
        f"extract_lineage_traits drifted; got {lt_digest}, expected {LINEAGE_TRAITS_SHA256}"
    )
