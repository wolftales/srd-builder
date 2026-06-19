import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _assert_golden_matches(rendered: str, expected_path: Path) -> None:
    """Compare a rendered JSON document against an on-disk golden fixture.

    Ignores `_meta.generated_by`, which is tied to the package version and is
    not a data-fidelity field. Version sync between fixtures and the package
    is verified separately by `test_version_consistency.py`.
    """
    rendered_doc = json.loads(rendered)
    expected_doc = json.loads(expected_path.read_text(encoding="utf-8"))
    if "_meta" in expected_doc and "_meta" in rendered_doc:
        expected_doc["_meta"]["generated_by"] = rendered_doc["_meta"].get("generated_by")
    assert rendered_doc == expected_doc


@pytest.fixture
def assert_golden_matches():
    return _assert_golden_matches
