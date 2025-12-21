import hashlib
import json
from pathlib import Path

import jsonschema

from srd_builder.build import build
from srd_builder.constants import EXTRACTOR_VERSION, SCHEMA_VERSION


def test_build_pipeline(tmp_path, monkeypatch):
    class _DummyValidator:
        def __init__(self, _schema):
            pass

        def validate(self, _instance):
            return None

    monkeypatch.setattr(jsonschema, "Draft202012Validator", _DummyValidator)

    from srd_builder.utils import validate as validate_module

    ruleset = "srd_5_1"
    rulesets_root = tmp_path / "rulesets"
    raw_dir = rulesets_root / ruleset / "raw"
    raw_dir.mkdir(parents=True)

    fixture_raw = Path("tests/fixtures/srd_5_1/raw/monsters.json")
    fixture_data = json.loads(fixture_raw.read_text(encoding="utf-8"))

    raw_dir.joinpath("monsters.json").write_text(
        json.dumps(fixture_data, indent=2),
        encoding="utf-8",
    )

    # Create a mock PDF (any .pdf name works)
    pdf_path = raw_dir / "test_srd.pdf"
    pdf_path.write_bytes(b"placeholder pdf data")

    # Mock extract_monsters to avoid PDF parsing issues with fake PDF
    from srd_builder import build as build_module

    def mock_extract_monsters(_pdf_path):
        # Return structure matching extract_monsters output
        # fixture_data is a list of monsters, but extract_monsters returns dict with metadata
        return {
            "monsters": fixture_data,  # The fixture is already a list
            "_meta": {
                "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                "extractor_version": EXTRACTOR_VERSION,
                "pages_processed": 134,
                "monster_count": len(fixture_data),
                "total_warnings": 0,
                "extraction_warnings": [],
            },
        }

    monkeypatch.setattr(build_module, "extract_monsters", mock_extract_monsters)

    monkeypatch.chdir(tmp_path)

    out_dir = tmp_path / "dist"
    report_path = build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert report_path.exists()

    dist_ruleset_dir = out_dir / ruleset
    assert dist_ruleset_dir.exists()

    assert raw_dir.is_dir()

    # Check pdf_meta.json (input validation file)
    pdf_meta_path = raw_dir / "pdf_meta.json"
    assert pdf_meta_path.exists()
    pdf_meta = json.loads(pdf_meta_path.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    assert pdf_meta["pdf_sha256"] == expected_hash

    # Check meta.json at package root (rich consumer metadata)
    dist_meta_path = dist_ruleset_dir / "meta.json"
    assert dist_meta_path.exists()
    dist_meta = json.loads(dist_meta_path.read_text(encoding="utf-8"))
    assert dist_meta["ruleset_version"] == "5.1"
    assert dist_meta["source"] == "SRD_CC_v5.1"
    assert "license" in dist_meta
    assert "page_index" in dist_meta
    assert "files" in dist_meta
    assert "extraction_status" in dist_meta

    # Check data files at package root (flat structure)
    monsters_path = dist_ruleset_dir / "monsters.json"
    index_path = dist_ruleset_dir / "index.json"
    assert monsters_path.exists()
    assert index_path.exists()

    monsters_doc = json.loads(monsters_path.read_text(encoding="utf-8"))
    assert monsters_doc["_meta"] == {
        "source": "SRD_CC_v5.1",
        "ruleset_version": "5.1",
        "schema_version": SCHEMA_VERSION,
        "generated_by": monsters_doc["_meta"]["generated_by"],
        "build_report": "./build_report.json",
    }
    assert monsters_doc["_meta"]["generated_by"].startswith("srd-builder v")
    assert len(monsters_doc["items"]) > 0

    index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_doc["_meta"]["ruleset_version"] == "5.1"
    assert "conflicts" not in index_doc or index_doc["conflicts"]

    # Check determinism: rebuilding should produce identical output (meta.json is now stable)
    first_pdf_meta_bytes = pdf_meta_path.read_bytes()
    meta_bytes = dist_meta_path.read_bytes()
    monsters_bytes = monsters_path.read_bytes()
    index_bytes = index_path.read_bytes()
    build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert first_pdf_meta_bytes == pdf_meta_path.read_bytes()
    assert meta_bytes == dist_meta_path.read_bytes()
    assert monsters_bytes == monsters_path.read_bytes()
    assert index_bytes == index_path.read_bytes()

    monkeypatch.setattr(validate_module, "DIST_DIR", out_dir)
    monkeypatch.setattr(validate_module, "RULESETS_DIR", rulesets_root)
    validate_module.validate_ruleset(ruleset)
