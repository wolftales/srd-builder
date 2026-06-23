import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REPO_ROOT = Path(__file__).resolve().parents[1]
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"


@pytest.fixture(scope="session")
def srd_5_1_pdf() -> Path:
    """Path to the SRD 5.1 PDF, or skip the test if absent.

    The PDF is gitignored (and the CI workflow's first step actively
    forbids it being committed), so CI environments never have a local
    copy. Any test that exercises live PDF extraction must depend on
    this fixture so it skips cleanly in CI instead of erroring.
    """
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"SRD 5.1 PDF not available at {SRD_5_1_PDF}")
    return SRD_5_1_PDF


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
