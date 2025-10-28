"""Validation helpers for SRD datasets."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from itertools import islice
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
RULESETS_DIR = Path(__file__).resolve().parents[2] / "rulesets"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_monsters(ruleset: str, limit: int | None = None) -> int:
    data_file = RULESETS_DIR / ruleset / "data" / "monsters.json"
    if not data_file.exists():
        print(f"No monsters.json found for ruleset '{ruleset}'. Skipping validation.")
        return 0

    schema_file = SCHEMA_DIR / "monster.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(
            "Monster schema is missing. Did you remove schemas/monster.schema.json?"
        )

    monsters = load_json(data_file)
    if not isinstance(monsters, list):  # pragma: no cover - defensive guard
        raise TypeError("monsters.json must contain a JSON array")

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
    validate_monsters(ruleset=args.ruleset, limit=args.limit)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
