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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .assemble.assemble_equipment import assemble_equipment_from_tables
from .assemble.indexer import build_indexes
from .build_prose_dataset import build_prose_dataset
from .extract.extract_equipment import extract_equipment
from .extract.extract_features import extract_class_features, extract_lineage_traits
from .extract.extract_monsters import extract_monsters
from .extract.extract_pdf_metadata import extract_pdf_metadata
from .extract.extract_spells import extract_spells
from .extraction import extract_tables_to_json
from .extraction.extraction_metadata import TABLES
from .parse.parse_classes import parse_classes
from .parse.parse_conditions import parse_condition_records
from .parse.parse_diseases import parse_disease_records
from .parse.parse_equipment import parse_equipment_records
from .parse.parse_features import parse_features
from .parse.parse_lineages import parse_lineages
from .parse.parse_monsters import parse_monster_records
from .parse.parse_poison_descriptions import parse_poison_description_records
from .parse.parse_poisons_table import parse_poisons_table
from .parse.parse_spells import parse_spell_records
from .parse.parse_tables import parse_single_table
from .postprocess import clean_equipment_record, clean_monster_record, clean_spell_record
from .utils.constants import RULESETS_DIRNAME, SCHEMA_VERSION
from .utils.metadata import generate_meta_json, wrap_with_meta
from .utils.table_indexer import TableIndexer


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


