"""Pin hand-curated facts against shipped dist/<ruleset>/*.json output.

This is a release-gate test: it asserts specific field values on
specific records (e.g., "Fireball is level 3", "Goblin AC is 15") so
silent parser drift fails loudly before a release ships.

It requires a built dist/srd_5_1/ tree. CI does not (and structurally
cannot) build, because the SRD PDF is not committed; the test skips
with a loud message in that environment. Run locally via:

    python -m srd_builder.build --ruleset srd_5_1
    pytest tests/test_known_truths.py -v

Or as part of the release gate (scripts/release_check.sh).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TRUTHS_FILE = REPO_ROOT / "tests" / "fixtures" / "known_truths.json"
DIST_BASE = REPO_ROOT / "dist"


def _load_truths() -> dict[str, Any]:
    return json.loads(TRUTHS_FILE.read_text(encoding="utf-8"))


def _dist_dir(ruleset: str) -> Path:
    return DIST_BASE / ruleset


def _truth_cases() -> list[tuple[str, str, str, dict[str, Any]]]:
    """Flatten the truths file into (ruleset, dataset, record_id, fields) tuples
    so pytest can parametrize one test per truth (failures name the specific
    record + dataset)."""
    truths = _load_truths()
    ruleset = truths["_meta"]["ruleset"]
    cases: list[tuple[str, str, str, dict[str, Any]]] = []
    for dataset, block in truths["datasets"].items():
        for truth in block["truths"]:
            cases.append((ruleset, dataset, truth["id"], truth["fields"]))
    return cases


def _container_key(ruleset: str, dataset: str) -> str:
    truths = _load_truths()
    return truths["datasets"][dataset]["container_key"]


def _dataset_present(ruleset: str) -> bool:
    return (_dist_dir(ruleset) / "ability_scores.json").exists()


@pytest.fixture(scope="module")
def dist_data() -> dict[str, dict[str, Any]]:
    """Load every shipped JSON file once per test module."""
    truths = _load_truths()
    ruleset = truths["_meta"]["ruleset"]
    if not _dataset_present(ruleset):
        pytest.skip(
            f"dist/{ruleset}/ not built — known_truths is a release-gate test, "
            "not a CI test. Run `python -m srd_builder.build --ruleset "
            f"{ruleset}` first (or invoke via scripts/release_check.sh)."
        )
    data: dict[str, dict[str, Any]] = {}
    for dataset in truths["datasets"]:
        path = _dist_dir(ruleset) / f"{dataset}.json"
        data[dataset] = json.loads(path.read_text(encoding="utf-8"))
    return data


@pytest.mark.parametrize(
    ("ruleset", "dataset", "record_id", "expected_fields"),
    _truth_cases(),
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_known_truth(
    ruleset: str,
    dataset: str,
    record_id: str,
    expected_fields: dict[str, Any],
    dist_data: dict[str, dict[str, Any]],
) -> None:
    doc = dist_data[dataset]
    container_key = _container_key(ruleset, dataset)
    items = doc.get(container_key, [])
    assert items, (
        f"{dataset}.json has no records under key {container_key!r} — "
        "extraction may have regressed to zero output."
    )
    matches = [it for it in items if it.get("id") == record_id]
    assert matches, (
        f"{dataset}: record id={record_id!r} not found in {len(items)} shipped "
        "records. Either the record was renamed/dropped or known_truths.json "
        "is stale."
    )
    assert len(matches) == 1, (
        f"{dataset}: record id={record_id!r} appears {len(matches)} times "
        "(expected exactly one). Indicates a duplicate id bug."
    )
    record = matches[0]
    mismatches: list[str] = []
    for field, expected in expected_fields.items():
        actual = record.get(field)
        if actual != expected:
            mismatches.append(f"  {field}: expected={expected!r}  actual={actual!r}")
    assert not mismatches, (
        f"{dataset} record id={record_id!r} drifted from known truths:\n" + "\n".join(mismatches)
    )
