from pathlib import Path

from srd_builder.build import build


def test_build_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "dist"
    path = build(ruleset="srd_5_1", output_format="json", out_dir=out)
    assert path.exists()
    assert path.name == "build_report.json"
