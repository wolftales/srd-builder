"""Build scaffold for srd-builder.

The goal of this module is to provide a deterministic entry point that
creates predictable output directories without attempting to parse SRD
content yet. Future implementations will replace the stubbed pieces
with real extraction logic.
"""

from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .indexer import build_indexes
from .parse_monsters import normalize_monster
from .postprocess import (
    polish_text_fields,
    rename_abilities_to_traits,
    split_legendary,
    standardize_challenge,
    structure_defenses,
    unify_simple_name,
)


@dataclass
class BuildReport:
    """Small metadata payload written alongside build artifacts."""

    ruleset: str
    output_format: str
    timestamp_utc: str
    builder_version: str
    python_version: str

    @classmethod
    def create(cls, ruleset: str, output_format: str) -> BuildReport:
        # The timestamp only lives in the report to aid debugging. Downstream
        # dataset files should remain timestamp-free to keep builds reproducible.
        timestamp = datetime.now(timezone.utc).isoformat()
        return cls(
            ruleset=ruleset,
            output_format=output_format,
            timestamp_utc=timestamp,
            builder_version=__version__,
            python_version=platform.python_version(),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SRD datasets")
    parser.add_argument(
        "--ruleset",
        required=True,
        help="Ruleset identifier (e.g. srd_5_1)",
    )
    parser.add_argument(
        "--format",
        default="json",
        choices=["json"],
        help="Output format to generate (json only for now)",
    )
    parser.add_argument(
        "--out",
        default="dist",
        help="Root output directory for build artifacts",
    )
    return parser.parse_args(argv)


def build(ruleset: str, output_format: str, out_dir: Path) -> Path:
    target_dir = out_dir / ruleset
    target_dir.mkdir(parents=True, exist_ok=True)

    report = BuildReport.create(ruleset=ruleset, output_format=output_format)
    report_path = target_dir / "build_report.json"
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")

    raw_path = Path("rulesets") / ruleset / "raw" / "monsters.json"
    if not raw_path.exists():
        print(f"No raw monsters found at {raw_path}, skipping dataset build.")
        return report_path

    monsters_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    monsters_norm = [normalize_monster(monster) for monster in monsters_raw]

    def compose(*fns):
        def inner(value):
            for fn in fns:
                value = fn(value)
            return value

        return inner

    postprocess = compose(
        unify_simple_name,
        rename_abilities_to_traits,
        split_legendary,
        structure_defenses,
        standardize_challenge,
        polish_text_fields,
    )
    monsters_final = [postprocess(monster) for monster in monsters_norm]

    index_blob = build_indexes(monsters_final)

    data_dir = target_dir / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "monsters.json").write_text(
        json.dumps(monsters_final, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (data_dir / "index.json").write_text(
        json.dumps(index_blob, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return report_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out)
    build(ruleset=args.ruleset, output_format=args.format, out_dir=out_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
