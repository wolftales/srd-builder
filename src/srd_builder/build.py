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
from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

from . import __version__
from .extract_monsters import extract_monsters
from .indexer import build_indexes
from .parse_monsters import parse_monster_records
from .postprocess import clean_monster_record

RULESETS_DIRNAME: Final = "rulesets"
DATA_SOURCE: Final = "SRD_CC_v5.1"
SCHEMA_VERSION: Final = "1.1.0"


def _meta_block(ruleset: str) -> dict[str, str]:
    return {
        "ruleset": ruleset,
        "schema_version": SCHEMA_VERSION,
        "source": DATA_SOURCE,
        "build_report": "../build_report.json",
        "generated_by": f"srd-builder v{__version__}",
    }


def _wrap_with_meta(payload: dict[str, Any], *, ruleset: str) -> dict[str, Any]:
    document: OrderedDict[str, Any] = OrderedDict()
    document["_meta"] = _meta_block(ruleset)
    for key, value in payload.items():
        document[key] = value
    return document


def _load_raw_monsters(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw monster data from extraction output.

    Tries monsters_raw.json first (v0.3.0 extraction format),
    falls back to monsters.json (legacy TabylTop format).
    """
    # Try v0.3.0 extraction format first
    raw_source = raw_dir / "monsters_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "monsters" in data:
            return data["monsters"]
        raise TypeError("monsters_raw.json must contain 'monsters' key with array")

    # Fall back to legacy format
    legacy_source = raw_dir / "monsters.json"
    if legacy_source.exists():
        data = json.loads(legacy_source.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise TypeError("ruleset raw monsters must be stored as a JSON array")
        return data

    return []


def _render_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _write_datasets(
    *,
    ruleset: str,
    data_dir: Path,
    monsters: list[dict[str, Any]],
) -> None:
    processed = [clean_monster_record(monster) for monster in monsters]

    monsters_doc = _wrap_with_meta({"items": processed}, ruleset=ruleset)
    (data_dir / "monsters.json").write_text(
        _render_json(monsters_doc),
        encoding="utf-8",
    )

    index_payload = build_indexes(processed)
    index_doc = _wrap_with_meta(index_payload, ruleset=ruleset)
    (data_dir / "index.json").write_text(
        _render_json(index_doc),
        encoding="utf-8",
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


def _extract_raw_monsters(raw_dir: Path) -> Path | None:
    """Extract monsters from PDF if present.

    Returns:
        Path to extracted monsters_raw.json, or None if no PDF found
    """
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF found; extraction will skip.")
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting monsters from {pdf_path.name}...")

    # Run extraction
    extracted_data = extract_monsters(pdf_path)

    # Write to raw directory
    output_path = raw_dir / "monsters_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    monster_count = extracted_data["_meta"]["monster_count"]
    warnings = extracted_data["_meta"]["total_warnings"]
    print(f"✓ Extracted {monster_count} monsters (warnings: {warnings})")
    print(f"✓ Saved to {output_path}")

    # Update meta.json with PDF hash
    meta_path = raw_dir / "meta.json"
    meta: dict[str, object]
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            print(
                f"Warning: {meta_path} contains JSON that is not an object (got {type(meta).__name__}); resetting to empty dict.",
            )
            meta = {}
    else:
        meta = {}

    meta["pdf_sha256"] = extracted_data["_meta"]["pdf_sha256"]
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return output_path


def build(ruleset: str, output_format: str, out_dir: Path) -> Path:
    layout = ensure_ruleset_layout(ruleset=ruleset, out_dir=out_dir)
    target_dir = layout["dist_ruleset"]

    report = BuildReport.create(ruleset=ruleset, output_format=output_format)
    report_path = target_dir / "build_report.json"
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")

    # Extract monsters from PDF (v0.3.0)
    _extract_raw_monsters(raw_dir=layout["raw"])

    raw_monsters = _load_raw_monsters(layout["raw"])
    parsed = parse_monster_records(raw_monsters)
    _write_datasets(ruleset=ruleset, data_dir=layout["data"], monsters=parsed)

    return report_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out)
    build(ruleset=args.ruleset, output_format=args.format, out_dir=out_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
