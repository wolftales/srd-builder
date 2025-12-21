"""Validation helpers for SRD datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable
from itertools import islice
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
DIST_DIR = Path(__file__).resolve().parents[3] / "dist"
RULESETS_DIR = Path(__file__).resolve().parents[3] / "rulesets"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dataset(
    ruleset: str,
    *,
    dataset_name: str,
    schema_name: str,
    items_key: str = "items",
    limit: int | None = None,
) -> int:
    """Generic dataset validator to reduce duplication.

    Args:
        ruleset: Ruleset identifier (e.g., 'srd_5_1')
        dataset_name: Name of dataset file (e.g., 'monsters', 'spells')
        schema_name: Name of schema file (e.g., 'monster', 'spell')
        items_key: Key containing items array (default: 'items')
        limit: Optional limit on number of items to validate

    Returns:
        Number of items validated

    Raises:
        FileNotFoundError: If schema is missing
        TypeError: If document structure is invalid
    """
    data_file = DIST_DIR / ruleset / f"{dataset_name}.json"
    if not data_file.exists():
        print(f"No {dataset_name}.json found for ruleset '{ruleset}'. Skipping validation.")
        return 0

    schema_file = SCHEMA_DIR / f"{schema_name}.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(
            f"{schema_name.capitalize()} schema is missing. Did you remove schemas/{schema_name}.schema.json?"
        )

    document = load_json(data_file)
    if not isinstance(document, dict):  # pragma: no cover - defensive guard
        raise TypeError(f"{dataset_name}.json must contain a JSON object")
    items = document.get(items_key, [])
    if not isinstance(items, list):
        raise TypeError(f"{dataset_name}.json '{items_key}' must contain a JSON array")

    schema = load_json(schema_file)
    validator = Draft202012Validator(schema)

    count = 0
    iterable: Iterable[object] = items
    if limit is not None:
        iterable = islice(iterable, limit)

    for item in iterable:
        validator.validate(item)
        count += 1

    entity_label = dataset_name.rstrip("s")  # "monsters" -> "monster"
    print(f"Validated {count} {entity_label} entries for ruleset '{ruleset}'.")
    return count


def validate_monsters(ruleset: str, limit: int | None = None) -> int:
    """Validate monsters.json against monster.schema.json."""
    return validate_dataset(ruleset, dataset_name="monsters", schema_name="monster", limit=limit)


def validate_spells(ruleset: str, limit: int | None = None) -> int:
    """Validate spells.json against spell.schema.json."""
    return validate_dataset(ruleset, dataset_name="spells", schema_name="spell", limit=limit)


def validate_lineages(ruleset: str, limit: int | None = None) -> int:
    """Validate lineages.json against lineage.schema.json."""
    return validate_dataset(ruleset, dataset_name="lineages", schema_name="lineage", limit=limit)


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
            empty_text_spells = [
                s.get("name", "unknown")
                for s in spells
                if isinstance(s, dict) and not s.get("text", "").strip()
            ]
            if empty_text_spells:
                issues.append(f"Spells with empty text: {', '.join(empty_text_spells)}")

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
    report_path = DIST_DIR / ruleset / "build_report.json"
    if not report_path.exists():
        raise FileNotFoundError(
            f"build_report.json missing for ruleset '{ruleset}'. Did you run build?"
        )

    print(f"OK: build_report.json present for {ruleset}.")


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


def validate_ruleset(ruleset: str, limit: int | None = None) -> None:
    _ensure_build_report(ruleset)
    _check_pdf_hash(ruleset)

    validate_monsters(ruleset=ruleset, limit=limit)
    validate_spells(ruleset=ruleset, limit=limit)
    validate_lineages(ruleset=ruleset, limit=limit)
    check_data_quality(ruleset=ruleset)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SRD dataset files")
    parser.add_argument("--ruleset", required=True, help="Ruleset identifier (e.g. srd_5_1)")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of monsters to validate",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    validate_ruleset(ruleset=args.ruleset, limit=args.limit)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
