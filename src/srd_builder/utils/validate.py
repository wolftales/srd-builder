"""Strict validation of SRD bundle datasets against shipped JSON Schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from collections.abc import Iterable
from itertools import islice
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..constants import DIST_DIRNAME, RULESETS_DIRNAME, SCHEMAS_DIRNAME

SCHEMA_DIR = Path(__file__).resolve().parents[3] / SCHEMAS_DIRNAME
DIST_DIR = Path(__file__).resolve().parents[3] / DIST_DIRNAME
RULESETS_DIR = Path(__file__).resolve().parents[3] / RULESETS_DIRNAME

# Maps every emitted dataset filename to the schema stem (file without .schema.json)
# that defines its item shape. Every dataset shipped in dist/<ruleset>/ MUST appear
# here, otherwise the strict validator silently skips it.
DATASET_SCHEMA_MAP: dict[str, str] = {
    "ability_scores.json": "ability_score",
    "classes.json": "class",
    "conditions.json": "condition",
    "damage_types.json": "damage_type",
    "diseases.json": "disease",
    "equipment.json": "equipment",
    "features.json": "features",
    "lineages.json": "lineage",
    "magic_items.json": "magic_item",
    "monsters.json": "monster",
    "poisons.json": "poison",
    "rules.json": "rule",
    "skills.json": "skill",
    "spells.json": "spell",
    "tables.json": "table",
    "weapon_properties.json": "weapon_property",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _categorize_error(err: Any) -> str:
    """Build a stable category key from a jsonschema ValidationError."""
    path = ".".join(str(p) for p in err.absolute_path) or "<root>"
    return f"{err.validator}@{path}"


def validate_one_dataset(
    *,
    data_path: Path,
    schema_path: Path,
    limit: int | None = None,
) -> dict[str, Any]:
    """Validate a single dataset file against a schema, collecting every error."""
    report: dict[str, Any] = {
        "dataset": data_path.name,
        "status": "OK",
        "total": 0,
        "failed": 0,
        "categories": {},
        "errors": [],
    }
    if not data_path.exists():
        report["status"] = "NO_DATA"
        return report
    if not schema_path.exists():
        report["status"] = "NO_SCHEMA"
        return report

    document = load_json(data_path)
    items = document.get("items", []) if isinstance(document, dict) else []
    if not isinstance(items, list):
        report["status"] = "BAD_SHAPE"
        return report

    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)

    iterable: Iterable[Any] = items
    if limit is not None:
        iterable = islice(iterable, limit)

    categories: dict[str, int] = defaultdict(int)
    errors_list: list[dict[str, str]] = []
    total = 0
    failed = 0

    for item in iterable:
        total += 1
        if not isinstance(item, dict):
            continue
        item_errors = list(validator.iter_errors(item))
        if item_errors:
            failed += 1
            item_id = str(item.get("id", "<no-id>"))
            for err in item_errors:
                cat = _categorize_error(err)
                categories[cat] += 1
                errors_list.append(
                    {
                        "id": item_id,
                        "category": cat,
                        "path": ".".join(str(p) for p in err.absolute_path),
                        "message": err.message,
                    }
                )

    report["total"] = total
    report["failed"] = failed
    report["categories"] = dict(categories)
    report["errors"] = errors_list
    report["status"] = "OK" if failed == 0 else "FAIL"
    return report


def validate_all_datasets(
    ruleset: str,
    *,
    schema_source: str = "bundle",
    limit: int | None = None,
) -> dict[str, Any]:
    """Validate every dataset shipped under ``dist/<ruleset>/`` against shipped schemas."""
    ruleset_dir = DIST_DIR / ruleset
    if schema_source == "bundle":
        schema_dir = ruleset_dir / "schemas"
    elif schema_source == "repo":
        schema_dir = SCHEMA_DIR
    else:
        raise ValueError(f"schema_source must be 'bundle' or 'repo', got {schema_source!r}")

    dataset_reports: list[dict[str, Any]] = []
    total_items = 0
    total_failed = 0
    for dataset_file, schema_stem in DATASET_SCHEMA_MAP.items():
        d_report = validate_one_dataset(
            data_path=ruleset_dir / dataset_file,
            schema_path=schema_dir / f"{schema_stem}.schema.json",
            limit=limit,
        )
        dataset_reports.append(d_report)
        total_items += d_report["total"]
        total_failed += d_report["failed"]

    return {
        "ruleset": ruleset,
        "schema_source": schema_source,
        "total_items": total_items,
        "total_failed": total_failed,
        "datasets": dataset_reports,
    }


def render_report(report: dict[str, Any], *, show_samples: int = 3) -> str:
    """Pretty-print a validation report as a multi-line string."""
    lines: list[str] = []
    lines.append(
        f"Validation report for ruleset '{report['ruleset']}' (schemas={report['schema_source']})"
    )
    lines.append("")
    lines.append(f"{'Dataset':<28}{'Total':>8}{'Fail':>8}  Status")
    lines.append("-" * 60)
    for d in report["datasets"]:
        lines.append(f"{d['dataset']:<28}{d['total']:>8}{d['failed']:>8}  {d['status']}")
    lines.append("-" * 60)
    lines.append(f"{'TOTAL':<28}{report['total_items']:>8}{report['total_failed']:>8}")

    if report["total_failed"]:
        lines.append("")
        lines.append("Error categories per failing dataset (top 5 each):")
        for d in report["datasets"]:
            if not d["failed"]:
                continue
            lines.append("")
            lines.append(f"  {d['dataset']} ({d['failed']} failing items):")
            for cat, n in sorted(d["categories"].items(), key=lambda x: -x[1])[:5]:
                lines.append(f"    [{n:>4}] {cat}")
            if show_samples:
                lines.append("    samples:")
                for err in d["errors"][:show_samples]:
                    msg = err["message"]
                    if len(msg) > 120:
                        msg = msg[:117] + "..."
                    lines.append(f"      {err['id']}  [{err['category']}]")
                    lines.append(f"        {msg}")
    return "\n".join(lines)


def check_data_quality(ruleset: str) -> None:  # noqa: C901
    """Check data quality issues beyond schema validation.

    Validates:
    - No spells with empty text fields
    - No duplicate IDs in index
    """
    issues: list[str] = []

    # Check spells for empty text
    spells_file = DIST_DIR / ruleset / "spells.json"
    if spells_file.exists():
        document = load_json(spells_file)
        if isinstance(document, dict):
            spells = document.get("items", [])
            empty_desc_spells = []
            only_higher_levels_spells = []
            for s in spells:
                if isinstance(s, dict):
                    description = s.get("description")
                    # Check if 'description' is missing, is not a list, or is an empty list
                    if not isinstance(description, list) or not description:
                        empty_desc_spells.append(s.get("name", "unknown"))
                    # Check if all strings within the list are empty/whitespace
                    elif all(not para.strip() for para in description):
                        empty_desc_spells.append(s.get("name", "unknown"))
                    # Check if spell only has "At Higher Levels" text (missing main description)
                    elif len(description) == 1 and description[0].strip().startswith(
                        "At Higher Levels"
                    ):
                        only_higher_levels_spells.append(s.get("name", "unknown"))

            if empty_desc_spells:
                issues.append(f"Spells with empty description: {', '.join(empty_desc_spells)}")
            if only_higher_levels_spells:
                issues.append(
                    f"Spells with only 'At Higher Levels' text (missing main description): {', '.join(only_higher_levels_spells)}"
                )

    # Check index for duplicates
    index_file = DIST_DIR / ruleset / "index.json"
    if index_file.exists():
        document = load_json(index_file)
        if isinstance(document, dict):
            # Check equipment by_rarity for duplicates
            equipment = document.get("equipment", {})
            if isinstance(equipment, dict):
                by_rarity = equipment.get("by_rarity", {})
                if isinstance(by_rarity, dict):
                    for rarity, items in by_rarity.items():
                        if isinstance(items, list):
                            seen: set[str] = set()
                            for item_id in items:
                                if item_id in seen:
                                    issues.append(
                                        f"Duplicate in equipment.by_rarity.{rarity}: {item_id}"
                                    )
                                seen.add(item_id)

    if issues:
        raise ValueError("Data quality issues found:\n  - " + "\n  - ".join(issues))

    print(f"OK: Data quality checks passed for ruleset '{ruleset}'.")


def _ensure_build_report(ruleset: str) -> None:
    # As of v0.38.0 build_report.json lives alongside the bundle (not inside it)
    # so the bundle directory stays byte-deterministic. Same producer, same
    # consumer-visible information, different location.
    report_path = DIST_DIR / "build_report.json"
    if not report_path.exists():
        raise FileNotFoundError(
            f"build_report.json missing for ruleset '{ruleset}'. "
            f"Expected at {report_path}. Did you run build?"
        )

    print(f"OK: build_report.json present for {ruleset} at {report_path}.")


def _check_pdf_hash(ruleset: str) -> None:
    raw_dir = RULESETS_DIR / ruleset / "raw"
    pdf_files = sorted(raw_dir.glob("*.pdf")) if raw_dir.exists() else []

    pdf_meta_path = raw_dir / "pdf_meta.json"
    if pdf_files:
        if not pdf_meta_path.exists():
            raise FileNotFoundError(
                f"PDF file(s) found in '{raw_dir}' but pdf_meta.json is missing. Cannot validate PDF hash."
            )

        pdf_meta_obj = load_json(pdf_meta_path)
        if not isinstance(pdf_meta_obj, dict) or "pdf_sha256" not in pdf_meta_obj:
            print("PDF/hash not present — OK for v0.2.0.")
            return

        recorded_hash = pdf_meta_obj["pdf_sha256"]
        if not isinstance(recorded_hash, str):
            raise TypeError("pdf_meta.json pdf_sha256 must be a string")

        pdf_path = pdf_files[0]
        computed_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        if computed_hash != recorded_hash:
            raise ValueError(
                "PDF hash mismatch: pdf_meta.json pdf_sha256 does not match the current file"
            )

        print("OK: PDF hash matches pdf_meta.json.")
        return

    print("PDF/hash not present — OK for v0.2.0.")


def validate_ruleset(
    ruleset: str,
    limit: int | None = None,
    *,
    strict: bool = True,
    schema_source: str = "bundle",
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Run the full validation suite for a ruleset bundle.

    With ``strict=True`` (the default) any schema-validation failure raises
    ``SystemExit(1)`` after a full report has been printed. This is the
    producer-side gate: emitted data MUST conform to its shipped schemas.
    Pass ``strict=False`` for report-only mode during iteration.
    """
    _ensure_build_report(ruleset)
    _check_pdf_hash(ruleset)

    report = validate_all_datasets(ruleset, schema_source=schema_source, limit=limit)
    print(render_report(report))

    if report_path is not None:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nWrote machine-readable report to {report_path}")

    check_data_quality(ruleset=ruleset)

    if strict and report["total_failed"]:
        n_ds = sum(1 for d in report["datasets"] if d["failed"])
        sys.stdout.flush()
        raise SystemExit(
            f"\nStrict validation FAILED: {report['total_failed']} item(s) "
            f"across {n_ds} dataset(s) failed schema validation."
        )

    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Strict validation of an SRD bundle against shipped JSON Schemas"
    )
    parser.add_argument("--ruleset", required=True, help="Ruleset identifier (e.g. srd_5_1)")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on items validated per dataset (debugging only)",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print the report but exit 0 even when failures exist (iteration mode)",
    )
    parser.add_argument(
        "--schema-source",
        choices=("bundle", "repo"),
        default="bundle",
        help="Validate against schemas shipped in the bundle (default) or repo top-level schemas/",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write a machine-readable JSON report (dataset/id/category/path/message) to this path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        validate_ruleset(
            ruleset=args.ruleset,
            limit=args.limit,
            strict=not args.report_only,
            schema_source=args.schema_source,
            report_path=args.report,
        )
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            return 1
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
