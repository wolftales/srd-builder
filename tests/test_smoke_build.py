import json
from pathlib import Path

from srd_builder import __version__
from srd_builder.build import build
from srd_builder.utils.constants import SCHEMA_VERSION


def test_build_writes_report_and_datasets(tmp_path: Path) -> None:
    out = tmp_path / "dist"
    path = build(ruleset="srd_5_1", output_format="json", out_dir=out)
    assert path.exists()
    assert path.name == "build_report.json"

    # Validate build_report structure
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["ruleset"] == "srd_5_1"
    assert report["output_format"] == "json"
    assert report["builder_version"] == __version__, (
        f"build_report.json has builder_version={report['builder_version']}, "
        f"but __version__ is {__version__}. These must match!"
    )
    assert report["schema_version"] == SCHEMA_VERSION
    assert "python_version" in report
    assert "timestamp_utc" in report

    monsters_path = out / "srd_5_1" / "monsters.json"
    assert monsters_path.exists()
    document = json.loads(monsters_path.read_text(encoding="utf-8"))
    assert document["_meta"]["ruleset_version"] == "5.1"
    assert document["_meta"]["source"] == "SRD_CC_v5.1"
    # With fixture data present, we should have processed monsters
    assert "items" in document
    assert isinstance(document["items"], list)
