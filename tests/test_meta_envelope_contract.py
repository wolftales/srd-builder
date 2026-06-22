"""Envelope contract tests.

Freezes the consumer-visible shape of the bundle envelope so renames
like ``files`` → ``inventory`` → ``datasets`` cannot ship silently. Any
such change is a MAJOR ``builder_version`` bump and must update
``schemas/meta.schema.json``. See docs/COMPATIBILITY.md.

Validates two files:

* ``dist/srd_5_1/meta.json`` against ``schemas/meta.schema.json``
* ``dist/build_report.json`` against ``schemas/build_report.schema.json``
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Draft202012Validator = None

META_DATA = Path("dist/srd_5_1/meta.json")
META_SCHEMA = Path("schemas/meta.schema.json")
BUILD_REPORT_DATA = Path("dist/build_report.json")
BUILD_REPORT_SCHEMA = Path("schemas/build_report.schema.json")


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not installed")
@pytest.mark.skipif(not META_DATA.exists(), reason="No built bundle present")
def test_meta_json_envelope_contract() -> None:
    schema = json.loads(META_SCHEMA.read_text(encoding="utf-8"))
    document = json.loads(META_DATA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    if errors:
        msg_lines = [f"{e.json_path}: {e.message}" for e in errors]
        pytest.fail("meta.json violates envelope contract:\n  - " + "\n  - ".join(msg_lines))


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not installed")
@pytest.mark.skipif(not BUILD_REPORT_DATA.exists(), reason="No build_report.json present")
def test_build_report_envelope_contract() -> None:
    schema = json.loads(BUILD_REPORT_SCHEMA.read_text(encoding="utf-8"))
    document = json.loads(BUILD_REPORT_DATA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    if errors:
        msg_lines = [f"{e.json_path}: {e.message}" for e in errors]
        pytest.fail(
            "build_report.json violates envelope contract:\n  - " + "\n  - ".join(msg_lines)
        )


@pytest.mark.skipif(not BUILD_REPORT_DATA.exists(), reason="No build_report.json present")
def test_build_report_lives_outside_bundle() -> None:
    """The bundle directory must contain no build_report.json (timestamp
    field would break determinism). The report belongs one level up."""
    in_bundle = META_DATA.parent / "build_report.json"
    assert not in_bundle.exists(), (
        f"build_report.json found inside the bundle at {in_bundle}; "
        "it must live alongside the bundle directory (dist/build_report.json) "
        "so the bundle stays byte-deterministic."
    )


@pytest.mark.skipif(not META_DATA.exists(), reason="No built bundle present")
def test_meta_datasets_manifest_keyname_frozen() -> None:
    """Guards specifically against the manifest rename that motivated this
    contract: 'files' (early) → 'inventory' (mid) → 'datasets' (current)."""
    document = json.loads(META_DATA.read_text(encoding="utf-8"))
    assert "datasets" in document, "meta.json must carry the dataset manifest under 'datasets'."
    assert "files" not in document, "Legacy 'files' manifest key must not be reintroduced."
    assert "inventory" not in document, "Legacy 'inventory' manifest key must not be reintroduced."


@pytest.mark.skipif(not META_DATA.exists(), reason="No built bundle present")
def test_meta_pdf_hash_is_raw_hex() -> None:
    """The pdf_hash representation is normalized to raw hex across the
    whole envelope so a single regex matches both meta.json.build.pdf_hash
    and every dataset's _meta.pdf_sha256."""
    document = json.loads(META_DATA.read_text(encoding="utf-8"))
    pdf_hash = document.get("build", {}).get("pdf_hash")
    if pdf_hash is None:
        pytest.skip("No pdf_hash present in this bundle")
    assert isinstance(pdf_hash, str)
    assert not pdf_hash.startswith("sha256:"), (
        f"pdf_hash uses legacy 'sha256:<hex>' prefix form: {pdf_hash!r}. "
        "Use raw hex to match dataset _meta.pdf_sha256."
    )
    assert len(pdf_hash) == 64, f"Expected 64-char hex sha256, got len={len(pdf_hash)}."
    assert all(c in "0123456789abcdef" for c in pdf_hash), (
        f"pdf_hash must be lowercase hex: {pdf_hash!r}"
    )
