import json
from pathlib import Path

from srd_builder.build import build


def test_build_writes_report_and_datasets(tmp_path: Path) -> None:
    out = tmp_path / "dist"
    path = build(ruleset="srd_5_1", output_format="json", out_dir=out)
    assert path.exists()
    assert path.name == "build_report.json"

    monsters_path = out / "srd_5_1" / "data" / "monsters.json"
    assert monsters_path.exists()
    document = json.loads(monsters_path.read_text(encoding="utf-8"))
    assert document["_meta"]["ruleset"] == "srd_5_1"
    assert document["items"] == []
