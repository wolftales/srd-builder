import hashlib
import json

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

    pdf_path = raw_dir / "srd.pdf"
    pdf_path.write_bytes(b"placeholder pdf data")

    monkeypatch.chdir(tmp_path)

    out_dir = tmp_path / "dist"
    report_path = build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert report_path.exists()

    dist_ruleset_dir = out_dir / ruleset
    assert dist_ruleset_dir.exists()
    assert (dist_ruleset_dir / "data").is_dir()

    assert raw_dir.is_dir()
    assert (raw_dir / "extracted").is_dir()

    meta_path = raw_dir / "meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    assert meta["pdf_sha256"] == expected_hash

    first_meta_bytes = meta_path.read_bytes()
    build(ruleset=ruleset, output_format="json", out_dir=out_dir)
    assert first_meta_bytes == meta_path.read_bytes()

    monkeypatch.setattr(validate_module, "DIST_DIR", out_dir)
    monkeypatch.setattr(validate_module, "RULESETS_DIR", rulesets_root)
    validate_module.validate_ruleset(ruleset)
