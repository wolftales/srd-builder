"""Validation helpers for SRD datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable
from itertools import islice
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
DIST_DIR = Path(__file__).resolve().parents[2] / "dist"
RULESETS_DIR = Path(__file__).resolve().parents[2] / "rulesets"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_monsters(ruleset: str, limit: int | None = None) -> int:
    data_file = DIST_DIR / ruleset / "monsters.json"
    if not data_file.exists():
        print(f"No monsters.json found for ruleset '{ruleset}'. Skipping validation.")
        return 0

    schema_file = SCHEMA_DIR / "monster.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(
            "Monster schema is missing. Did you remove schemas/monster.schema.json?"
        )

    document = load_json(data_file)
    if not isinstance(document, dict):  # pragma: no cover - defensive guard
        raise TypeError("monsters.json must contain a JSON object")
    monsters = document.get("items", [])
    if not isinstance(monsters, list):
        raise TypeError("monsters.json 'items' must contain a JSON array")

    schema = load_json(schema_file)
    validator = Draft202012Validator(schema)

    count = 0
    iterable: Iterable[object] = monsters
    if limit is not None:
        iterable = islice(iterable, limit)

    for monster in iterable:
        validator.validate(monster)
        count += 1

    print(f"Validated {count} monster entries for ruleset '{ruleset}'.")
    return count


def validate_spells(ruleset: str, limit: int | None = None) -> int:
    data_file = DIST_DIR / ruleset / "spells.json"
    if not data_file.exists():
        print(f"No spells.json found for ruleset '{ruleset}'. Skipping validation.")
        return 0

    schema_file = SCHEMA_DIR / "spell.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(
            "Spell schema is missing. Did you remove schemas/spell.schema.json?"
        )

    document = load_json(data_file)
    if not isinstance(document, dict):  # pragma: no cover - defensive guard
        raise TypeError("spells.json must contain a JSON object")
    spells = document.get("items", [])
    if not isinstance(spells, list):
        raise TypeError("spells.json 'items' must contain a JSON array")

    schema = load_json(schema_file)
    validator = Draft202012Validator(schema)

    count = 0
    iterable: Iterable[object] = spells
    if limit is not None:
        iterable = islice(iterable, limit)

    for spell in iterable:
        validator.validate(spell)
        count += 1

    print(f"Validated {count} spell entries for ruleset '{ruleset}'.")
    return count


def validate_lineages(ruleset: str, limit: int | None = None) -> int:
    data_file = DIST_DIR / ruleset / "lineages.json"
    if not data_file.exists():
        print(f"No lineages.json found for ruleset '{ruleset}'. Skipping validation.")
        return 0

    schema_file = SCHEMA_DIR / "lineage.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(
            "Lineage schema is missing. Did you remove schemas/lineage.schema.json?"
        )

    document = load_json(data_file)
    if not isinstance(document, dict):  # pragma: no cover - defensive guard
        raise TypeError("lineages.json must contain a JSON object")
    lineages = document.get("items", [])
    if not isinstance(lineages, list):
        raise TypeError("lineages.json 'items' must contain a JSON array")

    schema = load_json(schema_file)
    validator = Draft202012Validator(schema)

    count = 0
    iterable: Iterable[object] = lineages
    if limit is not None:
        iterable = islice(iterable, limit)

    for lineage in iterable:
        validator.validate(lineage)
        count += 1

    print(f"Validated {count} lineage entries for ruleset '{ruleset}'.")
    return count


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
