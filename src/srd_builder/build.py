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
from typing import Any

from . import __version__
from .constants import DATA_SOURCE, RULESETS_DIRNAME, SCHEMA_VERSION
from .extract_equipment import extract_equipment
from .extract_monsters import extract_monsters
from .extract_pdf_metadata import extract_pdf_metadata
from .extract_spells import extract_spells
from .extract_tables import extract_tables_to_json
from .indexer import build_indexes
from .parse_equipment import parse_equipment_records
from .parse_lineages import parse_lineages
from .parse_monsters import parse_monster_records
from .parse_spells import parse_spell_records
from .parse_tables import parse_single_table
from .postprocess import clean_equipment_record, clean_monster_record, clean_spell_record
from .table_indexer import TableIndexer


def _meta_block(ruleset: str) -> dict[str, str]:
    return {
        "ruleset": ruleset,
        "schema_version": SCHEMA_VERSION,
        "source": DATA_SOURCE,
        "build_report": "./build_report.json",
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
    pdf_metadata: dict[str, Any] | None = None,
    monsters_complete: bool,
    monsters_page_range: tuple[int, int] | None = None,
    equipment_complete: bool = False,
    equipment_page_range: tuple[int, int] | None = None,
    spells_complete: bool = False,
    spells_page_range: tuple[int, int] | None = None,
    table_page_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate rich metadata for dist/meta.json with provenance.

    This is the consumer-facing metadata that includes license info,
    page index for all content types, file manifest, and extraction status.
    """
    # Use extracted PDF metadata if available, otherwise fall back to hardcoded defaults
    version = pdf_metadata.get("version", "5.1") if pdf_metadata else "5.1"
    license_type = pdf_metadata.get("license_type", "CC-BY-4.0") if pdf_metadata else "CC-BY-4.0"
    license_url = (
        pdf_metadata.get("license_url", "https://creativecommons.org/licenses/by/4.0/legalcode")
        if pdf_metadata
        else "https://creativecommons.org/licenses/by/4.0/legalcode"
    )
    attribution = (
        pdf_metadata.get(
            "attribution",
            (
                "This work includes material taken from the System Reference Document 5.1 "
                '("SRD 5.1") by Wizards of the Coast LLC and available at '
                "https://dnd.wizards.com/resources/systems-reference-document. "
                "The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 "
                "International License available at https://creativecommons.org/licenses/by/4.0/legalcode."
            ),
        )
        if pdf_metadata
        else (
            "This work includes material taken from the System Reference Document 5.1 "
            '("SRD 5.1") by Wizards of the Coast LLC and available at '
            "https://dnd.wizards.com/resources/systems-reference-document. "
            "The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 "
            "International License available at https://creativecommons.org/licenses/by/4.0/legalcode."
        )
    )

    return {
        "source": DATA_SOURCE,
        "ruleset_version": version,
        "license": {
            "type": license_type,
            "url": license_url,
            "attribution": attribution,
            "conversion_note": (
                "Converted from the original PDF by srd-builder "
                f"(https://github.com/wolftales/srd-builder) version {__version__}"
            ),
        },
        "build": {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "builder_version": __version__,
            "pdf_hash": f"sha256:{pdf_hash}" if pdf_hash else None,
        },
        "page_index": _build_page_index(
            monsters_page_range, equipment_page_range, spells_page_range, table_page_index
        ),
        "files": {
            "meta": "meta.json",
            "build_report": "build_report.json",
            "index": "index.json",
            "monsters": "monsters.json",
            "equipment": "equipment.json",
            "spells": "spells.json",
            "tables": "tables.json",
            "lineages": "lineages.json",
        },
        "terminology": {"aliases": {"race": "lineage", "races": "lineages"}},
        "extraction_status": {
            "monsters": "complete" if monsters_complete else "in_progress",
            "equipment": "complete" if equipment_complete else "in_progress",
            "spells": "complete" if spells_complete else "in_progress",
            "tables": "complete",
            "lineages": "complete",
        },
        "$schema_version": SCHEMA_VERSION,
    }


def _write_datasets(
    *,
    ruleset: str,
    dist_data_dir: Path,
    monsters: list[dict[str, Any]],
    equipment: list[dict[str, Any]] | None = None,
    spells: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    lineages: list[dict[str, Any]] | None = None,
) -> None:
    processed_monsters = [clean_monster_record(monster) for monster in monsters]

    monsters_doc = _wrap_with_meta({"items": processed_monsters}, ruleset=ruleset)
    (dist_data_dir / "monsters.json").write_text(
        _render_json(monsters_doc),
        encoding="utf-8",
    )

    # Write equipment if available
    processed_equipment = None
    if equipment:
        processed_equipment = [clean_equipment_record(item) for item in equipment]
        equipment_doc = _wrap_with_meta({"items": processed_equipment}, ruleset=ruleset)
        (dist_data_dir / "equipment.json").write_text(
            _render_json(equipment_doc),
            encoding="utf-8",
        )

    # Write spells (always write, even if empty, to maintain consistent structure)
    processed_spells = None
    if spells is not None:
        processed_spells = [clean_spell_record(spell) for spell in spells]
    else:
        processed_spells = []

    spells_doc = _wrap_with_meta({"items": processed_spells}, ruleset=ruleset)
    (dist_data_dir / "spells.json").write_text(
        _render_json(spells_doc),
        encoding="utf-8",
    )

    # Write tables (v0.7.0)
    # Tables are already fully normalized by parse_single_table, no additional cleaning needed
    processed_tables = tables if tables else None
    if processed_tables:
        tables_doc = _wrap_with_meta({"items": processed_tables}, ruleset=ruleset)
        (dist_data_dir / "tables.json").write_text(
            _render_json(tables_doc),
            encoding="utf-8",
        )

    # Write lineages (v0.8.0)
    # Lineages are already fully normalized by parse_lineages, no additional cleaning needed
    processed_lineages = lineages if lineages else None
    if processed_lineages:
        lineages_doc = _wrap_with_meta({"items": processed_lineages}, ruleset=ruleset)
        (dist_data_dir / "lineages.json").write_text(
            _render_json(lineages_doc),
            encoding="utf-8",
        )

    index_payload = build_indexes(
        processed_monsters,
        processed_spells,
        processed_equipment,
        processed_tables,
        processed_lineages,
    )
    index_doc = _wrap_with_meta(index_payload, ruleset=ruleset)
    (dist_data_dir / "index.json").write_text(
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
    raw_dir = Path(RULESETS_DIRNAME) / ruleset / "raw"

    dist_ruleset_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    return {
        "dist_ruleset": dist_ruleset_dir,
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
    for schema_file in [
        "monster.schema.json",
        "equipment.schema.json",
        "spell.schema.json",
        "table.schema.json",
        "lineage.schema.json",
    ]:
        src = schemas_src / schema_file
        if src.exists():
            (schemas_dst / schema_file).write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )
        else:
            print(f"  ⚠ Schema not found: {schema_file}")
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
    spells_page_range: tuple[int, int] | None,
    table_page_index: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build page_index section for meta.json.

    Combines simple page ranges with comprehensive table_indexer data.
    """
    # Start with table indexer data if available (most comprehensive)
    if table_page_index:
        return table_page_index

    # Fallback to simple page ranges
    page_index: dict[str, dict[str, int]] = {}
    if monsters_page_range:
        page_index["monsters"] = {"start": monsters_page_range[0], "end": monsters_page_range[1]}
    if equipment_page_range:
        page_index["equipment"] = {"start": equipment_page_range[0], "end": equipment_page_range[1]}
    if spells_page_range:
        page_index["spells"] = {"start": spells_page_range[0], "end": spells_page_range[1]}
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


def _extract_raw_spells(raw_dir: Path) -> Path | None:
    """Extract spells from PDF if present.

    Returns:
        Path to extracted spells_raw.json, or None if no PDF found
    """
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting spells from {pdf_path.name}...")

    # Run extraction
    try:
        extracted_data = extract_spells(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"⚠️ Spell extraction skipped: {exc}")
        return None

    # Write to raw directory
    output_path = raw_dir / "spells_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    spell_count = extracted_data["_meta"]["spell_count"]
    warnings = extracted_data["_meta"]["total_warnings"]
    print(f"✓ Extracted {spell_count} spells (warnings: {warnings})")
    print(f"✓ Saved to {output_path}")

    return output_path


def _load_raw_spells(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw spell data from extraction output."""
    raw_source = raw_dir / "spells_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "spells" in data:
            return data["spells"]
        raise TypeError("spells_raw.json must contain 'spells' key with array")
    return []


def _extract_raw_tables(raw_dir: Path) -> Path | None:
    """Extract reference tables from PDF.

    Returns:
        Path to extracted tables_raw.json, or None if no PDF found
    """
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting tables from {pdf_path.name}...")

    try:
        output_path = raw_dir / "tables_raw.json"
        extract_tables_to_json(pdf_path, output_path, skip_failures=True)
        print(f"✓ Saved to {output_path}")
        return output_path
    except Exception as exc:  # pragma: no cover
        print(f"⚠️ Table extraction skipped: {exc}")
        return None


def _load_raw_tables(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw table data from extraction output."""
    raw_source = raw_dir / "tables_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "tables" in data:
            return data["tables"]
        raise TypeError("tables_raw.json must contain 'tables' key with array")
    return []


def _generate_table_page_index(
    raw_dir: Path, extracted_table_ids: list[str] | None = None
) -> dict[str, Any] | None:
    """Generate page_index data from table_indexer for meta.json.

    Args:
        raw_dir: Directory containing the PDF
        extracted_table_ids: List of table IDs that were successfully extracted

    Returns:
        Page index dictionary or None if no PDF found
    """
    pdf_files = sorted(Path(raw_dir).glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    try:
        indexer = TableIndexer(pdf_path)
        page_index = indexer.generate_page_index_for_meta(extracted_table_ids)
        return page_index
    except Exception as exc:  # pragma: no cover
        print(f"⚠️ Table page index generation skipped: {exc}")
        return None


def build(  # noqa: C901
    ruleset: str, output_format: str, out_dir: Path, bundle: bool = False
) -> Path:
    layout = ensure_ruleset_layout(ruleset=ruleset, out_dir=out_dir)
    target_dir = layout["dist_ruleset"]

    report = BuildReport.create(ruleset=ruleset, output_format=output_format)
    report_path = target_dir / "build_report.json"
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")

    # Extract monsters from PDF (v0.3.0)
    _extract_raw_monsters(raw_dir=layout["raw"])

    # Extract equipment from PDF (v0.5.0)
    _extract_raw_equipment(raw_dir=layout["raw"])

    # Extract spells from PDF (v0.6.0)
    _extract_raw_spells(raw_dir=layout["raw"])

    # Extract tables from PDF (v0.7.0)
    _extract_raw_tables(raw_dir=layout["raw"])

    raw_monsters = _load_raw_monsters(layout["raw"])
    parsed_monsters = parse_monster_records(raw_monsters)

    raw_equipment = _load_raw_equipment(layout["raw"])
    parsed_equipment = parse_equipment_records(raw_equipment)

    raw_spells = _load_raw_spells(layout["raw"])
    parsed_spells = parse_spell_records(raw_spells)

    # Parse tables (v0.7.0)
    raw_tables = _load_raw_tables(layout["raw"])
    parsed_tables = None
    if raw_tables:
        from scripts.table_targets import TARGET_TABLES

        targets_by_id = {t["id"]: t for t in TARGET_TABLES}
        parsed_tables = [parse_single_table(raw, targets_by_id) for raw in raw_tables]

    # Parse lineages (v0.8.0)
    # Lineages come from canonical targets, not PDF extraction
    parsed_lineages = parse_lineages()

    _write_datasets(
        ruleset=ruleset,
        dist_data_dir=target_dir,
        monsters=parsed_monsters,
        equipment=parsed_equipment if parsed_equipment else None,
        spells=parsed_spells if parsed_spells else None,
        tables=parsed_tables if parsed_tables else None,
        lineages=parsed_lineages if parsed_lineages else None,
    )

    # Extract metadata from PDF if present (v0.8.1)
    pdf_metadata = None
    pdf_files = sorted(layout["raw"].glob("*.pdf"))
    if pdf_files:
        try:
            pdf_metadata = extract_pdf_metadata(pdf_files[0])
            print(f"✓ Extracted metadata from {pdf_files[0].name}")
        except Exception as exc:
            print(f"⚠️ PDF metadata extraction failed: {exc}")

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

    # Compute page range from raw spells
    spells_page_range = None
    if raw_spells:
        all_pages = [page for spell in raw_spells if (page := spell.get("page"))]
        if all_pages:
            spells_page_range = (min(all_pages), max(all_pages))

    # Generate comprehensive page_index from table_indexer (v0.7.0)
    # Pass list of successfully extracted table IDs for accurate reporting
    extracted_table_ids = [t["id"] for t in parsed_tables] if parsed_tables else None
    table_page_index = _generate_table_page_index(layout["raw"], extracted_table_ids)

    # Generate rich meta.json for consumers (includes license, page_index, etc.)
    meta_json = _generate_meta_json(
        pdf_hash=pdf_hash,
        pdf_metadata=pdf_metadata,
        monsters_complete=len(parsed_monsters) > 0,
        monsters_page_range=monsters_page_range,
        equipment_complete=len(parsed_equipment) > 0,
        equipment_page_range=equipment_page_range,
        spells_complete=len(parsed_spells) > 0,
        spells_page_range=spells_page_range,
        table_page_index=table_page_index,
    )
    meta_path = target_dir / "meta.json"
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
