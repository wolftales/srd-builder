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
from .extract_equipment import extract_equipment
from .extract_monsters import extract_monsters
from .indexer import build_indexes
from .parse_equipment import parse_equipment_records
from .parse_monsters import parse_monster_records
from .postprocess import clean_equipment_record, clean_monster_record

RULESETS_DIRNAME: Final = "rulesets"
DATA_SOURCE: Final = "SRD_CC_v5.1"
SCHEMA_VERSION: Final = "1.1.0"
FORMAT_VERSION: Final = "v0.4.1"


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


def _generate_meta_json(
    *,
    pdf_hash: str | None,
    monsters_complete: bool,
    monsters_page_range: tuple[int, int] | None = None,
    equipment_complete: bool = False,
    equipment_page_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Generate rich metadata for dist/meta.json with provenance.

    This is the consumer-facing metadata that includes license info,
    page index for all content types, file manifest, and extraction status.
    """
    return {
        "version": "5.1",
        "source": DATA_SOURCE,
        "format_version": FORMAT_VERSION,
        "license": {
            "type": "CC-BY-4.0",
            "url": "https://creativecommons.org/licenses/by/4.0/legalcode",
            "attribution": (
                "This work includes material taken from the System Reference Document 5.1 "
                '("SRD 5.1") by Wizards of the Coast LLC and available at '
                "https://dnd.wizards.com/resources/systems-reference-document. "
                "The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 "
                "International License available at https://creativecommons.org/licenses/by/4.0/legalcode."
            ),
            "conversion_note": (
                "Converted from the original PDF by srd-builder "
                f"(https://github.com/wolftales/srd-builder) version {__version__}"
            ),
        },
        "build": {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extractor_version": FORMAT_VERSION,
            "builder_version": __version__,
            "pdf_hash": f"sha256:{pdf_hash}" if pdf_hash else None,
        },
        "page_index": _build_page_index(monsters_page_range, equipment_page_range),
        "files": {
            "meta": "meta.json",
            "build_report": "build_report.json",
            "index": "data/index.json",
            "monsters": "data/monsters.json",
            "equipment": "data/equipment.json",
        },
        "extraction_status": {
            "monsters": "complete" if monsters_complete else "in_progress",
            "equipment": "complete" if equipment_complete else "in_progress",
        },
        "$schema_version": "1.1.0",
    }


def _write_datasets(
    *,
    ruleset: str,
    data_dir: Path,
    monsters: list[dict[str, Any]],
    equipment: list[dict[str, Any]] | None = None,
) -> None:
    processed_monsters = [clean_monster_record(monster) for monster in monsters]

    monsters_doc = _wrap_with_meta({"items": processed_monsters}, ruleset=ruleset)
    (data_dir / "monsters.json").write_text(
        _render_json(monsters_doc),
        encoding="utf-8",
    )

    # Write equipment if available
    if equipment:
        processed_equipment = [clean_equipment_record(item) for item in equipment]
        equipment_doc = _wrap_with_meta({"items": processed_equipment}, ruleset=ruleset)
        (data_dir / "equipment.json").write_text(
            _render_json(equipment_doc),
            encoding="utf-8",
        )

    index_payload = build_indexes(processed_monsters)
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
    parser.add_argument(
        "--bundle",
        action="store_true",
        help="Create complete bundle with schemas and documentation (for production)",
    )
    return parser.parse_args(argv)


def ensure_ruleset_layout(ruleset: str, out_dir: Path) -> dict[str, Path]:
    """Create the directory layout expected for a ruleset build.

    Returns a mapping of key directory names to their resolved paths.
    """

    dist_ruleset_dir = out_dir / ruleset
    data_dir = dist_ruleset_dir / "data"
    raw_dir = Path(RULESETS_DIRNAME) / ruleset / "raw"

    dist_ruleset_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    return {
        "dist_ruleset": dist_ruleset_dir,
        "data": data_dir,
        "raw": raw_dir,
    }


def _copy_bundle_collateral(target_dir: Path) -> None:
    """Copy schemas and documentation to create complete bundle.

    For production releases, this assembles the full package with:
    - README.md (from BUNDLE_README.md)
    - schemas/ directory
    - docs/ directory
    """
    repo_root = Path(__file__).resolve().parents[2]

    # Copy README (from BUNDLE_README.md)
    readme_src = repo_root / "docs" / "BUNDLE_README.md"
    readme_dst = target_dir / "README.md"
    if readme_src.exists():
        readme_dst.write_text(readme_src.read_text(encoding="utf-8"), encoding="utf-8")
        print("  ✓ Copied README.md")

    # Copy schemas
    schemas_src = repo_root / "schemas"
    schemas_dst = target_dir / "schemas"
    schemas_dst.mkdir(exist_ok=True)
    for schema_file in ["monster.schema.json", "equipment.schema.json"]:
        src = schemas_src / schema_file
        if src.exists():
            (schemas_dst / schema_file).write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )
    print("  ✓ Copied schemas/")

    # Copy docs
    docs_src = repo_root / "docs"
    docs_dst = target_dir / "docs"
    docs_dst.mkdir(exist_ok=True)
    for doc_file in ["SCHEMAS.md", "DATA_DICTIONARY.md"]:
        src = docs_src / doc_file
        if src.exists():
            (docs_dst / doc_file).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print("  ✓ Copied docs/")


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

    # Update pdf_meta.json with PDF hash (input validation file)
    pdf_meta_path = raw_dir / "pdf_meta.json"
    pdf_meta: dict[str, object]
    if pdf_meta_path.exists():
        pdf_meta = json.loads(pdf_meta_path.read_text(encoding="utf-8"))
        if not isinstance(pdf_meta, dict):
            print(
                f"Warning: {pdf_meta_path} contains JSON that is not an object (got {type(pdf_meta).__name__}); resetting to empty dict.",
            )
            pdf_meta = {}
    else:
        pdf_meta = {}

    pdf_meta["pdf_sha256"] = extracted_data["_meta"]["pdf_sha256"]
    pdf_meta_path.write_text(
        json.dumps(pdf_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return output_path


def _build_page_index(
    monsters_page_range: tuple[int, int] | None,
    equipment_page_range: tuple[int, int] | None,
) -> dict[str, dict[str, int]]:
    """Build page_index section for meta.json."""
    page_index: dict[str, dict[str, int]] = {}
    if monsters_page_range:
        page_index["monsters"] = {"start": monsters_page_range[0], "end": monsters_page_range[1]}
    if equipment_page_range:
        page_index["equipment"] = {"start": equipment_page_range[0], "end": equipment_page_range[1]}
    return page_index


def _extract_raw_equipment(raw_dir: Path) -> Path | None:
    """Extract equipment from PDF if present.

    Returns:
        Path to extracted equipment_raw.json, or None if no PDF found
    """
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting equipment from {pdf_path.name}...")

    # Run extraction
    try:
        extracted_data = extract_equipment(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive guard for non-PDF fixtures
        print(f"⚠️ Equipment extraction skipped: {exc}")
        return None

    # Write to raw directory
    output_path = raw_dir / "equipment_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    item_count = extracted_data["_meta"]["items_extracted"]
    warnings = extracted_data["_meta"]["warnings"]
    print(f"✓ Extracted {item_count} equipment items (warnings: {len(warnings)})")
    print(f"✓ Saved to {output_path}")

    return output_path


def _load_raw_equipment(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw equipment data from extraction output."""
    raw_source = raw_dir / "equipment_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "equipment" in data:
            return data["equipment"]
        raise TypeError("equipment_raw.json must contain 'equipment' key with array")
    return []


def build(ruleset: str, output_format: str, out_dir: Path, bundle: bool = False) -> Path:
    layout = ensure_ruleset_layout(ruleset=ruleset, out_dir=out_dir)
    target_dir = layout["dist_ruleset"]

    report = BuildReport.create(ruleset=ruleset, output_format=output_format)
    report_path = target_dir / "build_report.json"
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")

    # Extract monsters from PDF (v0.3.0)
    _extract_raw_monsters(raw_dir=layout["raw"])

    # Extract equipment from PDF (v0.5.0)
    _extract_raw_equipment(raw_dir=layout["raw"])

    raw_monsters = _load_raw_monsters(layout["raw"])
    parsed_monsters = parse_monster_records(raw_monsters)

    raw_equipment = _load_raw_equipment(layout["raw"])
    parsed_equipment = parse_equipment_records(raw_equipment)

    _write_datasets(
        ruleset=ruleset,
        data_dir=layout["data"],
        monsters=parsed_monsters,
        equipment=parsed_equipment if parsed_equipment else None,
    )

    # Read PDF hash from pdf_meta.json (if present)
    pdf_meta_path = layout["raw"] / "pdf_meta.json"
    pdf_hash = None
    if pdf_meta_path.exists():
        pdf_meta = json.loads(pdf_meta_path.read_text(encoding="utf-8"))
        if isinstance(pdf_meta, dict):
            pdf_hash = pdf_meta.get("pdf_sha256")

    # Compute page range from raw monsters for provenance
    monsters_page_range = None
    if raw_monsters:
        all_pages = []
        for monster in raw_monsters:
            pages = monster.get("pages", [])
            if isinstance(pages, list):
                all_pages.extend(pages)
        if all_pages:
            monsters_page_range = (min(all_pages), max(all_pages))

    # Compute page range from raw equipment
    equipment_page_range = None
    if raw_equipment:
        all_pages = [page for item in raw_equipment if (page := item.get("page"))]
        if all_pages:
            equipment_page_range = (min(all_pages), max(all_pages))

    # Generate rich meta.json for consumers (includes license, page_index, etc.)
    meta_json = _generate_meta_json(
        pdf_hash=pdf_hash,
        monsters_complete=len(parsed_monsters) > 0,
        monsters_page_range=monsters_page_range,
        equipment_complete=len(parsed_equipment) > 0,
        equipment_page_range=equipment_page_range,
    )
    meta_path = layout["data"] / "meta.json"
    meta_path.write_text(_render_json(meta_json), encoding="utf-8")

    # Copy collateral for production bundle
    if bundle:
        _copy_bundle_collateral(target_dir)

    return report_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out)
    build(ruleset=args.ruleset, output_format=args.format, out_dir=out_dir, bundle=args.bundle)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
