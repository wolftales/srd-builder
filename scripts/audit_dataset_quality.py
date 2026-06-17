#!/usr/bin/env python3
"""Data quality audit for built srd-builder distributions.

Phase Z of the v0.24.0 quality-gate effort. Runs structural checks on every
shipped dataset under ``dist/<ruleset>/`` and emits a machine-readable JSON
report plus a human-friendly summary. Intended to be wired into ``make smoke``
and CI after Phases A-C land the matching extractor fixes.

Checks (grouped by severity):

  critical
    - duplicate_id            same id appears more than once in a dataset
    - control_chars_in_field  raw \\t / \\r / \\xa0 leaked into id, name, or text
    - footer_leakage          "System Reference Document" copy bled into prose
    - inventory_mismatch      meta.json.datasets[*].count disagrees with actual counts

  warning
    - bad_id_format           id does not match ``^[a-z][a-z0-9_]*:[a-z0-9_]+$``
    - missing_reference       cross-dataset id not resolved (e.g. feature_id)

Exit codes:
  0  no findings of the selected severity or higher (default: none required)
  1  one or more findings at or above ``--fail-on`` severity
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Make src/srd_builder importable when invoked directly from the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from srd_builder.utils.metadata import ALL_DATASETS  # noqa: E402

SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}

ID_RE = re.compile(r"^[a-z][a-z0-9_]*:[a-z0-9_]+$")
CONTROL_RE = re.compile(r"[\t\r\xa0]")
FOOTER_RE = re.compile(r"System Reference Document", re.IGNORECASE)
TEXT_FIELDS = ("text", "description", "summary")


@dataclass(frozen=True)
class Finding:
    severity: str
    dataset: str
    code: str
    detail: str
    item_id: str | None = None


def _load_items(dist_dir: Path, dataset: str) -> list[dict[str, Any]]:
    """Return the dataset's item list, accepting any of the three shipped shapes."""
    path = dist_dir / f"{dataset}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    for key in ("items", dataset, "features"):
        value = data.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []


