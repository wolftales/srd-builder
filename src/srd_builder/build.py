"""Build scaffold for srd-builder.

The goal of this module is to provide a deterministic entry point that
creates predictable output directories without attempting to parse SRD
content yet. Future implementations will replace the stubbed pieces
with real extraction logic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from . import __version__


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


RULESETS_DIRNAME: Final = "rulesets"


def ensure_ruleset_layout(ruleset: str, out_dir: Path) -> dict[str, Path]:
    """Create the directory layout expected for a ruleset build.

    Returns a mapping of key directory names to their resolved paths.
    """

    dist_ruleset_dir = out_dir / ruleset
    data_dir = dist_ruleset_dir / "data"
    raw_dir = Path(RULESETS_DIRNAME) / ruleset / "raw"
    extracted_dir = raw_dir / "extracted"

    dist_ruleset_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(exist_ok=True)

    return {
        "dist_ruleset": dist_ruleset_dir,
        "data": data_dir,
        "raw": raw_dir,
        "extracted": extracted_dir,
    }


def _update_pdf_metadata(raw_dir: Path) -> None:
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF found; v0.2.0 extractor will skip.")
        return

    pdf_path = pdf_files[0]
    sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    meta_path = raw_dir / "meta.json"
    meta: dict[str, object]
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            print(
                f"Warning: {meta_path} contains JSON that is not an object (got {type(meta).__name__}); resetting to empty dict."
            )
            meta = {}
    else:
        meta = {}

    meta["pdf_sha256"] = sha256
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("Found PDF; v0.2.0 will extract raw JSON.")


def build(ruleset: str, output_format: str, out_dir: Path) -> Path:
    layout = ensure_ruleset_layout(ruleset=ruleset, out_dir=out_dir)
    target_dir = layout["dist_ruleset"]

    report = BuildReport.create(ruleset=ruleset, output_format=output_format)
    report_path = target_dir / "build_report.json"
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")

    _update_pdf_metadata(raw_dir=layout["raw"])

    return report_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out)
    build(ruleset=args.ruleset, output_format=args.format, out_dir=out_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
