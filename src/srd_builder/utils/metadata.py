"""Utilities for building metadata documents (meta.json and _meta blocks)."""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

from .. import __version__
from ..constants import DATA_SOURCE
from .page_index import PAGE_INDEX

# Schema directory location
SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"

__all__ = [
    "ALL_DATASETS",
    "build_inventory",
    "build_page_index",
    "generate_meta_json",
    "meta_block",
    "read_schema_version",
    "wrap_with_meta",
]

# Single source of truth for the complete set of shipped datasets (alphabetical).
ALL_DATASETS: list[str] = [
    "ability_scores",
    "classes",
    "conditions",
    "damage_types",
    "diseases",
    "equipment",
    "features",
    "lineages",
    "magic_items",
    "monsters",
    "poisons",
    "rules",
    "skills",
    "spells",
    "tables",
    "weapon_properties",
]

# Mapping from dataset file basename to its schema name.
DATASET_TO_SCHEMA: dict[str, str] = {
    "ability_scores": "ability_score",
    "classes": "class",
    "conditions": "condition",
    "damage_types": "damage_type",
    "diseases": "disease",
    "equipment": "equipment",
    "features": "features",
    "lineages": "lineage",
    "magic_items": "magic_item",
    "monsters": "monster",
    "poisons": "poison",
    "rules": "rule",
    "skills": "skill",
    "spells": "spell",
    "tables": "table",
    "weapon_properties": "weapon_property",
}


def _compute_extraction_status(
    *,
    dist_dir: Path | None,
    monsters_complete: bool,
    equipment_complete: bool,
    spells_complete: bool,
    classes_complete: bool,
) -> dict[str, str]:
    """Compute extraction_status by checking which files actually exist.

    Args:
        dist_dir: Distribution directory to check. If None, use parameter flags.
        monsters_complete: Whether monsters extraction completed
        equipment_complete: Whether equipment extraction completed
        spells_complete: Whether spells extraction completed
        classes_complete: Whether classes extraction completed

    Returns:
        Dictionary mapping dataset names to "complete" or "in_progress"
    """
    if dist_dir is None:
        # Fallback to parameter-based approach (legacy)
        # Keep in alphabetical order
        return {
            "ability_scores": "complete",
            "classes": "complete" if classes_complete else "in_progress",
            "conditions": "complete",
            "damage_types": "complete",
            "diseases": "complete",
            "equipment": "complete" if equipment_complete else "in_progress",
            "features": "complete",
            "lineages": "complete",
            "magic_items": "complete",
            "monsters": "complete" if monsters_complete else "in_progress",
            "poisons": "complete",
            "rules": "complete",
            "skills": "complete",
            "spells": "complete" if spells_complete else "in_progress",
            "tables": "complete",
            "weapon_properties": "complete",
        }

    # Check actual file existence
    # Keep in alphabetical order for consistency in meta.json output
    datasets = ALL_DATASETS

    status = {}
    for dataset in datasets:
        file_path = dist_dir / f"{dataset}.json"
        status[dataset] = "complete" if file_path.exists() else "in_progress"

    return status


def read_schema_version(schema_name: str) -> str:
    """Read version from a schema file.

    Args:
        schema_name: Name of schema (e.g., 'monster', 'spell', 'equipment')

    Returns:
        Version string from schema file

    Raises:
        FileNotFoundError: If schema file doesn't exist
        KeyError: If schema file doesn't have 'version' field
    """
    schema_path = SCHEMA_DIR / f"{schema_name}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
    if "version" not in schema_data:
        raise KeyError(f"Schema file {schema_path} missing 'version' field")

    return schema_data["version"]


def build_inventory(dist_dir: Path) -> dict[str, int]:
    """Count items in each shipped dataset, returning {dataset_name: count}.

    Some legacy datasets use the dataset name as the array key (e.g. ``conditions``,
    ``diseases``, ``features``) instead of the canonical ``items`` key. We accept
    either shape; missing or unreadable files report 0.
    """
    inventory: dict[str, int] = {}
    for name in ALL_DATASETS:
        path = dist_dir / f"{name}.json"
        if not path.exists():
            inventory[name] = 0
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError, json.JSONDecodeError:
            inventory[name] = 0
            continue
        if not isinstance(data, dict):
            inventory[name] = 0
            continue
        items = data.get("items")
        if not isinstance(items, list):
            # Legacy datasets use their own name as the array key.
            items = data.get(name)
        inventory[name] = len(items) if isinstance(items, list) else 0
    return inventory