def _iter_text(value: Any) -> Iterator[str]:
    """Yield every string contained in nested dicts / lists."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from _iter_text(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _iter_text(v)


# ---------------------------------------------------------------------------
# Individual checks


def check_ids(dataset: str, items: list[dict[str, Any]]) -> Iterable[Finding]:
    """Flag bad id formats and duplicate ids."""
    counter: Counter[str] = Counter()
    for item in items:
        rid = item.get("id")
        if not isinstance(rid, str) or not rid:
            continue
        counter[rid] += 1
        if not ID_RE.match(rid):
            yield Finding(
                severity="warning",
                dataset=dataset,
                code="bad_id_format",
                detail=f"id={rid!r} (name={item.get('name')!r})",
                item_id=rid,
            )
    for rid, count in counter.items():
        if count > 1:
            yield Finding(
                severity="critical",
                dataset=dataset,
                code="duplicate_id",
                detail=f"id {rid!r} appears {count}x",
                item_id=rid,
            )


def check_control_chars(dataset: str, items: list[dict[str, Any]]) -> Iterable[Finding]:
    """Flag tab / CR / non-breaking-space leaked into identifiers or names."""
    for item in items:
        rid = item.get("id") if isinstance(item.get("id"), str) else None
        for field in ("id", "name"):
            value = item.get(field)
            if isinstance(value, str) and CONTROL_RE.search(value):
                yield Finding(
                    severity="critical",
                    dataset=dataset,
                    code="control_chars_in_field",
                    detail=f"{field}={value!r}",
                    item_id=rid,
                )


def check_footer_leakage(dataset: str, items: list[dict[str, Any]]) -> Iterable[Finding]:
    """Flag prose fields that still contain the PDF footer copy."""
    for item in items:
        rid = item.get("id") if isinstance(item.get("id"), str) else None
        for field in TEXT_FIELDS:
            for text in _iter_text(item.get(field)):
                if FOOTER_RE.search(text):
                    yield Finding(
                        severity="critical",
                        dataset=dataset,
                        code="footer_leakage",
                        detail=f"{field} contains PDF footer",
                        item_id=rid,
                    )
                    break
        # Monster / class action descriptions are nested one level deeper.
        for action in item.get("actions", []) or []:
            if not isinstance(action, dict):
                continue
            for text in _iter_text(action.get("description")):
                if FOOTER_RE.search(text):
                    aname = action.get("name", "?")
                    yield Finding(
                        severity="critical",
                        dataset=dataset,
                        code="footer_leakage",
                        detail=f"action {aname!r}: description contains PDF footer",
                        item_id=rid,
                    )
                    break


def _collect_ids(items: list[dict[str, Any]]) -> set[str]:
    return {item["id"] for item in items if isinstance(item.get("id"), str)}


def check_cross_references(distributions: dict[str, list[dict[str, Any]]]) -> Iterable[Finding]:
    """Resolve a small set of high-signal cross-dataset id references."""
    damage_ids = _collect_ids(distributions.get("damage_types", []))
    feature_ids = _collect_ids(distributions.get("features", []))
    spell_ids = _collect_ids(distributions.get("spells", []))
    ability_ids = _collect_ids(distributions.get("ability_scores", []))

    for monster in distributions.get("monsters", []):
        mid = monster.get("id")
        for field in ("damage_resistances", "damage_immunities", "damage_vulnerabilities"):
            for entry in monster.get(field, []) or []:
                if not isinstance(entry, dict):
                    continue
                tid = entry.get("type_id")
                if tid and tid not in damage_ids:
                    yield Finding(
                        severity="warning",
                        dataset="monsters",
                        code="missing_reference",
                        detail=f"{field}: damage_type {tid!r} not in damage_types",
                        item_id=mid,
                    )
        for action in monster.get("actions", []) or []:
            if not isinstance(action, dict):
                continue
            dc = action.get("dc") or {}
            aid = dc.get("dc_type_id")
            if aid and aid not in ability_ids:
                yield Finding(
                    severity="warning",
                    dataset="monsters",
                    code="missing_reference",
                    detail=f"action {action.get('name')!r}: ability {aid!r} not in ability_scores",
                    item_id=mid,
                )
        for spell_ref in (monster.get("innate_spellcasting") or {}).get("spells", []):
            if isinstance(spell_ref, dict):
                sid = spell_ref.get("spell_id")
                if sid and sid not in spell_ids:
                    yield Finding(
                        severity="warning",
                        dataset="monsters",
                        code="missing_reference",
                        detail=f"innate_spellcasting: spell {sid!r} not in spells",
                        item_id=mid,
                    )

    for source_ds in ("classes", "lineages"):
        for item in distributions.get(source_ds, []):
            owner_id = item.get("id")
            for fid in item.get("features", []) or []:
                if isinstance(fid, str) and fid not in feature_ids:
                    yield Finding(
                        severity="warning",
                        dataset=source_ds,
                        code="missing_reference",
                        detail=f"feature {fid!r} not in features",
                        item_id=owner_id,
                    )


def check_inventory(dist_dir: Path, counts: dict[str, int]) -> Iterable[Finding]:
    """Confirm meta.json.datasets[*].count matches the on-disk dataset sizes."""
    meta_path = dist_dir / "meta.json"
    if not meta_path.exists():
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return
    datasets = meta.get("datasets")
    if not isinstance(datasets, dict):
        return
    for dataset, actual in counts.items():
        entry = datasets.get(dataset)
        if not isinstance(entry, dict):
            yield Finding(
                severity="critical",
                dataset=dataset,
                code="inventory_mismatch",
                detail="not present in meta.json.datasets",
            )
            continue
        declared = entry.get("count")
        if declared != actual:
            yield Finding(
                severity="critical",
                dataset=dataset,
                code="inventory_mismatch",
                detail=f"meta declares {declared}, dist contains {actual}",
            )


# ---------------------------------------------------------------------------
# Driver


def audit(dist_dir: Path) -> tuple[list[Finding], dict[str, int]]:
    """Run every check; return findings list and per-dataset counts."""
    distributions = {ds: _load_items(dist_dir, ds) for ds in ALL_DATASETS}
    counts = {ds: len(items) for ds, items in distributions.items()}

    findings: list[Finding] = []
    for dataset, items in distributions.items():
        if not items:
            continue
        findings.extend(check_ids(dataset, items))
        findings.extend(check_control_chars(dataset, items))
        findings.extend(check_footer_leakage(dataset, items))
    findings.extend(check_cross_references(distributions))
    findings.extend(check_inventory(dist_dir, counts))
    return findings, counts


def render_summary(findings: list[Finding], counts: dict[str, int]) -> str:
    by_severity: Counter[str] = Counter(f.severity for f in findings)
    by_code: Counter[tuple[str, str]] = Counter((f.severity, f.code) for f in findings)
    by_dataset: Counter[str] = Counter(f.dataset for f in findings)

    lines = ["=== srd-builder data quality audit ===", ""]
    lines.append(f"datasets scanned: {sum(1 for v in counts.values() if v)}")
    lines.append(f"total items:      {sum(counts.values())}")
    lines.append(f"total findings:   {len(findings)}")
    lines.append("")
    lines.append("findings by severity:")
    for severity in ("critical", "warning", "info"):
        lines.append(f"  {severity:8s} {by_severity[severity]}")
    lines.append("")
    lines.append("findings by code:")
    for (severity, code), count in sorted(
        by_code.items(), key=lambda kv: (-SEVERITY_ORDER[kv[0][0]], -kv[1])
    ):
        lines.append(f"  [{severity:8s}] {code:24s} {count}")
    if by_dataset:
        lines.append("")
        lines.append("findings by dataset:")
        for dataset, count in by_dataset.most_common():
            lines.append(f"  {dataset:20s} {count}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dist",
        type=Path,
        default=REPO_ROOT / "dist" / "srd_5_1",
        help="distribution directory to audit (default: dist/srd_5_1)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="write JSON report to this path",
    )
    parser.add_argument(
        "--fail-on",
        choices=("critical", "warning", "info"),
        default=None,
        help="exit non-zero when findings at or above this severity exist",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the human summary",
    )
    args = parser.parse_args()

    if not args.dist.exists():
        print(f"error: dist directory does not exist: {args.dist}", file=sys.stderr)
        return 2

    findings, counts = audit(args.dist)

    if args.output is not None:
        report = {
            "dist": str(args.dist),
            "counts": counts,
            "summary": dict(Counter(f.severity for f in findings)),
            "findings": [asdict(f) for f in findings],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")

    if not args.quiet:
        print(render_summary(findings, counts))

    if args.fail_on is not None:
        threshold = SEVERITY_ORDER[args.fail_on]
        if any(SEVERITY_ORDER[f.severity] >= threshold for f in findings):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