def _write_datasets(  # noqa: PLR0913
    *,
    ruleset: str,
    ruleset_version: str,
    dist_data_dir: Path,
    monsters: list[dict[str, Any]],
    equipment: list[dict[str, Any]] | None = None,
    spells: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    lineages: list[dict[str, Any]] | None = None,
    classes: list[dict[str, Any]] | None = None,
    conditions: dict[str, Any] | None = None,  # Prose dataset document
    diseases: dict[str, Any] | None = None,  # Prose dataset document
    poisons: dict[str, Any] | None = None,  # Prose dataset document
    features: dict[str, Any] | None = None,  # Prose dataset document
) -> None:
    processed_monsters = [clean_monster_record(monster) for monster in monsters]

    monsters_doc = wrap_with_meta(
        {"items": processed_monsters}, ruleset=ruleset, ruleset_version=ruleset_version
    )
    (dist_data_dir / "monsters.json").write_text(
        _render_json(monsters_doc),
        encoding="utf-8",
    )

    # Write equipment if available
    processed_equipment = None
    if equipment:
        processed_equipment = [clean_equipment_record(item) for item in equipment]
        equipment_doc = wrap_with_meta(
            {"items": processed_equipment}, ruleset=ruleset, ruleset_version=ruleset_version
        )

        # Add equipment-specific metadata (SRD economic rules)
        equipment_doc["_meta"]["equipment_economics"] = {
            "resale_rules": {
                "arms_armor_equipment": "Undamaged weapons, armor, and other equipment fetch half their cost when sold in a market. Weapons and armor used by monsters are rarely in good enough condition to sell.",
                "magic_items": "Selling magic items is problematic. Finding someone to buy a potion or a scroll isn't too hard, but other items are out of the realm of most but the wealthiest nobles. The value of magic is far beyond simple gold.",
                "gems_jewelry_art": "These items retain their full value in the marketplace, and you can either trade them in for coin or use them as currency for other transactions.",
                "trade_goods": "Like gems and art objects, trade goods—bars of iron, bags of salt, livestock, and so on—retain their full value in the marketplace and barter economy.",
            },
            "default_resale_multiplier": 0.5,
            "source_page": 62,
        }

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

    spells_doc = wrap_with_meta(
        {"items": processed_spells}, ruleset=ruleset, ruleset_version=ruleset_version
    )
    (dist_data_dir / "spells.json").write_text(
        _render_json(spells_doc),
        encoding="utf-8",
    )

    # Write tables (v0.7.0)
    # Tables are already fully normalized by parse_single_table, no additional cleaning needed
    processed_tables = tables if tables else None
    if processed_tables:
        # Sort tables by page number (document/TOC order)
        def get_sort_page(table):
            page = table.get("page")
            if page is None:
                return 99999  # Put tables without pages at end
            if isinstance(page, list):
                return page[0] if page else 99999
            return page

        sorted_tables = sorted(processed_tables, key=lambda t: (get_sort_page(t), t.get("id", "")))

        # Reorder table properties: metadata first, columns and rows at end
        reordered_tables = []
        for table in sorted_tables:
            ordered = {}
            # Core identification first
            for key in ["id", "simple_name", "name"]:
                if key in table:
                    ordered[key] = table[key]
            # Metadata fields
            for key in ["page", "category", "section", "notes", "summary"]:
                if key in table:
                    ordered[key] = table[key]
            # Any other fields (except columns/rows)
            for key, value in table.items():
                if key not in ordered and key not in ["columns", "rows"]:
                    ordered[key] = value
            # Columns and rows at the very end
            if "columns" in table:
                ordered["columns"] = table["columns"]
            if "rows" in table:
                ordered["rows"] = table["rows"]
            reordered_tables.append(ordered)

        tables_doc = wrap_with_meta(
            {"items": reordered_tables}, ruleset=ruleset, ruleset_version=ruleset_version
        )
        (dist_data_dir / "tables.json").write_text(
            _render_json(tables_doc),
            encoding="utf-8",
        )

    # Write lineages (v0.8.0)
    # Lineages are already fully normalized by parse_lineages, no additional cleaning needed
    processed_lineages = lineages if lineages else None
    if processed_lineages:
        lineages_doc = wrap_with_meta(
            {"items": processed_lineages}, ruleset=ruleset, ruleset_version=ruleset_version
        )
        (dist_data_dir / "lineages.json").write_text(
            _render_json(lineages_doc),
            encoding="utf-8",
        )

    # Write classes (v0.8.2)
    # Classes are already fully normalized by parse_classes, no additional cleaning needed
    processed_classes = classes if classes else None
    if processed_classes:
        classes_doc = wrap_with_meta(
            {"items": processed_classes}, ruleset=ruleset, ruleset_version=ruleset_version
        )
        (dist_data_dir / "classes.json").write_text(
            _render_json(classes_doc),
            encoding="utf-8",
        )

    # Write conditions (v0.10.0)
    # Conditions are already fully normalized by build_conditions, no additional cleaning needed
    processed_conditions = None
    if conditions:
        # Conditions come as a complete document with _meta already included
        (dist_data_dir / "conditions.json").write_text(
            _render_json(conditions),
            encoding="utf-8",
        )
        # Extract just the conditions list for indexing
        processed_conditions = conditions.get("conditions", [])

    # Write diseases (v0.11.0)
    processed_diseases = None
    if diseases:
        (dist_data_dir / "diseases.json").write_text(
            _render_json(diseases),
            encoding="utf-8",
        )
        processed_diseases = diseases.get("diseases", [])

    # Write poisons (v0.11.0)
    # Poisons is a single table record (like madness tables)
    processed_poisons = None
    if poisons:
        (dist_data_dir / "poisons.json").write_text(
            _render_json(poisons),
            encoding="utf-8",
        )
        # Extract just the items list for indexing
        processed_poisons = poisons.get("items", [])

    # Write features (v0.11.0)
    processed_features = None
    if features:
        (dist_data_dir / "features.json").write_text(
            _render_json(features),
            encoding="utf-8",
        )
        # Extract just the features list for indexing
        processed_features = features.get("features", [])

    index_payload = build_indexes(
        processed_monsters,
        processed_spells,
        processed_equipment,
        processed_tables,
        processed_lineages,
        processed_classes,
        processed_conditions,
        processed_diseases,
        processed_poisons,
        processed_features,
    )
    index_doc = wrap_with_meta(index_payload, ruleset=ruleset, ruleset_version=ruleset_version)
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
    schema_version: str
    python_version: str

    @classmethod
    def create(cls, ruleset: str, output_format: str) -> BuildReport:
        # The timestamp only lives in the report to aid debugging. Downstream
        # dataset files should remain timestamp-free to keep builds reproducible.
        timestamp = datetime.now(UTC).isoformat()
        return cls(
            ruleset=ruleset,
            output_format=output_format,
            timestamp_utc=timestamp,
            builder_version=__version__,
            schema_version=SCHEMA_VERSION,
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
    parser.add_argument(
        "--tables-only",
        action="store_true",
        help="Extract only tables (skip monsters, equipment, spells) for faster iteration",
    )
    parser.add_argument(
        "--monsters-only",
        action="store_true",
        help="Extract only monsters (skip equipment, spells, tables)",
    )
    parser.add_argument(
        "--equipment-only",
        action="store_true",
        help="Extract only equipment (skip monsters, spells, tables)",
    )
    parser.add_argument(
        "--spells-only",
        action="store_true",
        help="Extract only spells (skip monsters, equipment, tables)",
    )
    parser.add_argument(
        "--skip",
        type=str,
        help="Comma-separated list of datasets to skip (e.g. 'monsters,equipment,spells')",
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
        "class.schema.json",
        "condition.schema.json",
        "features.schema.json",
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
    ruleset: str,
    output_format: str,
    out_dir: Path,
    bundle: bool = False,
    skip_datasets: set[str] | None = None,
) -> Path:
    layout = ensure_ruleset_layout(ruleset=ruleset, out_dir=out_dir)
    target_dir = layout["dist_ruleset"]
    skip_datasets = skip_datasets or set()

    report = BuildReport.create(ruleset=ruleset, output_format=output_format)
    report_path = target_dir / "build_report.json"
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")

    # Extract monsters from PDF (v0.3.0)
    if "monsters" not in skip_datasets:
        _extract_raw_monsters(raw_dir=layout["raw"])

    # Extract equipment from PDF (v0.5.0)
    if "equipment" not in skip_datasets:
        _extract_raw_equipment(raw_dir=layout["raw"])

    # Extract spells from PDF (v0.6.0)
    if "spells" not in skip_datasets:
        _extract_raw_spells(raw_dir=layout["raw"])

    # Extract tables from PDF (v0.7.0)
    if "tables" not in skip_datasets:
        _extract_raw_tables(raw_dir=layout["raw"])

    raw_monsters = _load_raw_monsters(layout["raw"]) if "monsters" not in skip_datasets else []
    parsed_monsters = parse_monster_records(raw_monsters) if raw_monsters else []

    # Parse tables (v0.7.0) - needed before equipment assembly
    raw_tables = _load_raw_tables(layout["raw"])
    parsed_tables = None
    if raw_tables:
        from scripts.table_targets import TARGET_TABLES

        targets_by_id = {t["id"]: t for t in TARGET_TABLES}
        parsed_tables = [parse_single_table(raw, targets_by_id) for raw in raw_tables]

    # Equipment assembly (v0.9.9) - now uses tables.json instead of PyMuPDF
    parsed_equipment = []
    if "equipment" not in skip_datasets:
        if parsed_tables:
            # New table-based assembly (v0.9.9 Part 2)
            parsed_equipment = assemble_equipment_from_tables(parsed_tables)
        else:
            # Fallback to old PyMuPDF extraction if no tables available
            raw_equipment = _load_raw_equipment(layout["raw"])
            parsed_equipment = parse_equipment_records(raw_equipment) if raw_equipment else []

    raw_spells = _load_raw_spells(layout["raw"]) if "spells" not in skip_datasets else []
    parsed_spells = parse_spell_records(raw_spells) if raw_spells else []

    # Parse lineages (v0.8.0)
    # Lineages come from canonical targets, not PDF extraction
    parsed_lineages = parse_lineages()

    # Parse classes (v0.8.2)
    # Classes come from canonical targets, not PDF extraction
    parsed_classes = parse_classes()

    # Build prose datasets (v0.10.0+)
    # Generic config-driven approach for conditions, diseases, madness, poisons
    pdf_files = sorted(layout["raw"].glob("*.pdf"))

    # Extract features (v0.11.0)
    # Features come from PDF extraction: class features + lineage traits
    features_doc = None
    if pdf_files and "features" not in skip_datasets:
        try:
            print(f"Extracting features from {pdf_files[0].name}...")
            raw_class_features = extract_class_features(pdf_files[0])
            class_features = parse_features(raw_class_features, "class")

            raw_lineage_traits = extract_lineage_traits(pdf_files[0])
            lineage_traits = parse_features(raw_lineage_traits, "lineage")

            all_features = class_features + lineage_traits
            print(
                f"✓ Extracted {len(all_features)} features ({len(class_features)} class + {len(lineage_traits)} lineage)"
            )
        except Exception as exc:
            print(f"⚠️ Feature extraction failed: {exc}")
            all_features = []
    else:
        all_features = []

    # Map dataset names to their parser functions
    # NOTE: Diseases are prose. Madness and poisons use tables + prose descriptions.
    prose_parsers = {
        "conditions": parse_condition_records,
        "diseases": parse_disease_records,
        "poison_descriptions": parse_poison_description_records,
    }

    # Build prose datasets
    conditions_doc = None
    diseases_doc = None
    poison_descriptions_by_name = {}

    # Poisons items come from table + descriptions (table itself goes to tables.json)
    poisons_doc = None

    if pdf_files:
        for dataset_name, parser_func in prose_parsers.items():
            try:
                doc = build_prose_dataset(dataset_name, pdf_files[0], parser_func)
                # Assign to appropriate variable
                if dataset_name == "conditions":
                    conditions_doc = doc
                elif dataset_name == "diseases":
                    diseases_doc = doc
                elif dataset_name == "poison_descriptions":
                    # Build lookup map for merging with poison table data
                    output_key = TABLES[dataset_name].get("output_key", "items")
                    for desc in doc.get(output_key, []):
                        simple_name = desc.get("simple_name")
                        if simple_name:
                            poison_descriptions_by_name[simple_name] = desc
            except Exception as exc:
                print(f"⚠️ {dataset_name.capitalize()} extraction failed: {exc}")

    # Extract metadata from PDF if present - do this BEFORE building final docs
    pdf_metadata = None
    pdf_files_for_meta = sorted(layout["raw"].glob("*.pdf"))
    if pdf_files_for_meta:
        try:
            pdf_metadata = extract_pdf_metadata(pdf_files_for_meta[0])
            print(f"✓ Extracted metadata from {pdf_files[0].name}")
        except Exception as exc:
            print(f"⚠️ PDF metadata extraction failed: {exc}")

    ruleset_version = pdf_metadata.get("version", "5.1") if pdf_metadata else "5.1"

    # Build poison items from table + descriptions (tables themselves go to tables.json)
    if parsed_tables:
        # Build poison items from table + descriptions
        poisons_table = None
        for table in parsed_tables:
            if table.get("simple_name") == "poisons":
                poisons_table = table
                break

        if poisons_table:
            try:
                # Parse poison table into individual item records (equipment-style)
                parsed_poisons = parse_poisons_table(
                    poisons_table, descriptions=poison_descriptions_by_name
                )

                # Wrap as items array with proper _meta
                poisons_doc = wrap_with_meta(
                    {"items": parsed_poisons}, ruleset=ruleset, ruleset_version=ruleset_version
                )
                print(f"✓ Parsed {len(parsed_poisons)} poison items")
            except Exception as exc:
                print(f"⚠️ Poison item parsing failed: {exc}")

    # Build features document (v0.11.0)
    if all_features:
        features_doc = wrap_with_meta(
            {"features": all_features}, ruleset=ruleset, ruleset_version=ruleset_version
        )

    _write_datasets(
        ruleset=ruleset,
        ruleset_version=ruleset_version,
        dist_data_dir=target_dir,
        monsters=parsed_monsters,
        equipment=parsed_equipment if parsed_equipment else None,
        spells=parsed_spells if parsed_spells else None,
        tables=parsed_tables if parsed_tables else None,
        lineages=parsed_lineages if parsed_lineages else None,
        classes=parsed_classes if parsed_classes else None,
        conditions=conditions_doc if conditions_doc else None,
        diseases=diseases_doc if diseases_doc else None,
        poisons=poisons_doc if poisons_doc else None,
        features=features_doc if features_doc else None,
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

    # Compute page range from equipment (now from parsed_equipment since we assemble from tables)
    equipment_page_range = None
    if parsed_equipment:
        all_pages = [page for item in parsed_equipment if (page := item.get("page"))]
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
    meta_json = generate_meta_json(
        pdf_hash=pdf_hash,
        pdf_metadata=pdf_metadata,
        monsters_complete=len(parsed_monsters) > 0,
        monsters_page_range=monsters_page_range,
        equipment_complete=len(parsed_equipment) > 0,
        equipment_page_range=equipment_page_range,
        spells_complete=len(parsed_spells) > 0,
        spells_page_range=spells_page_range,
        table_page_index=table_page_index,
        classes_complete=len(parsed_classes) > 0,
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

    # Parse skip list from various flags
    skip_datasets = set()
    if args.tables_only:
        skip_datasets = {"monsters", "equipment", "spells"}
    elif args.monsters_only:
        skip_datasets = {"equipment", "spells", "tables"}
    elif args.equipment_only:
        skip_datasets = {"monsters", "spells", "tables"}
    elif args.spells_only:
        skip_datasets = {"monsters", "equipment", "tables"}
    elif args.skip:
        skip_datasets = {s.strip() for s in args.skip.split(",")}

    build(
        ruleset=args.ruleset,
        output_format=args.format,
        out_dir=out_dir,
        bundle=args.bundle,
        skip_datasets=skip_datasets,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
