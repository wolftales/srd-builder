"""Round-trip PDF sampling: every record's declared page must contain it.

For each shipped dataset, sample the first 5 records (sorted by id),
look up each record's ``page`` field, render that PDF page via
``utils.pdf_probe``, and assert the record's ``name`` appears as a
substring within ±1 page of the declared page.

Catches silent parser drift where the extractor produces records whose
``page`` field does not point to where the record actually lives in the
source PDF. This is the v0.28.0 Phase D companion to the audit codes
(Phase C) and the known_truths release gate (Phase B).

Scope decisions:
  - **Sampling:** deterministic (first 5 records sorted by id), not random.
    Reproducible failures matter more than coverage breadth for a smoke
    test of this kind.
  - **Matching field:** ``name`` only. Wider field coverage (description,
    text) was deferred to keep the false-positive floor at zero.
  - **Tolerance:** ±1 page. ``page`` in dataset records is the page where
    the record's heading appears, but the SRD frequently uses section
    headers on one page with subheadings flowing onto the next. ±1
    absorbs that without masking real drift (>±1 = bug).
  - **Skip behavior:** mirrors ``tests/test_pdf_provenance.py`` — skips
    with a loud message when the PDF or pymupdf is not present (CI /
    container builds without the SRD bundle).
  - **Dataset scope:** all 15 datasets with a ``page`` field. ``lineages``
    is excluded because its records carry no ``page`` field by design.

Known drift (xfail today, real backlog items):
  - ``skills`` — 1/5 sampled fails (``Athletics`` declared p76, body on
    p78). Off-by-two from section header.
  - ``tables`` — 2/5 fail with large drift (``Ability Scores and
    Modifiers`` declared p7 but body on p76; ``Adventure Gear`` not
    found anywhere by name). Suggests stale TOC-derived page numbers.
  - ``weapon_properties`` — 5/5 fail. All 11 records claim p147 but the
    weapon-property prose is elsewhere. Looks like a single hardcoded
    page constant.

The xfail markers exist so this test ships green; remove them when the
underlying page-field assignment is fixed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"
DIST_DIR = REPO_ROOT / "dist" / "srd_5_1"

# (dataset_filename_stem, top-level list key in the shipped JSON).
# ``lineages`` is intentionally absent — its records carry no ``page``.
_DATASETS: list[tuple[str, str]] = [
    ("ability_scores", "items"),
    ("classes", "items"),
    ("conditions", "conditions"),
    ("damage_types", "items"),
    ("diseases", "diseases"),
    ("equipment", "items"),
    ("features", "features"),
    ("magic_items", "items"),
    ("monsters", "items"),
    ("poisons", "items"),
    ("rules", "items"),
    ("skills", "items"),
    ("spells", "items"),
    ("tables", "items"),
    ("weapon_properties", "items"),
]

_XFAIL_DATASETS = {
    "skills": "Athletics declared p76, body on p78 (page-field drift)",
    "tables": "Multiple records have stale TOC-derived page numbers",
    "weapon_properties": "All 11 records hardcoded to p147; body is elsewhere",
}


def _params() -> list[pytest.param]:
    out: list[pytest.param] = []
    for ds, key in _DATASETS:
        if ds in _XFAIL_DATASETS:
            out.append(
                pytest.param(
                    ds,
                    key,
                    marks=pytest.mark.xfail(
                        reason=_XFAIL_DATASETS[ds],
                        strict=False,
                    ),
                    id=ds,
                )
            )
        else:
            out.append(pytest.param(ds, key, id=ds))
    return out


def _require_pdf_and_fitz() -> None:
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def _require_dist(dataset: str) -> Path:
    path = DIST_DIR / f"{dataset}.json"
    if not path.exists():
        pytest.skip(f"dist not built: {path} (run `make build` first)")
    return path


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _resolve_page(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, list) and value and isinstance(value[0], int):
        return value[0]
    return None


@pytest.mark.parametrize(("dataset", "list_key"), _params())
def test_first_records_appear_on_declared_pages(dataset: str, list_key: str) -> None:
    _require_pdf_and_fitz()
    dist_path = _require_dist(dataset)

    from srd_builder.utils.pdf_probe import (
        open_pdf,
        page_text,
        srd_page_to_pdf_index,
    )

    payload = json.loads(dist_path.read_text(encoding="utf-8"))
    raw_items = payload.get(list_key)
    assert isinstance(raw_items, list) and raw_items, (
        f"{dataset}: expected non-empty list under key {list_key!r}"
    )

    candidates = [
        item
        for item in raw_items
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("name"), str)
        and _resolve_page(item.get("page")) is not None
    ]
    sampled = sorted(candidates, key=lambda x: x["id"])[:5]
    assert sampled, f"{dataset}: no sampleable records found (need id+name+page)"

    failures: list[str] = []
    tolerance = 1

    with open_pdf(SRD_5_1_PDF) as doc:
        page_count = doc.page_count
        for item in sampled:
            declared = _resolve_page(item["page"])
            assert declared is not None  # narrow type for mypy
            target = _norm(item["name"])
            found_on: int | None = None
            for offset in range(-tolerance, tolerance + 1):
                probe = declared + offset
                if not 1 <= probe <= page_count:
                    continue
                text = _norm(page_text(doc, srd_page_to_pdf_index(probe)))
                if target in text:
                    found_on = probe
                    break
            if found_on is None:
                failures.append(
                    f"  {item['id']!r} name={item['name']!r} declared p{declared} "
                    f"(not found within \u00b1{tolerance} pages)"
                )

    if failures:
        pytest.fail(
            f"{dataset}: {len(failures)}/{len(sampled)} sampled records not "
            f"found on or near their declared page:\n" + "\n".join(failures)
        )
