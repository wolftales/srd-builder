import hashlib
import json
from pathlib import Path

import jsonschema

from srd_builder.build import build


def test_build_pipeline(tmp_path, monkeypatch):
    class _DummyValidator:
        def __init__(self, _schema):
            pass

        def validate(self, _instance):
            return None

    monkeypatch.setattr(jsonschema, "Draft202012Validator", _DummyValidator)

    from srd_builder import validate as validate_module

    ruleset = "srd_5_1"
    rulesets_root = tmp_path / "rulesets"
    raw_dir = rulesets_root / ruleset / "raw"
    raw_dir.mkdir(parents=True)

    fixture_raw = Path("tests/fixtures/srd_5_1/raw/monsters.json")
    raw_dir.joinpath("monsters.json").write_text(
        fixture_raw.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    pdf_path = raw_dir / "srd.pdf"
    pdf_path.write_bytes(b"placeholder pdf data")

    monkeypatch.chdir(tmp_path)

    out_dir = tmp_path / "dist"
    report_path = build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert report_path.exists()

    dist_ruleset_dir = out_dir / ruleset
    assert dist_ruleset_dir.exists()
    data_dir = dist_ruleset_dir / "data"
    assert data_dir.is_dir()

    assert raw_dir.is_dir()
    assert (raw_dir / "extracted").is_dir()

    meta_path = raw_dir / "meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    assert meta["pdf_sha256"] == expected_hash

    monsters_path = data_dir / "monsters.json"
    index_path = data_dir / "index.json"
    assert monsters_path.exists()
    assert index_path.exists()

    monsters_doc = json.loads(monsters_path.read_text(encoding="utf-8"))
    assert monsters_doc["_meta"] == {
        "ruleset": ruleset,
        "schema_version": "1.1.0",
        "source": "SRD_CC_v5.1",
        "build_report": "../build_report.json",
        "generated_by": monsters_doc["_meta"]["generated_by"],
    }
    assert monsters_doc["_meta"]["generated_by"].startswith("srd-builder v")
    assert len(monsters_doc["items"]) > 0

    index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_doc["_meta"]["ruleset"] == ruleset
    assert "conflicts" not in index_doc or index_doc["conflicts"]

    first_meta_bytes = meta_path.read_bytes()
    monsters_bytes = monsters_path.read_bytes()
    index_bytes = index_path.read_bytes()
    build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert first_meta_bytes == meta_path.read_bytes()
    assert monsters_bytes == monsters_path.read_bytes()
    assert index_bytes == index_path.read_bytes()

    monkeypatch.setattr(validate_module, "DIST_DIR", out_dir)
    monkeypatch.setattr(validate_module, "RULESETS_DIR", rulesets_root)
    validate_module.validate_ruleset(ruleset)