def meta_block(ruleset: str, schema_version: str, ruleset_version: str = "5.1") -> dict[str, str]:
    """Generate standardized _meta block with consistent field order.

    Args:
        ruleset: Ruleset identifier (e.g., 'srd_5_1')
        schema_version: Schema version for this specific dataset
        ruleset_version: Version of the ruleset (default: '5.1')

    Returns:
        Metadata dictionary
    """
    return {
        "source": DATA_SOURCE,
        "ruleset_version": ruleset_version,
        "schema_version": schema_version,
        "generated_by": f"srd-builder v{__version__}",
        "build_report": "./build_report.json",
    }


def wrap_with_meta(
    payload: dict[str, Any], *, ruleset: str, schema_version: str, ruleset_version: str = "5.1"
) -> dict[str, Any]:
    """Wrap payload with _meta block.

    Args:
        payload: Data to wrap
        ruleset: Ruleset identifier
        schema_version: Schema version for this dataset
        ruleset_version: Version of the ruleset

    Returns:
        Document with _meta block
    """
    document: OrderedDict[str, Any] = OrderedDict()
    document["_meta"] = meta_block(ruleset, schema_version, ruleset_version)
    for key, value in payload.items():
        document[key] = value
    return document


def build_page_index(
    *,
    monsters_page_range: tuple[int, int] | None,
    equipment_page_range: tuple[int, int] | None,
    spells_page_range: tuple[int, int] | None,
    table_page_index: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build page_index section for meta.json."""

    page_index: dict[str, dict[str, int | str]] = {}

    for section_name, section in PAGE_INDEX.items():
        section_data: dict[str, int | str] = {
            "start": section["pages"]["start"],
            "end": section["pages"]["end"],
            "description": section["description"],
        }
        dataset = section.get("dataset")
        if dataset is not None:
            section_data["dataset"] = dataset
        page_index[section_name] = section_data

    if table_page_index and "reference_tables" in table_page_index:
        page_index["reference_tables"] = table_page_index["reference_tables"]

    return page_index


def generate_meta_json(  # noqa: PLR0913
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
    classes_complete: bool = False,
    build_timestamp: str | None = None,
    dist_dir: Path | None = None,
) -> dict[str, Any]:
    """Generate rich metadata for dist/meta.json with provenance.

    Args:
        dist_dir: Distribution directory to check for actual file existence.
                  If provided, extraction_status will reflect what was actually built.
    """

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

    build_info: dict[str, str | None] = {
        "pdf_hash": f"sha256:{pdf_hash}" if pdf_hash else None,
    }
    if build_timestamp is not None:
        build_info["extracted_at"] = build_timestamp

    # Schema versions for each dataset type (read from schema files for independent evolution).
    # One entry per shipped dataset, alphabetical by schema name.
    schemas = {
        schema_name: read_schema_version(schema_name)
        for schema_name in sorted(set(DATASET_TO_SCHEMA.values()))
    }

    # Per-dataset item counts ("inventory") computed from the actual dist files if present.
    inventory = build_inventory(dist_dir) if dist_dir is not None else {}

    return {
        "source": DATA_SOURCE,
        "ruleset_version": version,
        "builder_version": __version__,
        "schemas": schemas,
        "license": {
            "type": license_type,
            "url": license_url,
            "attribution": attribution,
            "conversion_note": (
                "Converted from the original PDF by srd-builder "
                f"(https://github.com/wolftales/srd-builder) version {__version__}"
            ),
        },
        "build": build_info,
        "page_index": build_page_index(
            monsters_page_range=monsters_page_range,
            equipment_page_range=equipment_page_range,
            spells_page_range=spells_page_range,
            table_page_index=table_page_index,
        ),
        "datasets": _build_datasets_block(
            inventory=inventory,
            extraction_status=_compute_extraction_status(
                dist_dir=dist_dir,
                monsters_complete=monsters_complete,
                equipment_complete=equipment_complete,
                spells_complete=spells_complete,
                classes_complete=classes_complete,
            ),
        ),
        "terminology": {"aliases": {"race": "lineage", "races": "lineages"}},
    }


def _build_datasets_block(
    *,
    inventory: dict[str, int],
    extraction_status: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Collapse files / inventory / extraction_status into one per-dataset block.

    Shape: ``{dataset_name: {"file": str, "count": int, "status": str}}``

    Always emits every dataset in ALL_DATASETS so consumers can iterate the
    block without cross-referencing a separate file list.
    """
    block: dict[str, dict[str, Any]] = {}
    for name in ALL_DATASETS:
        block[name] = {
            "file": f"{name}.json",
            "count": inventory.get(name, 0),
            "status": extraction_status.get(name, "in_progress"),
        }
    return block
